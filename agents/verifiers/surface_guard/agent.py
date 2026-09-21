"""surface-guard —— V1↔V2 稳定表面守门（4 产品智能体 + 4 技能 + 框架表面）。

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
1. **框架表面**（任务②产物，最该守）：pasm_framework 的 **30 个契约名**
   （核心 14 + v0.2/v0.3 扩展 16；`__all__` 共 31 项含 `__version__`）都在、
   `__all__` 无悬空名；
   CognitiveAssembler.v1 能装配出后端、BaseApplication 在临时目录里真跑通、
   handle() 能力路由 + 回落 chat 都生效；装配出的后端仍满足 CognitiveBackend
   （即"换 V2 后端零改动"的承诺没被破）；BaseApplication 是 BaseAgent 子类
   （4 产品 reparent 到它的迁移路径活着）。
   1b. **插件子系统**（v0.2.0）：build_manager 能装配（含内联自定义插件）、
   enabled 开关生效、拼错的配置名进 `unknown()`（不静默吞）、
   **全关插件时 handle 仍与 v0.1.0 一致**（兼容底线）。
   1c. **开发效率**（v0.2.1）：配置预设 >= 6 套且 load/to_dict/describe 往返正常、
   SimpleApplication + @capability 命中、`ingest()` 未启用知识库时**显式报错**
   （不许静默返回 0）、`stream()` 产出 delta/replace + done 事件序列。
2. **产品表面**（4 智能体）：pasm_agents 公开 API 里所有 BaseAgent 子类都能
   import + 在临时目录里 observe/act/feedback/recall + tier 合法；且 4 个已知产品
   （NpcAgent / ElderlyCompanion / LearningTutor / CustomerServiceAgent）在位。
   数据驱动——新增产品自动覆盖。
   > 注意一个**反直觉但关键**的事实：客服产品建在框架的 `BaseApplication` 上，
   > 却仍能被这里的 `issubclass(obj, BaseAgent)` 认出来 —— 因为
   > **`BaseApplication` 本身就是 `BaseAgent` 的子类**。别以为"换了底座就漏检了"；
   > 真正会让它漏检的是**忘了在 `pasm_agents/__init__.py` 里按需导出它**。
3. **技能表面**（4 技能）：skill/ 下 SKILL.*.body.md 全部存在且非空，4 个产品技能
   （companion / npc / tutor / cs-agent）在位；新技能框架 BaseSkill 能产出合法 manifest、
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
    """V1↔V2 稳定表面守门：4 产品智能体 + 4 技能 + 框架表面。"""

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

        # 契约名分两组：拆仓时确立的核心 14 名 + v0.2/v0.3 新增的扩展表面。
        # 只断言「必须都在」（required ⊆ actual），不锁死全集 —— 新增表面不算回归，
        # 删除 / 改名 / 漏改 __all__ 才算。历史上这里写死 14 名，框架演进到 31 名后
        # 守门名不副实（新增的插件子系统 / SimpleApplication / stream / ingest 无人守），
        # 本组扩展即为补齐该缺口。
        core = [
            "CognitiveAssembler", "CognitiveService", "CognitiveBackend",
            "DomainAdapter", "NullDomainAdapter", "StaticDomainAdapter",
            "Capability", "CapabilityDiscovery",
            "BaseApplication", "BaseSkill", "SkillManifest",
            "FrameworkError", "SurfaceMissing", "BackendContractBroken",
        ]
        ext = [
            # 开发效率（v0.2.1）：3 行起步
            "SimpleApplication", "capability",
            # 配置系统（v0.2.1）：预设 / 落盘 / 展示
            "load", "preset", "save", "to_dict", "describe", "PRESETS",
            # 插件子系统（v0.2.0）：即插即用的底座
            "PluginManager", "Plugin", "BasePlugin", "Message", "PluginContext",
            "BackendConfig", "build_manager", "default_config",
        ]
        expect = core + ext
        missing = [n for n in expect if not hasattr(fw, n)]
        label = "框架表面导出齐全（%d 名：核心 %d + 扩展 %d）" % (
            len(expect), len(core), len(ext))
        if missing:
            self.fail(label, "缺：%s" % ", ".join(missing))
        else:
            self.ok(label, "、".join(ext))

        # __all__ 自洽：列出来的名字必须真能取到（防改名后漏改 __all__ 的静默漂移）
        dangling = [n for n in getattr(fw, "__all__", []) if not hasattr(fw, n)]
        if dangling:
            self.fail("框架 __all__ 自洽（无悬空名）", "悬空：%s" % ", ".join(dangling))
        else:
            self.ok("框架 __all__ 自洽（共 %d 名，无悬空）"
                    % len(getattr(fw, "__all__", [])))

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

        # v0.2/v0.3 新增表面：插件子系统 + 开发效率（行为级，不只查名字在不在）
        self._check_plugin_surface(fw, tmp)
        self._check_devtools_surface(fw, tmp)

    # ------------------------------------------------------ ①b 插件子系统表面
    def _check_plugin_surface(self, fw, tmp):
        """插件子系统：装配 / 开关 / 内联自定义插件 / 未知名暴露 / 全关兼容底线。

        「全关时行为与 v0.1.0 一致」是插件化的兼容底线 —— 一旦被破，
        老用户的代码会在升级后静默变行为，最难查。
        """
        import os

        class _Probe(fw.BasePlugin):
            """内联自定义插件（使用者不写进仓，只在配置里开）。"""

            name = "_surface_probe"

            def on_reply(self, ctx):
                if not ctx.message.reply:
                    ctx.message.reply = "probe"

        try:
            pm = fw.build_manager({
                "knowledge_base": {"enabled": True,
                                   "config": {"kb_dir": os.path.join(tmp, "kb")}},
                "_surface_probe": {"enabled": True, "class": _Probe},
            })
        except Exception as ex:                      # noqa: BLE001
            self.fail("插件：build_manager 可装配（含内联自定义插件 class=）",
                      "%s: %s" % (type(ex).__name__, ex))
            return
        self.ok("插件：build_manager 可装配（含内联自定义插件 class=）")

        names = pm.names()
        if "_surface_probe" in names and "knowledge_base" in names:
            self.ok("插件：内置 + 自定义插件均注册", "、".join(sorted(names)))
        else:
            self.fail("插件：内置 + 自定义插件均注册", "实际：%s" % "、".join(sorted(names)))

        if pm.is_enabled("knowledge_base") and pm.is_enabled("_surface_probe"):
            self.ok("插件：enabled 开关生效")
        else:
            self.fail("插件：enabled 开关生效",
                      "knowledge_base=%s probe=%s" % (pm.is_enabled("knowledge_base"),
                                                      pm.is_enabled("_surface_probe")))

        # 拼错的插件名不得被静默吞 —— 「配置写了却没生效」的经典假失败
        try:
            unk = fw.build_manager({"knowlege_base": {"enabled": True}}).unknown()
            if unk == ["knowlege_base"]:
                self.ok("插件：拼错的配置名被显式记录（unknown()）", "、".join(unk))
            else:
                self.fail("插件：拼错名进 unknown()", "实际 %r" % unk)
        except Exception as ex:                      # noqa: BLE001
            self.fail("插件：拼错名进 unknown()", "%s: %s" % (type(ex).__name__, ex))

        # 兼容底线：全关插件时 handle == v0.1.0（能力路由 → 回落 chat）
        try:
            class _Bare(fw.BaseApplication):
                def action_pool(self):
                    return ["a1"]

                def _render_reply(self, text, facts, mood):
                    return "bare:%s" % text

            bare = _Bare(
                agent_id="surface_bare", persona={"name": "x"},
                persist_dir=os.path.join(tmp, "bare"),
                backend_config=fw.load(preset_name="minimal"),
            )
            got = bare.handle("你好")
            if isinstance(got, str) and got.startswith("bare:"):
                self.ok("插件：全关时 handle 与 v0.1.0 一致（回落 chat，兼容底线）")
            else:
                self.fail("插件：全关时 handle 回落 chat", "返回 %r" % got)
        except Exception as ex:                      # noqa: BLE001
            self.fail("插件：全关时 handle 行为一致", "%s: %s" % (type(ex).__name__, ex))

    # ------------------------------------------------------ ①c 开发效率表面
    def _check_devtools_surface(self, fw, tmp):
        """SimpleApplication / @capability / stream() / ingest() / 配置预设。

        这些是 v0.2/v0.3 让「更快更优地开发应用」的关键表面：
        写应用只需 3 行、资料摄取有唯一入口、回复可流式下发。
        """
        import os

        # —— 配置系统：预设 + 序列化往返 ——
        try:
            presets = fw.PRESETS
            if isinstance(presets, dict) and len(presets) >= 6:
                self.ok("配置：场景预设 >= 6 套（实测 %d）" % len(presets),
                        "、".join(sorted(presets)))
            else:
                self.fail("配置：场景预设 >= 6 套", "实际 %r" % (list(presets or [])))
        except Exception as ex:                      # noqa: BLE001
            self.fail("配置：PRESETS 可取", "%s: %s" % (type(ex).__name__, ex))
        try:
            cfg = fw.load(preset_name="chatbot")
            d = fw.to_dict(cfg)
            if isinstance(d, dict) and "plugins" in d and fw.describe(cfg):
                self.ok("配置：load/to_dict/describe 往返正常")
            else:
                self.fail("配置：load/to_dict/describe 往返", repr(d)[:60])
        except Exception as ex:                      # noqa: BLE001
            self.fail("配置：load/to_dict/describe 可用",
                      "%s: %s" % (type(ex).__name__, ex))

        # —— SimpleApplication + @capability（3 行起步）——
        try:
            class _Mini(fw.SimpleApplication):
                @fw.capability(keywords=("退款", "退钱"))
                def refund(self, text):
                    return "退款入口：/refund"

            mini = _Mini(
                "surface_mini", {"name": "x"},
                persist_dir=os.path.join(tmp, "mini"),
                backend_config=fw.load(preset_name="minimal"),
            )
            r = mini.ask("我要退款")
            if r == "退款入口：/refund":
                self.ok("开发效率：SimpleApplication + @capability 命中")
            else:
                self.fail("开发效率：@capability 命中", "返回 %r" % r)
        except Exception as ex:                      # noqa: BLE001
            self.fail("开发效率：SimpleApplication 可实例化",
                      "%s: %s" % (type(ex).__name__, ex))

        # —— ingest() 未启用知识库时必须显式报错（不许静默返回 0）——
        try:
            nk = fw.SimpleApplication(
                "surface_nokb", {"name": "x"},
                persist_dir=os.path.join(tmp, "nokb"),
                backend_config=fw.load(preset_name="minimal"),
            )
            try:
                nk.ingest([{"title": "t", "content": "c"}])
                self.fail("开发效率：ingest() 未启用知识库时显式报错",
                          "静默返回了 —— 正是「喂了资料却答不上来」的假失败源头")
            except fw.FrameworkError:
                self.ok("开发效率：ingest() 未启用知识库时显式报错（不静默）")
        except Exception as ex:                      # noqa: BLE001
            self.fail("开发效率：ingest() 未启用时报错",
                      "%s: %s" % (type(ex).__name__, ex))

        # —— stream() 必须产出 delta/replace + done（真事件流）——
        try:
            class _Stream(fw.BaseApplication):
                def action_pool(self):
                    return ["a1"]

                def _render_reply(self, text, facts, mood):
                    return "流式回复内容"

            st = _Stream(
                "surface_stream", {"name": "x"},
                persist_dir=os.path.join(tmp, "stream"),
                backend_config=fw.load(preset_name="minimal"),
            )
            evs = list(st.stream("你好"))
            kinds = [e.get("type") for e in evs]
            ok_tail = bool(kinds) and kinds[-1] == "done"
            ok_body = any(k in ("delta", "replace") for k in kinds)
            if ok_tail and ok_body:
                self.ok("开发效率：stream() 产出 delta/replace + done",
                        "事件序列 %s" % kinds)
            else:
                self.fail("开发效率：stream() 事件序列", "实际 %s" % kinds)
        except Exception as ex:                      # noqa: BLE001
            self.fail("开发效率：stream() 可用", "%s: %s" % (type(ex).__name__, ex))

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

        # 已知产品必须仍在位（防改名/误删破坏下游）
        for must in ("NpcAgent", "ElderlyCompanion", "LearningTutor",
                     "CustomerServiceAgent"):
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

        for must in ("companion", "npc", "tutor", "cs-agent"):
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
