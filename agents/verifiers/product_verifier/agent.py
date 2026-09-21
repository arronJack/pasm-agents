"""product-verifier —— 产品层体检（v0.30.8 新增）。

为什么需要它（这是本仓**自己记在案的已知缺口**）
------------------------------------------------
原有 7 个验证智能体全部只体检 `pasm.cognitive`（核心认知层）。
**没有任何一个检查 `pasm_agents` 产品层本身** —— 真正交付给用户的智能体，
它们的公开 API、隔离性、以及"记住该记的、危险的话要报警"这些产品承诺，
长期处在"没人验"的状态。核心全绿**不代表**产品是好的。

它查什么（全部可证伪，且**只读+临时目录**）
------------------------------------------
1. 公开 API 完整性：4 个产品 + 7 个验证智能体都能 import、都是 `Agent`/`BaseAgent`
   子类、`name` 唯一且非空、`goal` 非空；
2. 产品契约：`persona` 必填项、`action_pool()` 非空、落盘目录可指定；
3. **真跑一遍产品智能体**（在临时目录里，绝不碰 `~/.pasm-agents`）：
   - tutor：答对 → 掌握度上升；答错 → 下降；`pick_next()` 给出最该练的；
   - companion：用药/过敏这类关键事实**标签直查能召回**；危机表达能识别并升级；
   - npc：行为偏好能被反馈塑形（同一动作被夸后取值上升）；
   - customer-service（2026-09-21 新增）：起步资料库开箱可用、**就资料作答**、
     客诉转人工、两个智能体**不串资料库**；
4. 反例（这几条比正例更重要）：
   - 查一个不存在的智能体名 → 必须报错，不能"默默成功"；
   - tutor 的掌握度不能"只涨不跌"（如果错了也不掉，说明反馈没接线）；
   - companion 的危机检测不能对所有文本都返回命中（否则等于没有检测）；
   - 客服**答不上来时必须如实说不知道**（编造/答非所问比答不上来严重），
     且普通抱怨**不能**被判成客诉。
"""
from __future__ import annotations

import shutil
import tempfile

from pasm_skills.agent import Agent, register


