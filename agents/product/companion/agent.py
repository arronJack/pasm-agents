"""老人陪伴产品智能体。

聚焦三件事：

1. **关键事实牢牢记住**：用药、过敏、家人、本人信息。标签式精确检索，**永不丢**。
2. **用药提醒**：到点不打扰但会主动提，过时不催但会观察。
3. **危机升级**：识别自伤/摔倒/胸口闷等关键词，主动播报给预设的紧急联系人。

快速开始：

.. code-block:: python

    from pasm_agents import ElderlyCompanion

    comp = ElderlyCompanion(agent_id="chenxiulan", persona={
        "name": "陈秀兰", "age": 78, "city": "深圳",
        "tone": "慢、温和、爱重复说过的话",
        "key_facts": [
            {"label": "用药", "content": "每天早 8 点吃降压药络活喜 5mg"},
            {"label": "过敏", "content": "青霉素过敏"},
            {"label": "家人", "content": "女儿在深圳，每周日下午来电话"},
            {"label": "本人", "content": "78 岁，独居，腿脚不便"},
        ],
        "emergency_contact": {"name": "女儿小敏", "phone": "13900000000"},
        "medication_schedule": [
            {"name": "络活喜", "dose": "5mg", "hour": 8},
        ],
    })
    comp.chat("我叫什么名字")
    print(comp.mood)
    if comp.detect_crisis("胸口闷得厉害"):
        comp.escalate("胸口闷")
"""

from __future__ import annotations

import random
import re
import time
from typing import Any, Dict, List, Optional

from pasm_skills.sdk import BaseAgent


# 危机关键词 —— 命中立即升级。留出扩展位（按需加方言/同义说法）。
CRISIS_KEYWORDS: Dict[str, List[str]] = {
    "胸闷/心梗风险": ["胸口闷", "胸口疼", "心慌", "喘不上气", "心里发慌"],
    "摔倒/外伤":     ["摔了", "摔倒了", "地上", "起不来", "滑倒"],
    "意识异常":      ["头晕", "眼前发黑", "站不稳", "想吐"],
    "自伤/轻生":     ["不想活", "走了算了", "没意思"],
}


def _crisis_scan(text: str) -> List[str]:
    """扫一遍文本，返回所有命中的危机类别。"""
    hits = []
    for cat, kws in CRISIS_KEYWORDS.items():
        if any(k in text for k in kws):
            hits.append(cat)
    return hits


