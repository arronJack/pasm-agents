"""智能客服产品智能体（CustomerServiceAgent）—— pasm-agents 的第 4 个产品。

它和另外三个产品（NPC / 老人陪伴 / 学习陪伴）的差别在**底座**：
另外三个继承基座的 ``BaseAgent``（只要 ``pasm-skills``），
本产品继承应用框架的 ``BaseApplication``（``pasm-framework`` 提供）——
因为"客服"的核心能力是**资料库**，而资料库是框架的 ``knowledge_base`` 插件，
不是 SDK 里有的东西。

它做到的事
----------
- **就资料作答**：检索资料库 → 命中就给带来源的答复；**查不到就如实说不知道**，
  绝不编造。这是客服可信度的底线，也是 ``_render_reply`` 只认
  ``knowledge_facts()``（带 ``source`` 的知识）而忽略纯闲聊记忆的原因。
- **不许答非所问**：命中还必须落在条目的**标题或标签**上（``touches_surface``）。
  否则问「请问 CEO 的私人邮箱是多少」会靠正文里一个「邮箱」命中"发票开具"，
  于是自信地答出开票流程 —— 对客服来说，答非所问比答不上来严重得多。
- **客诉识别与转人工**：``needs_escalation(text)`` 认出四类必须升级的表达
  （投诉/曝光、法律/监管、安全/伤害、要求退款赔偿），命中就给出明确的转人工提示，
  并把这次客诉按 ``salience=5`` 写进记忆（不会被闲聊挤掉，便于复盘）。
- **开箱可用**：首次启动自动把 ``DEFAULT_FAQ`` 灌进资料库，**不配任何东西**
  就能答上来；也可以随时 ``ingest_faq([...])`` 换成自己的知识。
- **可接大模型**：传 ``llm={...}`` 就启用 ``llm_responder`` 插件，
  回复更自然；LLM 挂了会自动回落模板，**永远有回应**。

快速开始：

.. code-block:: python

    from pasm_agents import CustomerServiceAgent

    cs = CustomerServiceAgent(agent_id="shop-cs", persona={
        "name": "小智", "role": "售后客服", "tone": "温暖、专业、耐心",
        "hotline": "400-000-0000",
    })
    cs.ingest_faq([
        {"title": "退换货政策", "content": "签收 7 天内无理由退货，生鲜除外。",
         "source": "faq", "tags": ["退货", "售后"]},
    ])
    print(cs.answer("怎么退货？"))
    print(cs.needs_escalation("我要投诉你们，再不处理就曝光！"))   # -> '投诉/曝光'
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pasm_framework import BaseApplication

#: 默认人设。``hotline`` 会被转人工提示引用；``escalate_note`` 可自定义措辞。
DEFAULT_PERSONA: Dict[str, Any] = {
    "name": "小智",
    "role": "智能客服",
    "tone": "温暖、专业、耐心",
    "temper": 0.6,
    "energy": 0.5,
    "play": 0.4,
    "hotline": "400-000-0000",
}

#: 开箱即用的起步资料（首次启动灌进资料库，保证"装完就能答"）。
#: 换成自己的业务知识只需 ``ingest_faq([...])``；或传 ``seed_faq=False`` 关掉。
DEFAULT_FAQ: List[Dict[str, Any]] = [
    {
        "title": "退换货政策",
        "content": "签收后 7 天内支持无理由退货（生鲜、定制类除外），"
                   "商品需保持不影响二次销售的完好状态。",
        "source": "faq",
        "tags": ["退货", "换货", "售后", "退款"],
    },
    {
        "title": "配送时效",
        "content": "现货商品 24 小时内发货；偏远地区约 3-5 个工作日到达。"
                   "发货后可在「我的订单」里查看物流单号。",
        "source": "faq",
        "tags": ["配送", "物流", "发货", "时效"],
    },
    {
        "title": "发票开具",
        "content": "支持开具电子发票，发货次日发送至注册邮箱；"
                   "如需纸质专票请在订单备注中说明并留下开票信息。",
        "source": "faq",
        "tags": ["发票", "开票", "税务"],
    },
    {
        "title": "会员权益",
        "content": "黄金会员享全年包邮、专属客服通道与生日礼券；"
                   "会员等级按近 12 个月累计消费自动评定。",
        "source": "faq",
        "tags": ["会员", "等级", "权益", "包邮"],
    },
    {
        "title": "支付方式",
        "content": "支持微信支付、支付宝与银行卡；企业客户可申请对公转账，"
                   "需在结算页选择「对公转账」并填写开票信息。",
        "source": "faq",
        "tags": ["支付", "付款", "对公", "转账"],
    },
]


#: 必须转人工的四类表达 —— 每条是 (原因标签, 触发词元组)。
#: 词表刻意**只收明确指向该场景**的说法，判不出来就放行（无法判定 = 不升级），
#: 避免把"这个功能真难用啊"这类普通抱怨也当客诉。
#: 元组用**短语**而非单字：「退款」是正常问询，「要求退款」才是客诉。
ESCALATION_RULES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("投诉/曝光", (
        "投诉", "曝光", "举报你们", "差评", "315", "12315", "消协",
        "发到网上", "让更多人知道",
    )),
    ("法律/监管", (
        "起诉", "律师", "法院", "法律途径", "仲裁", "工商局", "监管局",
    )),
    ("安全/伤害", (
        # ★ 只收**结果性**说法，不收"过敏/受伤"这类光杆词：
        # 「这个成分会让我过敏吗」是提问，不是伤害报告 —— 升级它等于乱升级。
        "过敏了", "过敏反应", "吃坏", "受伤了", "摔伤", "爆炸", "起火",
        "漏电", "中毒", "人身安全",
    )),
    ("要求赔偿", (
        "要求赔偿", "必须赔", "赔我", "赔偿我", "三倍赔偿", "假一赔",
    )),
)


def detect_escalation(text: str) -> Optional[str]:
    """认出必须转人工的原因标签；认不出来返回 ``None``。

    单独导出成函数（而不只做成方法）是为了让调用方**不构造智能体**
    也能复用同一套判据 —— 例如网关层在分发前先做一次预筛。
    """
    t = (text or "").strip()
    if not t:
        return None
    for reason, words in ESCALATION_RULES:
        for w in words:
            if w in t:
                return reason
    return None


# ============================================================ 检索相关性闸门
#: 与框架 ``knowledge_base`` 同口径的分词：英文/数字词（≥2 字符）+ 中文 bigram。
#: **单字不作数** —— 「你」「么」这类高频字会造成大量误命中。
_WORD_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+")

#: 次级判据的默认门槛（见 ``_render_reply`` 的说明）。
DEFAULT_SCORE_FLOOR: float = 4.0


def semantic_tokens(text: str) -> set:
    """把文本切成检索用的 token（与框架同口径）。"""
    out: set = set()
    for seg in _WORD_RE.findall(text or ""):
        if seg[0].isascii():
            if len(seg) >= 2:
                out.add(seg.lower())
        elif len(seg) >= 2:
            for i in range(len(seg) - 1):
                out.add(seg[i:i + 2])
    return out


def touches_surface(query_tokens: set, fact: Dict[str, Any]) -> bool:
    """这条命中是否落在条目的**检索面**（标题 / 标签）上。

    为什么需要这个闸门（实测数据，不是拍脑袋）
    ------------------------------------------
    ``knowledge_base`` 的分数是 ``(重叠词×字段权重 + 精确率) × 时间衰减``。
    在起步资料库上实测：

    * 真问题（「怎么退货？」「发票怎么开？」…）分数 **6.00 ~ 24.50**；
    * 假命中：问「请问 CEO 的私人邮箱是多少」，靠正文里一个「邮箱」命中了
      **发票开具** —— 分数 **2.29**，回复于是**答非所问**。

    想用绝对分数分开它们有个陷阱：分数带**时间衰减**（``0.6 + 0.4 × recency``），
    资料库放一个月后真命中会被压到原来的 0.6 倍，任何固定阈值都会开始"失忆"。

    所以主判据用**与分数、与时间都无关**的规则：**命中必须落在标题或标签上**。
    FAQ / 文档的标题与标签是人工维护的检索面；只跟正文里一个偶然重合的词
    撞上，几乎都是假命中。
    """
    surface = "%s %s" % (fact.get("title") or "", " ".join(fact.get("tags") or []))
    return bool(query_tokens & semantic_tokens(surface))


def _default_cs_config(kb_dir: Optional[str] = None,
                       llm: Optional[Dict[str, Any]] = None,
                       serve_port: int = 8080,
                       enable_gateway: bool = False) -> Dict[str, Any]:
    """后端开关表 —— 控制哪些内置插件启用。

    前 5 个默认开（基础且零依赖）：安全 / 会话 / 资料库 / 温度 / 可观测。
    ``llm_responder`` 传了 ``llm`` 才开；``web_gateway`` 默认**关**
    （理由见 ``serve()`` 的说明）。
    """
    return {
        "safety": {"enabled": True, "config": {"mode": "warn"}},
        "sessions": {"enabled": True, "config": {"max_history": 20}},
        "knowledge_base": {"enabled": True,
                           "config": ({"kb_dir": kb_dir} if kb_dir else {})},
        "warmth": {"enabled": True, "config": {}},
        "observability": {"enabled": True, "config": {}},
        "llm_responder": {"enabled": bool(llm), "config": llm or {}},
        "web_gateway": {"enabled": bool(enable_gateway),
                        "config": {"port": serve_port, "allowed_origins": "*"}},
    }


class CustomerServiceAgent(BaseApplication):
    """站点 / 平台智能客服（第 4 个产品智能体）。"""

    def __init__(
        self,
        agent_id: str,
        persona: Optional[Dict[str, Any]] = None,
        *,
        kb_dir: Optional[str] = None,
        llm: Optional[Dict[str, Any]] = None,
        serve_port: int = 8080,
        enable_gateway: bool = False,
        seed_faq: bool = True,
        score_floor: float = DEFAULT_SCORE_FLOOR,
        persist_dir: Optional[str] = None,
    ) -> None:
        self._serve_port = serve_port
        self._score_floor = float(score_floor)
        p = dict(DEFAULT_PERSONA)
        p.update(persona or {})
        # 资料库默认**按智能体隔离**（``<persist_dir>/kb``），不跟随插件那个
        # 全机共享的默认落点 ``~/.pasm_framework/kb``。
        # 不隔离的后果是真实的：同一台机器上跑两个客服（两家店/两个租户），
        # A 的 FAQ 会被检索进 B 的答复里 —— 属于跨租户数据泄漏，
        # 而且"我喂的资料为什么答不上来/为什么冒出别人的资料"极难排查。
        # 自测也受益：传了 persist_dir 就完全自洽，不会读到开发机上的真实资料库。
        if kb_dir is None:
            root = (Path(persist_dir) if persist_dir is not None
                    else (Path.home() / ".pasm-agents" / agent_id))
            kb_dir = str(Path(root) / "kb")
        super().__init__(
            agent_id, p,
            persist_dir=persist_dir,
            backend_config=_default_cs_config(
                kb_dir=kb_dir, llm=llm,
                serve_port=serve_port, enable_gateway=enable_gateway),
        )
        # 首次启动灌入起步资料库 —— 与老人陪伴"首次启动写入关键事实"同一套思路：
        # 用户的第一次体验必须能答上来，而不是"资料库是空的，请先喂资料"。
        # 用 state 里的一次性标记（而不是依赖资料库去重），语义明确、可预期。
        if seed_faq and not self.state.notes.get("cs_faq_seeded"):
            try:
                n = self.ingest(DEFAULT_FAQ)
            except Exception:
                # 资料库插件被关掉时不阻断构造 —— 但要在 state 里如实留痕，
                # 免得"我明明喂了资料为什么答不上来"变成最难查的一类问题。
                self.state.notes["cs_faq_seeded"] = "skipped(no knowledge_base)"
            else:
                self.state.notes["cs_faq_seeded"] = n
                self.save()

    # ------------------------------------------------------------ 回复模板
    def action_pool(self) -> List[str]:
        return ["reply", "escalate"]

    def _render_reply(
        self, text: str, facts: List[Dict[str, Any]], mood: float
    ) -> str:
        """只依据**有来源的知识**作答；查不到就如实说不知道（不编造）。

        ``facts`` 是混合检索结果：引擎的对话记忆（不带 ``source``）+ 资料库条目
        （带 ``source``）。必须过 ``knowledge_facts()`` 过滤 —— 否则会把
        "上一轮用户自己说过的话"当成资料答回去。

        然后还要过一次**相关性闸门**（见 ``touches_surface``）：命中必须落在条目的
        标题或标签上，**或**分数达到 ``score_floor``。不做这一步时，
        问「请问 CEO 的私人邮箱是多少」会靠正文里一个「邮箱」命中"发票开具"，
        于是答非所问 —— 对客服来说，答非所问比答不上来严重得多。

        （开了 LLM 时这一步通常走不到；但 LLM 失败会回落到这里，保证永远有回应。）
        """
        knowledge = self.knowledge_facts(facts)
        if knowledge:
            q = semantic_tokens(text)
            relevant = [
                f for f in knowledge
                if touches_surface(q, f)
                or float(f.get("score") or f.get("sal") or 0.0) >= self._score_floor
            ]
        else:
            relevant = []
        if relevant:
            top = relevant[0]
            brief = (top.get("brief") or top.get("title") or "").strip()
            src = str(top.get("source", ""))
            answer = "关于您的问题，我们查到相关说明：%s" % brief
            if src.startswith("knowledge_base"):
                answer += "（资料来源：%s）" % src.split(":", 1)[-1]
            return answer
        hotline = str(self.persona.get("hotline") or "").strip()
        tail = ("您可以拨打我们的客服热线 %s，" % hotline) if hotline else "您可以联系我们的客服，"
        return ("抱歉，我暂时没有查到关于这个问题的资料，已记录您的问题。"
                + tail + "或稍后再试，我们会尽快完善答案。")

    # ------------------------------------------------------------ 客诉升级
    def needs_escalation(self, text: str) -> Optional[str]:
        """这句该不该转人工？返回原因标签，或 ``None``。

        判据与模块级 ``detect_escalation`` 完全一致（同源，不会两边跑偏）。
        """
        return detect_escalation(text)

    def escalate(self, text: str, session_id: str = "default",
                 user_id: Optional[str] = None) -> Dict[str, Any]:
        """记录一次客诉并返回升级上下文（交给你的通知渠道）。

        与老人陪伴的 ``escalate`` 同一套做法：按 ``salience=5`` 写进记忆，
        这种记忆**不会被日常闲聊挤掉**，事后复盘一定查得到。
        """
        reason = self.needs_escalation(text) or "人工请求"
        self.observe(
            title="转人工：%s" % text[:20],
            brief=text,
            tags=["转人工", reason],
            salience=5,
            category="客诉",
        )
        try:
            self.save()
        except Exception:
            pass
        n = int(self.state.notes.get("cs_escalations") or 0) + 1
        self.state.notes["cs_escalations"] = n
        return {
            "agent_id": self.agent_id,
            "reason": reason,
            "text": text,
            "session_id": session_id,
            "user_id": user_id,
            "hotline": self.persona.get("hotline"),
            "escalation_count": n,
            "created_at": time.time(),
        }

    # ------------------------------------------------------------ 对外主入口
    def answer(self, text: str, session_id: str = "default",
               user_id: Optional[str] = None) -> str:
        """回答一个客户问题（``handle`` 的业务化封装 + 客诉转人工提示）。

        比裸 ``handle`` 多一件事：命中客诉判据时**在回复末尾追加转人工提示**，
        并把这次客诉记进记忆。这样"客服"与"普通聊天机器人"才有实质区别。
        """
        reply = self.handle(text, session_id=session_id, user_id=user_id)
        reason = self.needs_escalation(text)
        if not reason:
            return reply
        esc = self.escalate(text, session_id=session_id, user_id=user_id)
        hotline = str(esc.get("hotline") or "").strip()
        tail = ("客服热线 %s" % hotline) if hotline else "人工客服"
        return "%s\n\n【已标记转人工｜%s】您的诉求我已记录，会由专人跟进；" \
               "如需立刻处理请拨打 %s。" % (reply, reason, tail)

    def ingest_faq(self, items: List[Dict[str, Any]]) -> int:
        """把 FAQ / 产品文档喂进资料库（``ingest`` 的别名，会落盘）。"""
        return self.ingest(items)

    # ------------------------------------------------------------ 可观测
    def kb_stats(self) -> Optional[Dict[str, Any]]:
        """资料库规模（未启用资料库插件时返回 ``None``，不假装有）。"""
        kb = self.plugins.get("knowledge_base")
        if kb is None or not self.plugins.is_enabled("knowledge_base"):
            return None
        try:
            return kb.stats()
        except Exception:
            return None

    def snapshot(self) -> Dict[str, Any]:
        """可机读的状态快照（接监控 / 后台报表 / 家长端式的运营看板）。"""
        return {
            "agent_id": self.agent_id,
            "persona": dict(self.persona),
            "tier": self.tier,
            "mood": round(self.mood, 3),
            "interactions": self.state.total_interactions,
            "kb": self.kb_stats(),
            "escalations": int(self.state.notes.get("cs_escalations") or 0),
            "faq_seeded": self.state.notes.get("cs_faq_seeded"),
        }

    # ------------------------------------------------------------ 站点接入
    def serve(self, host: str = "0.0.0.0", port: Optional[int] = None) -> None:
        """启动 HTTP 网关（站点 ``<iframe>`` / REST 接入）。

        ⚠️ 必须构造时传 ``enable_gateway=True``，否则框架会直接抛
        ``FrameworkError`` —— 这是**故意的**：默认关掉网关，避免任何一次
        ``serve()`` 意外占住 8080 端口。
        """
        super().serve(host=host, port=port or self._serve_port)


__all__ = [
    "CustomerServiceAgent",
    "DEFAULT_FAQ",
    "DEFAULT_PERSONA",
    "DEFAULT_SCORE_FLOOR",
    "ESCALATION_RULES",
    "detect_escalation",
    "semantic_tokens",
    "touches_surface",
]
