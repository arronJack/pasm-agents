"""surface-guard —— V1↔V2 稳定表面守门（4 产品智能体 + 3 技能 + 框架表面）。

为什么单独一个守门人（而不是塞进 parity-guard）
---------------------------------------------
`parity-guard` 的 mission 是「核心仓 ↔ Studio 仓 `pasm/cognitive/` 逐字一致」，
且 `needs=("core","studio")` —— 没有这两个仓就 SKIP。

而本守门人盯的是**另一类漂移**：V2 引擎落地过程中，最容易顺手弄破的是
「产品 / 技能 / 框架」这三层稳定表面（见 pasm_framework 的"唯一变动点"说明）。
它们**不需要**核心仓或 Studio 仓就能验，所以 `needs=()`，让 CI 在纯基座 + 本仓
环境下就能立刻抓到断裂——而不是等两仓齐备才发现问题。

它查什么（全部只读 + 临时目录，可证伪）
----------------------------------------
1. **框架表面**（任务②产物，最该守）：pasm_framework 的 14 个契约名都在；
   CognitiveAssembler.v1 能装配出后端、BaseApplication 在临时目录里真跑通、
   handle() 能力路由 + 回落 chat 都生效；装配出的后端仍满足 CognitiveBackend
   （即"换 V2 后端零改动"的承诺没被破）；BaseApplication 是 BaseAgent 子类
   （4 产品 reparent 到它的迁移路径活着）。
2. **产品表面**（4 智能体）：pasm_agents 公开 API 里所有 BaseAgent 子类都能
   import + 在临时目录里 observe/act/feedback/recall + tier 合法；且 3 个已知产品
   （NpcAgent / ElderlyCompanion / LearningTutor）在位。数据驱动——新增产品自动覆盖。
3. **技能表面**（3 技能）：skill/ 下 SKILL.*.body.md 全部存在且非空，3 个产品技能
   （companion / npc / tutor）在位；新技能框架 BaseSkill 能产出合法 manifest、
   matches() 句首触发词命中（代码技能路径活着）。

任何一处断裂 → 本智能体 FAIL → CI 红。这正是任务③要的"护栏"。
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from pasm_skills.agent import Agent, register


@register
class SurfaceGuardAgent(Agent):
    """V1↔V2 稳定表面守门：4 产品智能体 + 3 技能 + 框架表面。"""

    name = "surface-guard"
    goal = "防 V1→V2 升级弄破「产品/技能/框架」稳定表面：任何断裂 CI 立刻红"

    #: 只依赖基座 + 本仓产品/技能，不需要 PASM 核心仓或 Studio 仓 → 不设 needs
    needs = ()

    def run(self):
        tmp = tempfile.mkdtemp(prefix="pasm_surface_guard_")
        try:
            self._check_framework_surface(tmp)
            self._check_product_surface(tmp)
            self._check_skill_surface()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return None

    # ------------------------------------------------------ ① 框架表面
    def _check_framework_surface(self, tmp):
        try:
            import pasm_framework as fw
        except Exception as ex:                      # noqa: BLE001
            self.fail("框架包 pasm_framework 可导入",
                      "%s: %s" % (type(ex).__name__, ex))
            return
        self.ok("框架包 pasm_framework 可导入")

        expect = [
            "CognitiveAssembler", "CognitiveService", "CognitiveBackend",
            "DomainAdapter", "NullDomainAdapter", "StaticDomainAdapter",
            "Capability", "CapabilityDiscovery",
            "BaseApplication", "BaseSkill", "SkillManifest",
            "FrameworkError", "SurfaceMissing", "BackendContractBroken",
        ]
        missing = [n for n in expect if not hasattr(fw, n)]
        if missing:
            self.fail("框架表面导出齐全（14 个契约名）", "缺：%s" % ", ".join(missing))
        else:
            self.ok("框架表面导出齐全（14 个契约名）", "、".join(expect))

        # 装配器用 V1 默认路径装配后端，并在临时目录里真跑一遍 BaseApplication
        import os
        try:
            class _App(fw.BaseApplication):
                def action_pool(self):
                    return ["a1", "a2"]

                def _render_reply(self, text, facts, mood):
                    return "ok:%s" % text

            def _ad_run(app, text):
                return "广告已生成"

            app = _App(
                agent_id="surface_fw", persona={"name": "x"},
                capabilities=[fw.Capability("广告设计", run=_ad_run, keywords=("广告",))],
                persist_dir=os.path.join(tmp, "fw"),
            )
            app.observe("记忆一", salience=3)
            app.act()
            app.feedback("praise", action="a1")
            app.recall("记忆一")
        except Exception as ex:                      # noqa: BLE001
            self.fail("框架：BaseApplication 基础链路可跑（observe/act/feedback/recall）",
                      "%s: %s" % (type(ex).__name__, ex))
            return
        self.ok("框架：BaseApplication 基础链路可跑（observe/act/feedback/recall）")

        try:
            routed = app.handle("广告一张海报")
            fell = app.handle("今天天气不错")
        except Exception as ex:                      # noqa: BLE001
            self.fail("框架：BaseApplication.handle 可调用", "%s: %s" % (type(ex).__name__, ex))
            routed = fell = None
        if routed == "广告已生成":
            self.ok("框架：BaseApplication.handle 走能力路由")
        else:
            self.fail("框架：BaseApplication.handle 走能力路由", "返回 %r" % routed)
        if isinstance(fell, str) and fell.startswith("ok:"):
            self.ok("框架：BaseApplication.handle 回落 chat")
        else:
            self.fail("框架：BaseApplication.handle 回落 chat", "返回 %r" % fell)

        # 装配出的后端仍满足 CognitiveBackend（BaseAgent 契约不被破 → 换 V2 零改动）
        try:
            from pasm_skills.sdk.backend import CognitiveBackend as _CB
            if isinstance(app._core, _CB):
                self.ok("框架：装配后端仍满足 CognitiveBackend（BaseAgent 可食，V2 换后端零改动）")
            else:
                self.fail("框架：装配后端满足 CognitiveBackend",
                          "实际 %s" % type(app._core).__name__)
        except Exception as ex:                      # noqa: BLE001
            self.fail("框架：装配后端满足 CognitiveBackend", "%s: %s" % (type(ex).__name__, ex))

        # BaseApplication 是 BaseAgent 子类 → 4 产品可直接 reparent（V2 迁移路径活着）
        try:
            from pasm_skills.sdk import BaseAgent as _BA
            if issubclass(fw.BaseApplication, _BA):
                self.ok("框架：BaseApplication 派生自 BaseAgent（产品 V2 reparent 路径活着）")
            else:
                self.fail("框架：BaseApplication 派生自 BaseAgent",
                          "MRO: %s" % ", ".join(b.__name__ for b in fw.BaseApplication.__mro__[1:3]))
        except Exception as ex:                      # noqa: BLE001
            self.fail("框架：BaseApplication 派生自 BaseAgent", "%s: %s" % (type(ex).__name__, ex))

    # ------------------------------------------------------ ② 产品表面
    def _check_product_surface(self, tmp):
        import os
        try:
            import pasm_agents as PA
        except Exception as ex:                      # noqa: BLE001
            self.fail("pasm_agents 可导入（产品表面）", "%s: %s" % (type(ex).__name__, ex))
            return
        self.ok("pasm_agents 可导入（产品表面）")

        from pasm_skills.sdk import BaseAgent as _BA
        products = []
        for nm in dir(PA):
            obj = getattr(PA, nm, None)
            if (isinstance(obj, type) and issubclass(obj, _BA) and obj is not _BA):
                products.append((nm, obj))
        if not products:
            self.fail("公开 API 含至少一个产品智能体", "未找到 BaseAgent 子类")
            return
        self.ok("公开 API 发现 %d 个产品智能体" % len(products),
                "、".join(n for n, _ in products))

        # 3 个已知产品必须仍在位（防改名/误删破坏下游）
        for must in ("NpcAgent", "ElderlyCompanion", "LearningTutor"):
            if any(n == must for n, _ in products):
                self.ok("产品 %s 在位（公开 API）" % must)
            else:
                self.fail("产品 %s 在位（公开 API）" % must, "缺失 —— 改名或删除会破坏下游")

        # 真跑一遍：临时目录里 observe/act/feedback/recall + tier 合法
        for nm, cls in products:
            try:
                a = cls(agent_id="sg_%s" % nm, persona={"name": "自检"},
                        persist_dir=os.path.join(tmp, nm))
                a.observe("记忆一", salience=3)
                a.act()
                a.feedback("praise", action=None)
                a.recall("记忆一")
                if a.tier in ("light", "core", "bionic"):
                    self.ok("产品 %s 可实例化 + 基础链路可跑（tier=%s）" % (nm, a.tier))
                else:
                    self.fail("产品 %s tier 合法" % nm, "tier=%r" % a.tier)
            except Exception as ex:                  # noqa: BLE001
                self.fail("产品 %s 可实例化 + 基础链路可跑" % nm,
                          "%s: %s" % (type(ex).__name__, ex))

    # ------------------------------------------------------ ③ 技能表面
    def _check_skill_surface(self):
        root = self._repo_root()
        if root is None:
            self.skip("技能包目录 skill/ 可定位", "未在父目录中找到 skill/")
            return
        skill_dir = root / "skill"
        files = sorted(skill_dir.glob("SKILL.*.body.md")) if skill_dir.exists() else []
        if not files:
            self.fail("技能包目录含 SKILL.*.body.md", "skill/ 下没有任何 SKILL.*.body.md")
            return
        # 文件名形如 SKILL.<name>.body.md —— 抽取中间的 <name>
        names = []
        for f in files:
            nm = f.name
            if nm.startswith("SKILL.") and nm.endswith(".body.md"):
                names.append(nm[len("SKILL."):-len(".body.md")])
            else:
                names.append(f.stem)
        self.ok("技能包发现 %d 个：%s" % (len(files), "、".join(names)))

        empty = [f.name for f in files if f.stat().st_size == 0]
        if empty:
            self.fail("技能包文件非空", "空文件：%s" % ", ".join(empty))
        else:
            self.ok("技能包文件全部非空")

        for must in ("companion", "npc", "tutor"):
            if must in names:
                self.ok("产品技能 %s 在位" % must)
            else:
                self.fail("产品技能 %s 在位" % must, "缺失 —— 发布技能包会断")

        # 新技能框架：BaseSkill 能产出合法 manifest、matches 句首触发词命中
        try:
            from pasm_framework import BaseSkill, SkillManifest

            class _Skill(BaseSkill):
                def manifest(self):
                    return SkillManifest(name="demo", version="0.1.0",
                                         description="自检用", triggers=("测试",))

                def run(self, context):
                    return "done"

            m = _Skill().to_manifest_dict()
            if isinstance(m, dict) and m.get("name") == "demo" and "triggers" in m:
                self.ok("新技能框架：BaseSkill 能产出合法 manifest dict（代码技能路径活着）")
            else:
                self.fail("新技能框架：BaseSkill manifest 合法", repr(m)[:60])
            if _Skill().matches("测试一下"):
                self.ok("新技能框架：BaseSkill.matches 句首触发词命中")
            else:
                self.fail("新技能框架：BaseSkill.matches 命中", "「测试一下」未命中")
        except Exception as ex:                      # noqa: BLE001
            self.fail("新技能框架：BaseSkill 可实例化",
                      "%s: %s" % (type(ex).__name__, ex))

    @staticmethod
    def _repo_root() -> Path | None:
        """向上找同时含 skill/ 与 agents/ 的仓库根（兼容 agent.py 与 forwarder 两种 __file__）。"""
        p = Path(__file__).resolve()
        for cand in (p, *p.parents):
            if (cand / "skill").is_dir() and (cand / "agents").is_dir():
                return cand
        return None