class ElderlyCompanion(BaseAgent):
    """陪伴型产品智能体：老人/独居人群。"""

    def __init__(self, agent_id: str, persona: Dict[str, Any], **kw):
        super().__init__(agent_id=agent_id, persona=persona, **kw)
        # 把 key_facts 在首次启动时全部入库（salience=5：不许忘）
        if self.state.total_interactions == 0:
            for i, f in enumerate(self.persona.get("key_facts") or []):
                self.observe(
                    title=f"{f['label']}：{f['content'][:18]}",
                    brief=f["content"],
                    tags=[f["label"], "关键事实", "不许忘"],
                    salience=5,
                    category="关键事实",
                )

    # ------- 行为池（陪伴场景比较收敛） -------------------------

    def action_pool(self) -> List[str]:
        return ["chat", "remind", "ask_back", "listen", "warm"]

    # ------- 引导 -------------------------------------------------

    def bootstrap_event(self) -> List[Dict[str, Any]]:
        return [{
            "title": "今天感觉怎么样？",
            "brief": "每天都先问一声",
            "tags": ["问候"],
            "salience": 1,
            "category": "问候",
        }]

    # ------- 聊天渲染 --------------------------------------------

    def _render_reply(
        self,
        text: str,
        facts: List[Dict[str, Any]],
        mood: float,
    ) -> str:
        p = self.persona
        name = p.get("name", "奶奶")
        tone = p.get("tone", "温和")

        # 1. 关键事实直查 —— 用户问"我叫什么"/"我吃什么药"等
        label_q = _label_query(text, labels=self.fact_labels)
        if label_q:
            hit = self._find_fact(label_q)
            if hit:
                return f"{name}想了想：「{hit['content']}」。记得清楚。"

        # 2. 命中了任何关键事实 → 主动提
        for f in facts:
            if "关键事实" in (f.get("tags") or []):
                brief = f.get("brief") or ""
                if brief and brief[:8] in text:
                    return f"{name}点头：「{brief}」。"

        # 3. 情绪偏负 → 主动安慰
        if mood < -0.4:
            return f"{name}愣了一下：「{random_kind()}」"

        # 4. 兜底（重复也无所谓，老人家就是会重复）
        lines = [
            "嗯嗯，我在听。",
            "这样啊，那你想聊点啥？",
            "（轻轻拍拍你的手）",
            "今天出门了没有呀？",
        ]
        return f"{name}：{random.choice(lines)}"

    # ------- 工具方法：危机识别 / 升级 --------------------------

    def detect_crisis(self, text: str) -> List[str]:
        """返回命中的危机类别列表。空列表 = 未命中。"""
        return _crisis_scan(text)

    def escalate(
        self, reason: str, contact: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """危机升级：写入紧急记忆 + 返回给上层（UI/IM）的升级信息。

        不会真的打电话 —— 那是上层调用方的事；
        产品智能体的职责是"识别 + 准备好上下文"，让真人/系统及时介入。
        """
        self.observe(
            title=f"⚠ 危机：{reason}",
            brief=f"触发原因：{reason}",
            tags=["危机", reason[:4], "已升级"],
            salience=5,
            category="危机",
        )
        self.feel(reason, valence=-0.6)
        target = contact or self.persona.get("emergency_contact") or {}
        return {
            "agent_id": self.agent_id,
            "persona_name": self.persona.get("name"),
            "reason": reason,
            "suggested_action": "立即联系紧急联系人或拨打 120",
            "emergency_contact": target,
            "snapshot": self.summary(),
            "ts": time.time(),
        }

    # ------- 用药提醒 --------------------------------------------

    def due_medication(self, now_hour: Optional[int] = None) -> List[Dict[str, Any]]:
        """返回此刻到点的药品（缺省按本地小时）。"""
        if now_hour is None:
            import datetime
            now_hour = datetime.datetime.now().hour
        due = []
        for m in self.persona.get("medication_schedule") or []:
            try:
                if int(m.get("hour", -1)) == now_hour:
                    due.append(m)
            except Exception:
                continue
        return due

    # ------- 内部工具 --------------------------------------------

    @property
    def fact_labels(self) -> List[str]:
        """persona 里实际存在的关键事实标签（供直查与自定义标签命中用）。"""
        out: List[str] = []
        for f in self.persona.get("key_facts") or []:
            lab = f.get("label")
            if lab and lab not in out:
                out.append(lab)
        return out

    def _find_fact(self, label: str) -> Optional[Dict[str, Any]]:
        """按标签精确检索关键事实（最高优先级检索路径）。"""
        for f in self.persona.get("key_facts") or []:
            if f.get("label") == label:
                return f
        return None


# ============================================================ 工具


#: 口语 → 标签 的别名表。老人**真实说话**用词散，而标签直查是"确定性命中"，
#: 所以这里必须按"老人会怎么说"来列，而不是按"标签长什么样"来列。
#:
#: **匹配顺序即优先级，且顺序是刻意排的**：``过敏 > 用药 > 家人 > 本人``。
#: 为什么 `过敏` 必须排在 `用药` 前面：「我对什么药过敏」这句话**同时**含
#: 用药词（什么药）与过敏词（过敏）；按"先命中先赢"，若用药在前，
#: 老人问过敏会被答成用药事实 —— 这类歧义不是理论问题，是探针里真会出现的一条。
#:
#: **值是字面串，不是正则**（v0.4.6 起）。原因：正则表里 `儿子|儿子` 这种重复项
#: 一旦写进去没人看得出来（`儿子|儿子` 与 `儿子` 等价），而字面表可以用
#: `len(pats) == len(set(pats))` 机械查重；`in` 匹配也更快、没有转义坑。
#:
#: 要加方言 / 地区说法，两条路：
#:   ① 改这里（内置词表）；
#:   ② `pasm_agents.register_label_aliases({"家人": ("屋里的",)})` —— 运行时加，不必改源码。
#: 另有一条零配置通路：`persona.key_facts` 里**自定义标签**（≥2 字，如「糖尿病」「血压」）
#: 在问句里原样出现时也会被直接命中。
LABEL_ALIASES: Dict[str, tuple] = {
    "过敏": (
        "过敏", "不能吃", "不能碰", "不能入口", "忌口", "忌嘴",
        "吃了难受", "吃了不舒服", "不耐受",
        # 老人问过敏常绕开"过敏"二字，用"会不舒服/不敢吃"这类迂回说法。
        # 刻意只收"会不舒服 / 会难受"这种**带前导词**的形态，
        # 不收光杆"不舒服""难受" —— 那会把"我今天身体不舒服"判成过敏。
        "会不舒服", "会难受", "吃不得", "不敢吃", "不良反应",
    ),
    "用药": (
        "药", "吃药", "服药", "用药", "吃的药", "吃什么药", "什么药",
        "药品", "药物", "药片", "药丸", "几粒", "吃几片", "吃几次",
        "几点吃药", "降压药", "降糖药",
    ),
    "家人": (
        "家人", "家里", "家庭", "亲人", "亲属", "亲戚",
        "孩子", "娃", "儿女", "子女", "闺女", "姑娘", "女儿", "儿子",
        "孙子", "孙女", "外孙", "老伴", "老头", "老公", "老婆", "老太婆",
        "媳妇", "儿媳", "女婿", "兄弟", "姐妹", "爹", "娘", "妈", "爸",
        "谁给我", "谁会来", "谁来看我", "谁会来看我", "看望我", "谁回来",
        "什么时候回来", "来看我",
    ),
    "本人": (
        "我叫什么", "我的名字", "我叫啥", "叫啥", "我姓", "姓什么",
        "谁是我", "我是谁", "多大", "几岁", "多少岁", "年龄", "年纪",
        "生日", "住哪", "住在哪", "住址", "地址", "老家", "哪里人",
    ),
}


def register_label_aliases(
    mapping: Dict[str, Any], *, prepend: bool = True,
) -> Dict[str, tuple]:
    """运行时扩充「口语 → 标签」别名表（加方言 / 地区说法**不必改源码**）。

    :param mapping: ``{标签: 说法}``；值可以是单个字符串或字符串序列，
        标签可以是四个内置标签之一（扩说法），也可以是**全新的标签名**。
    :param prepend: ``True``（默认）时新规则优先于内置规则；``False`` 时只作补充。
    :return: 合并后的别名表。

    刻意**就地更新** ``LABEL_ALIASES``（``clear()`` + ``update()``）而不是重新绑定新 dict：
    本模块被 `pasm_agents/__init__.py` 按名字导入，一旦重新绑定，外面拿到的还是旧表 ——
    这正是 PASM 踩过的"属性拷贝式分叉"（见 `tools/check_core_fork.py` 的分叉铁律）。

    用法::

        from pasm_agents import register_label_aliases
        register_label_aliases({"家人": ("屋里的", "俺家那口子")})   # 方言
    """
    incoming: Dict[str, tuple] = {}
    for lab, terms in mapping.items():
        if isinstance(terms, str):
            terms = (terms,)
        incoming[str(lab)] = tuple(str(t) for t in terms)

    merged: Dict[str, tuple] = {}
    if prepend:
        for lab, terms in incoming.items():
            merged[lab] = tuple(dict.fromkeys(terms))
        for lab, terms in LABEL_ALIASES.items():
            merged[lab] = tuple(dict.fromkeys(tuple(merged.get(lab, ())) + tuple(terms)))
    else:
        for lab, terms in LABEL_ALIASES.items():
            merged[lab] = tuple(terms)
        for lab, terms in incoming.items():
            merged[lab] = tuple(dict.fromkeys(tuple(merged.get(lab, ())) + terms))

    LABEL_ALIASES.clear()
    LABEL_ALIASES.update(merged)
    return LABEL_ALIASES


#: 只为了把空白（含全角空格）抹掉再匹配 —— 老人打字/语音转写常带空格。
_WS_RE = re.compile(r"[\s\u3000]+")


def _label_query(text: str, labels: Optional[List[str]] = None) -> Optional[str]:
    """把自然语言里的"我吃什么药 / 我叫什么 / 谁给我打电话"翻成标签。

    :param labels: 本次 persona 实际存在的标签，用于零配置命中自定义标签
        （如「糖尿病」）。文本里原样出现 ≥2 字的标签名即视为命中。
    """
    s = _WS_RE.sub("", text or "")
    if not s:
        return None
    # 0) persona 自定义标签原样出现 —— 让用户自己起的名也能直查
    for lab in labels or []:
        if lab and len(str(lab)) >= 2 and str(lab) in s:
            return str(lab)
    # 1) 内置别名表：按"老人会怎么说"匹配（字面包含，顺序即优先级）
    for lab, terms in LABEL_ALIASES.items():
        for term in terms:
            if term and term in s:
                return lab
    return None


def random_kind() -> str:
    from random import choice
    return choice([
        "别怕，我在。",
        "要不要我给闺女打个电话？",
        "要不要先坐下来喝口水？",
        "要不咱们先歇一会儿。",
    ])