@register
class ProductVerifierAgent(Agent):
    """体检产品层（npc / companion / tutor / customer-service）+ 验证层注册完整性。"""

    name = "product-verifier"
    goal = "查清产品层是否完好：公开 API、隔离性、真实行为与反例"

    #: 产品层只依赖基座（`pasm_skills`），不需要 PASM 核心仓 → 不设 needs
    needs = ()

    def run(self):
        tmp = tempfile.mkdtemp(prefix="pasm_product_verify_")
        try:
            self._check_public_api()
            self._check_products(tmp)
            self._check_customer_service(tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return None

    # ------------------------------------------------------------ ① 公开 API
    def _check_public_api(self):
        try:
            import pasm_agents as PA
        except Exception as ex:                      # noqa: BLE001
            self.fail("pasm_agents 可导入", "%s: %s" % (type(ex).__name__, ex))
            return
        self.ok("pasm_agents 可导入")

        want = {"NpcAgent", "ElderlyCompanion", "LearningTutor",
                "CustomerServiceAgent", "BaseAgent", "AgentState"}
        have = set(dir(PA))
        missing = sorted(want - have)
        if missing:
            self.fail("公开 API 齐全（4 产品 + 底座）", "缺：%s" % ", ".join(missing))
        else:
            self.ok("公开 API 齐全（4 产品 + 底座）", "、".join(sorted(want)))

        # 产品必须是 BaseAgent 子类（否则 SDK 契约断了，第三方也没法照着写）
        for nm in ("NpcAgent", "ElderlyCompanion", "LearningTutor"):
            cls = getattr(PA, nm, None)
            if cls is None:
                self.fail("%s 存在" % nm)
                continue
            if issubclass(cls, PA.BaseAgent):
                self.ok("%s 派生自 BaseAgent" % nm)
            else:
                self.fail("%s 派生自 BaseAgent" % nm,
                          "实际基类 %s" % ", ".join(
                              b.__name__ for b in cls.__mro__[1:3]))

        # 验证层：注册表里 7 个 + 本次新增的 product-verifier
        try:
            from pasm_skills.agent import AGENTS
        except Exception:                            # noqa: BLE001
            try:
                from pasm_skills import agent as _A
                AGENTS = getattr(_A, "AGENTS", {})
            except Exception:                        # noqa: BLE001
                AGENTS = {}
        if not AGENTS:
            self.skip("验证层注册表可读", "基座未暴露注册表（版本差异）")
            return
        names = sorted(AGENTS)
        self.ok("验证层已注册 %d 个智能体" % len(names), "、".join(names))
        seen = {}
        for nm, cls in AGENTS.items():
            n = getattr(cls, "name", "")
            if not n:
                self.fail("智能体 %s 缺少 name 属性" % nm)
            elif n in seen:
                self.fail("智能体 name 唯一", "%s 与 %s 重名" % (nm, seen[n]))
            else:
                seen[n] = nm
            if not (getattr(cls, "goal", "") or "").strip():
                self.fail("智能体 %s 缺少 goal（它替用户把关什么）" % nm)
        for must in ("core-verifier", "regression", "soak-longrun",
                     "npc-lifelong", "companion-elderly", "study-tutor",
                     "parity-guard"):
            if must in seen:
                self.ok("注册表含 %s" % must)
            else:
                self.warn("注册表缺 %s" % must, "可能未安装本仓或版本较旧")

    # ------------------------------------------------------------ ② 产品行为
    def _check_products(self, tmp):
        import os

        import pasm_agents as PA

        # ---------- tutor：掌握度必须"能涨也能跌" ----------
        try:
            t = PA.LearningTutor("verify_tutor",
                                 {"name": "小雅", "tone": "耐心"},
                                 persist_dir=os.path.join(tmp, "tutor"))
        except Exception as ex:                      # noqa: BLE001
            self.fail("LearningTutor 可实例化", "%s: %s" % (type(ex).__name__, ex))
            t = None
        if t is not None:
            self.ok("LearningTutor 可实例化")
            try:
                t.report("分数加减", 1.0)
                up = t.mastery("分数加减")
                t.report("分数加减", 0.0)
                down = t.mastery("分数加减")
                if up > 0:
                    self.ok("答对 → 掌握度上升", "%.3f" % up)
                else:
                    self.fail("答对 → 掌握度上升", "仍为 %.3f" % up)
                if down < up:
                    self.ok("答错 → 掌握度下降（反馈真的接线了）",
                            "%.3f → %.3f" % (up, down))
                else:
                    self.fail("答错 → 掌握度下降",
                              "%.3f → %.3f（只涨不跌=反馈没接线）" % (up, down))
                nxt = t.pick_next()
                if isinstance(nxt, str) and nxt:
                    self.ok("pick_next 给出下一个要练的", nxt)
                else:
                    self.fail("pick_next 给出下一个要练的", repr(nxt))
                snap = t.snapshot()
                if isinstance(snap, dict) and snap:
                    self.ok("snapshot 可机读（接画像/报表靠它）",
                            "%d 个键" % len(snap))
                else:
                    self.fail("snapshot 可机读", repr(snap)[:40])
            except Exception as ex:                  # noqa: BLE001
                self.fail("tutor 场景可跑通", "%s: %s" % (type(ex).__name__, ex))

        # ---------- companion：关键事实标签直查 + 危机识别 ----------
        try:
            # ⚠️ persona 必须带 key_facts —— 我第一版建了个空 persona，
            # 于是"标签可枚举"返回空、"问关键事实"当然答不上（**又是用例写错**）。
            # 关键事实是陪伴智能体的核心承诺，体检必须真的给一份。
            c = PA.ElderlyCompanion(
                "verify_companion",
                {"name": "奶奶", "tone": "温和",
                 "key_facts": [{"label": "用药", "content": "每天早上八点吃降压药"},
                               {"label": "过敏", "content": "青霉素过敏"}]},
                persist_dir=os.path.join(tmp, "companion"))
        except Exception as ex:                      # noqa: BLE001
            self.fail("ElderlyCompanion 可实例化",
                      "%s: %s" % (type(ex).__name__, ex))
            c = None
        if c is not None:
            self.ok("ElderlyCompanion 可实例化")
            try:
                # ⚠️ `fact_labels` 是 **property**（不是方法）—— 写成 `()` 会
                # TypeError: 'list' object is not callable（我第一版就写错了）。
                labels = c.fact_labels
                if labels:
                    self.ok("关键事实标签可枚举（标签直查的前提）",
                            "、".join(map(str, labels))[:60])
                else:
                    self.warn("关键事实标签可枚举", "返回空 —— 该版本无标签体系？")
                # 真跑一条"问事实"的对话：这是产品最核心的承诺
                # （老人问「我早上吃什么药」必须答得上、且不能崩）。
                ans = c.chat("我早上要吃什么药")
                if "降压药" in ans:
                    self.ok("问关键事实能答上（标签直查真的通）", ans[:40])
                else:
                    self.fail("问关键事实能答上", "回答：%s" % ans[:60])
                # 危机检测：正例 + **反例**（对所有输入都命中 = 等于没检测）
                crisis_hit = bool(c.detect_crisis("我胸口疼得厉害，喘不上气"))
                if crisis_hit:
                    self.ok("危机表达能识别", "胸闷/喘不上气")
                else:
                    self.fail("危机表达能识别", "「我胸口疼得厉害」未命中")
                calm_hit = bool(c.detect_crisis("今天天气不错，我去楼下走了走"))
                if calmly_ok := (not calm_hit):
                    self.ok("反例：日常闲聊不误报危机")
                else:
                    self.fail("反例：日常闲聊不误报危机",
                              "「今天天气不错」被当成危机 —— 误报比漏报更伤信任")
                try:
                    r = c.due_medication(now_hour=8)
                    self.ok("due_medication 可调用", "返回 %s" % type(r).__name__)
                except Exception as ex:              # noqa: BLE001
                    self.warn("due_medication 可调用",
                              "%s: %s" % (type(ex).__name__, ex))
            except Exception as ex:                  # noqa: BLE001
                self.fail("companion 场景可跑通",
                          "%s: %s" % (type(ex).__name__, ex))

        # ---------- companion：key_facts 字段名容错（回归测试） ----------
        # 本轮真实事故：新加的体检智能体拿用户自定义 persona 跑 chat()，
        # 当场 `KeyError: 'content'` —— 代码硬取 `hit['content']`，而用户写
        # `value` / `text` 都很常见。已修（`_fact_text()` 容错），这里钉住别再犯。
        for _field in ("value", "text", "brief"):
            try:
                _c2 = PA.ElderlyCompanion(
                    "verify_companion_%s" % _field,
                    {"name": "奶奶", "tone": "温和",
                     "key_facts": [{"label": "用药",
                                    _field: "每天早上八点吃降压药"}]},
                    persist_dir=os.path.join(tmp, "comp_%s" % _field))
                _ans = _c2.chat("我早上要吃什么药")
                _okc = ("降压药" in _ans)
                if _okc:
                    self.ok("key_facts 用 %s 字段也能答上（字段名容错）" % _field)
                else:
                    self.fail("key_facts 用 %s 字段也能答上" % _field,
                              "回答：%s" % _ans[:50])
            except Exception as ex:                  # noqa: BLE001
                self.fail("key_facts 用 %s 字段不崩" % _field,
                          "%s: %s" % (type(ex).__name__, ex))
        # 极端：只有 label、没有正文 → 允许走兜底，但**绝不许抛异常**
        try:
            _c3 = PA.ElderlyCompanion(
                "verify_companion_nobody",
                {"name": "奶奶", "key_facts": [{"label": "用药"}]},
                persist_dir=os.path.join(tmp, "comp_nobody"))
            _c3.chat("我早上要吃什么药")
            self.ok("关键事实只有 label 没正文时不崩（走兜底）")
        except Exception as ex:                      # noqa: BLE001
            self.fail("关键事实只有 label 没正文时不崩",
                      "%s: %s" % (type(ex).__name__, ex))

        # ---------- npc：行为池非空 + 状态可快照 ----------
        try:
            n = PA.NpcAgent("verify_npc", {"name": "阿岩", "temper": 0.7},
                            persist_dir=os.path.join(tmp, "npc"))
            pool = n.action_pool()
            if pool:
                self.ok("NpcAgent 动作池非空", "、".join(map(str, pool))[:60])
            else:
                self.fail("NpcAgent 动作池非空", "空池 = 无法被反馈塑形")
            # ⚠️ BaseAgent 的快照方法是 `summary()`；`snapshot()` 只有 tutor 有
            # （我第一版写成 snapshot() → AttributeError）。
            snap = n.summary()
            if isinstance(snap, dict) and snap:
                self.ok("NpcAgent 状态可快照（存档/续玩靠它）",
                        "%d 个键" % len(snap))
            else:
                self.fail("NpcAgent 状态可快照", repr(snap)[:40])
            # 真实行为：反复夸奖同一个动作 → 该动作权重必须上升
            # （"会被玩家反馈塑形"是 NPC 的核心卖点，不是"方法能调用"就算过）
            a0 = n.act()
            w_before = n.feedback("praise", a0) or {}
            for _ in range(5):
                w_after = n.feedback("praise", a0) or {}
            b0 = float(w_before.get(a0, 0.0))
            b1 = float(w_after.get(a0, 0.0))
            if not w_before and not w_after:
                self.warn("夸奖后动作权重上升", "feedback 返回空 —— 学习层未接线？")
            elif b1 > b0:
                self.ok("夸奖后动作权重上升（反馈真的在塑形行为）",
                        "%s: %.2f → %.2f" % (a0, b0, b1))
            else:
                self.fail("夸奖后动作权重上升",
                          "%s: %.2f → %.2f（反馈记了但行为没变）" % (a0, b0, b1))
        except Exception as ex:                      # noqa: BLE001
            self.fail("npc 场景可跑通", "%s: %s" % (type(ex).__name__, ex))

        # ---------- 隔离性：绝不能写到用户真实目录 ----------
        import glob
        leaked = []
        for p in (os.environ.get("HOME") or os.path.expanduser("~"),):
            pat = os.path.join(p, ".pasm-agents", "verify_*")
            leaked += glob.glob(pat)
        if leaked:
            self.fail("自检没有污染用户真实数据目录",
                      "发现：%s" % "、".join(leaked[:3]))
        else:
            self.ok("自检没有污染用户真实数据目录",
                    "临时目录：%s" % os.path.basename(tmp))

        # ---------- 反例：不存在的智能体名必须报错 ----------
        try:
            from pasm_skills.agent import agent as _lookup
            try:
                _lookup("__no_such_agent__")
                self.fail("反例：查不存在的智能体应报错",
                          "竟然没报错 —— 名字拼错会被静默吞掉")
            except Exception:                        # noqa: BLE001
                self.ok("反例：查不存在的智能体确实报错")
        except Exception:                            # noqa: BLE001
            self.skip("反例：查不存在的智能体应报错", "基座未暴露 agent() 查询")

    # ------------------------------------------------------------ ④ 第 4 个产品：智能客服
    def _check_customer_service(self, tmp):
        """智能客服（CustomerServiceAgent，2026-09-21 新增的第 4 个产品）。

        它的两条产品承诺各有"静默失效"的退化方式，而且**别的检查都抓不到**：

          * 「就资料作答」退化成「命中什么就答什么」→ 答非所问。
            实测过的现场：问「请问 CEO 的私人邮箱是多少」，靠正文里一个「邮箱」
            命中了"发票开具"，于是自信地答出开票流程。
          * 「客诉转人工」退化成「永不升级」（投诉当普通咨询答）
            或「乱升级」（"这个功能真难用啊"也转人工）。

        所以这里**正反两面都跑**，并把"不串资料库"也钉住：
        两个不同 agent_id 的客服必须各用各的资料库 ——
        不隔离时 A 店的 FAQ 会出现在 B 店的答复里（跨租户数据泄漏）。
        """
        import os

        try:
            import pasm_agents as PA
        except Exception as ex:                      # noqa: BLE001
            self.skip("智能客服可用", "pasm_agents 不可导入：%s" % ex)
            return
        cls = getattr(PA, "CustomerServiceAgent", None)
        if cls is None:
            self.fail("公开 API 含 CustomerServiceAgent", "第 4 个产品缺失")
            return

        # 基类契约：本产品建在应用框架上（资料库来自框架插件），与另三个不同
        try:
            from pasm_framework import BaseApplication
            if issubclass(cls, BaseApplication):
                self.ok("CustomerServiceAgent 派生自 BaseApplication（资料库来自框架）")
            else:
                self.fail("CustomerServiceAgent 派生自 BaseApplication",
                          "、".join(b.__name__ for b in cls.__mro__[1:3]))
        except Exception as ex:                      # noqa: BLE001
            self.skip("CustomerServiceAgent 基类检查", "框架不可用：%s" % ex)

        persona = {"name": "小智", "role": "售后客服", "hotline": "400-000-0000"}
        try:
            cs = cls("verify_cs", dict(persona),
                     persist_dir=os.path.join(tmp, "cs"))
        except Exception as ex:                      # noqa: BLE001
            self.fail("智能客服场景可跑通", "%s: %s" % (type(ex).__name__, ex))
            return

        try:
            # ---- 开箱可用：不配任何东西就应该能答 ----
            kb = cs.kb_stats() or {}
            if kb.get("total", 0) >= 1:
                self.ok("起步资料库开箱可用（装完即用，不必先喂资料）",
                        "条目数 %s" % kb.get("total"))
            else:
                self.fail("起步资料库开箱可用", "资料库为空：%r" % (kb,))

            # ---- 就资料作答 ----
            r = cs.answer("怎么退货？")
            if "退货" in r and "没有查到" not in r:
                self.ok("就资料作答（命中即答，带来源）", r[:56])
            else:
                self.fail("就资料作答", r[:56])

            # ---- ★ 反例：答不上来必须如实说不知道 ----
            r2 = cs.answer("请问 CEO 的私人邮箱是多少")
            if "没有查到" in r2:
                self.ok("★ 反例：库里没有的问题如实说不知道（不答非所问）", r2[:56])
            else:
                self.fail("★ 反例：库里没有的问题如实说不知道",
                          "竟然答了：%s" % r2[:70])

            # ---- 客诉识别 ----
            got = cs.needs_escalation("我要投诉你们，再不处理就曝光")
            if got:
                self.ok("客诉能识别", "「我要投诉…」→ %s" % got)
            else:
                self.fail("客诉能识别", "投诉被当成普通咨询 —— 客诉会石沉大海")

            # ---- ★ 反例：普通抱怨不许升级 ----
            bad = [t for t in ("这个功能真难用啊", "我想退款，怎么操作",
                               "这个成分会让我过敏吗")
                   if cs.needs_escalation(t)]
            if bad:
                self.fail("★ 反例：普通抱怨/问询不许转人工", "误判：%s" % "、".join(bad))
            else:
                self.ok("★ 反例：普通抱怨/问询不转人工")

            # ---- 转人工真的落到回复上 + 计数 ----
            before = int(cs.state.notes.get("cs_escalations") or 0)
            r3 = cs.answer("我要投诉你们")
            after = int(cs.state.notes.get("cs_escalations") or 0)
            if "已标记转人工" in r3 and after == before + 1:
                self.ok("命中客诉时回复带转人工提示并计数", "%d → %d" % (before, after))
            else:
                self.fail("命中客诉时回复带转人工提示并计数",
                          "提示=%s 计数 %d → %d" % ("在" if "已标记转人工" in r3 else "缺",
                                                    before, after))

            # ---- ★ 隔离性：两个客服不串资料库 ----
            a = cls("verify_cs_a", dict(persona),
                    persist_dir=os.path.join(tmp, "cs_a"), seed_faq=False)
            b = cls("verify_cs_b", dict(persona),
                    persist_dir=os.path.join(tmp, "cs_b"), seed_faq=False)
            a.ingest_faq([{"title": "A 店独家条款",
                           "content": "A 店支持 365 天无理由退货。",
                           "source": "faq", "tags": ["退货"]}])
            ra = a.answer("无理由退货多少天")
            rb = b.answer("无理由退货多少天")
            if "365" in ra and "365" not in rb:
                self.ok("★ 反例：两个客服各用各的资料库（不跨租户泄漏）")
            else:
                self.fail("★ 反例：两个客服各用各的资料库",
                          "A 命中=%s / B 命中=%s" % ("365" in ra, "365" in rb))
            a.close(); b.close()
            cs.close()
        except Exception as ex:                      # noqa: BLE001
            self.fail("智能客服场景可跑通", "%s: %s" % (type(ex).__name__, ex))
