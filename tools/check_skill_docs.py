"""检查技能正文里的"指引"是否和仓库现状一致。

为什么需要它
------------
`skill/SKILL.*.body.md` 是**给智能体读的操作说明** —— 里面写着"装什么、clone 哪个仓、跑什么命令"。
仓库一重构（比如 2026-09-12 把智能体从 `pasm-skills` 拆到 `pasm-agents`），
正文就会**静默失准**：文档说 `git clone pasm-skills && run --all`，
而那个仓里已经一个智能体都没有了。**没有任何测试会因此变红**，但用户照做就是跑不动。

这类"文档与结构脱节"最适合用机器查 —— 它不需要理解语义，只需要盯住几条硬事实：

  1. 本仓（智能体仓）的指引里，**不许**"只 clone 基座仓"当拿到智能体了；
  2. 指引里出现的 `pip install X` / `git clone .../X`，X 必须是已知存在的仓；
  3. 指引里出现的 `pasm_skills.xxx` / `pasm_agents.xxx` 模块路径必须真实可导入；
  4. 指引里出现的 CLI 子命令必须在对应 CLI 里存在；
  5. 指引里**不许**出现给维护者看的内部注释（它会原样出现在平台上用户看到的页面里）；
  6. 指引里**不许**出现拆仓后的过期导航（`cd pasm-skills && python -m pasm_agents …`）。

**扫描范围 = `skill/SKILL.*.body.md` + `examples/*.py`**，因为两者都是"用户会照着做"的文本。
（2026-09-21 补 `examples/`：那三份示例的 docstring 里就藏着第 6 类过期指令，
只因为当时"只扫 skill/"而长期漏网 —— 检查的**范围**和它的规则一样需要被审视。）

用法：
    python tools/check_skill_docs.py          # 退出码 0=通过，1=有问题
"""
from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skill"
EXAMPLES_DIR = ROOT / "examples"

#: 已知仓库（出现在 clone / pip install 里就必须是这些之一）
#: ★ 新仓落地后必须同步登记，否则正文里合法的引用会被判为"未知仓库"。
#:   2026-09-20 拆分出的 `pasm-framework`（应用开发框架）与
#:   2026-09-21 新建的 `pasm-customer-service`（专业客服系统）就各漏登记过一次 ——
#:   漏登记的后果不是"检查变松"，而是**正文里正确的东西被判错**，人会开始无视这个检查。
KNOWN_REPOS = {
    "pasm-skills", "pasm-agents", "pasm-framework", "pasm-customer-service",
    "pasm-mcp-server", "pasm-qclaw", "PASM-Lite", "PASM",
}

#: 本仓是智能体仓 —— 智能体在这儿，不在基座仓
SELF_REPO = "pasm-agents"
BASE_REPO = "pasm-skills"

#: 基座 CLI 的子命令（与实际实现保持一致）
BASE_CLI_SUBCMDS = {"list", "agents", "repos", "selftest", "run"}

#: 长得像模块路径、但**不是**模块的标识符。
#: entry point 组名（如 `pasm_skills.agents`）就是这种 —— 它是字符串名，import 必失败。
#: 新增时请写清"为什么它不是模块"，别当垃圾桶用。
NOT_MODULES = {
    "pasm_skills.agents": "entry point 组名（智能体包用来注册自己），不是模块",
}

#: 维护者内部注释的特征串 —— 这些是写给改正文的人看的，不该发给用户
INTERNAL_MARKERS = (
    "SKILL.md 的正文部分",
    "build_skill.py 会把它",
    "产出可直接上传的包",
)


def iter_bodies():
    """产出所有**用户会照着做**的指引文本：技能正文 + 示例脚本。

    为什么把 `examples/` 也纳进来（2026-09-21 补）
    ----------------------------------------------
    原来只扫 `skill/SKILL.*.body.md`。结果 `examples/*_quickstart.py` 的 docstring 里
    一直留着 `cd pasm-skills && python -m pasm_agents demo npc` —— 拆仓后这条指令
    **必然失败**（基座仓里一个智能体都没有）。和技能正文是**同一个病**，
    只因为"检查只扫 skill/"而漏网了。

    教训：这类检查的**扫描范围**本身就是最该被审视的东西 ——
    范围划窄了，它守得再好也只守住一小块。
    """
    for p in sorted(SKILL_DIR.glob("SKILL.*.body.md")):
        yield p, p.read_text(encoding="utf-8")
    for p in sorted(EXAMPLES_DIR.glob("*.py")):
        yield p, p.read_text(encoding="utf-8")


#: 拆仓后的典型**过期导航指令**：让用户去基座仓跑产品智能体。
#: 加新条目时请写清"为什么它必然失败"，别当垃圾桶用。
STALE_NAVIGATION = (
    ("cd pasm-skills",
     "基座仓里一个智能体都没有（2026-09-12 拆仓），进去跑 `pasm_agents` 必然失败"),
)


def check_stale_navigation(problems: list) -> None:
    for path, text in iter_bodies():
        for pat, why in STALE_NAVIGATION:
            if pat in text:
                problems.append("%s：出现过期导航指令 `%s` —— %s" % (path.name, pat, why))


def check_clone_targets(problems: list) -> None:
    """clone 的仓必须已知；且智能体仓的正文不许"只 clone 基座仓"。

    注意：**同时** clone 两个仓是合法的（纯源码跑的场景），
    要拦的是"只 clone 基座仓就当拿到智能体了" —— 那是拆仓后最容易犯的错。
    """
    for path, text in iter_bodies():
        cloned = set()
        for m in re.finditer(r"git clone\s+(\S+)", text):
            url = m.group(1)
            repo = url.rstrip("/").removesuffix(".git").rsplit("/", 1)[-1]
            cloned.add(repo)
            if repo not in KNOWN_REPOS:
                problems.append("%s：clone 了未知仓库 %s" % (path.name, url))
        if BASE_REPO in cloned and SELF_REPO not in cloned:
            problems.append(
                "%s：**只** clone 了基座仓 `%s` —— 但智能体在本仓 `%s`，"
                "基座仓里一个智能体都没有（这正是 2026-09-12 拆仓踩过的坑）"
                % (path.name, BASE_REPO, SELF_REPO))


def check_pip_targets(problems: list) -> None:
    """`pip install X` 的 X 必须是已知包。

    要按**词**遍历而不是按正则抓第一个 token —— 否则
    `pip install --upgrade pasm-agents` 会把 `--upgrade` 当成包名（真的踩过）。
    同时要先切掉行尾注释：`pip install pasm-agents  # 自动带上基座 pasm-skills`
    里的注释会被误当成第二个包名（也真踩过）。
    """
    for path, text in iter_bodies():
        for m in re.finditer(r"pip install([^\n`]*)", text):
            code = m.group(1).split("#", 1)[0]       # 去掉行尾注释
            for tok in code.split():
                if tok.startswith("-"):          # --upgrade / -e / -U / -r …
                    continue
                pkg = re.split(r"[\[>=<;]", tok)[0]
                if not pkg or pkg.startswith(".") or pkg == "install":
                    continue
                # 只对本项目相关的包名做校验，别人的包不管
                if pkg.startswith("pasm") and pkg not in KNOWN_REPOS:
                    problems.append("%s：pip install 了未知包 %s" % (path.name, pkg))


def check_module_paths(problems: list) -> None:
    """正文里写的模块路径必须真实可导入（防止重构后名字变了文档没改）。"""
    seen: set = set()
    for path, text in iter_bodies():
        for m in re.finditer(r"`(pasm_skills(?:\.[a-z_]+)*|pasm_agents(?:\.[a-z_]+)*)`", text):
            mod = m.group(1)
            if mod in seen:
                continue
            seen.add(mod)
            if mod in NOT_MODULES:               # entry point 组名之类，不是模块
                continue
            try:
                importlib.import_module(mod)
            except Exception as ex:                  # noqa: BLE001
                problems.append("%s：模块 `%s` 无法导入（%s）" % (path.name, mod, ex))


def check_cli_subcommands(problems: list) -> None:
    """正文里 `python -m pasm_skills <sub>` 的子命令必须存在。"""
    for path, text in iter_bodies():
        for m in re.finditer(r"python -m pasm_skills\s+([a-z\-]+)", text):
            sub = m.group(1)
            if sub not in BASE_CLI_SUBCMDS:
                problems.append("%s：基座 CLI 没有子命令 `%s`" % (path.name, sub))


def check_agent_names(problems: list) -> None:
    """正文提到的验证智能体名必须真在注册表里（需先装/挂上本仓）。"""
    try:
        import pasm_agents.verifiers  # noqa: F401
        from pasm_skills.agent import names
    except Exception as ex:                          # noqa: BLE001
        problems.append(
            "无法加载注册表（%s）—— 检查 PYTHONPATH 是否**同时**含基座仓与本仓"
            "（两个都要在，缺本仓时智能体注册表就是空的）" % ex)
        return
    registered = set(names())
    for path, text in iter_bodies():
        for m in re.finditer(r"`(core-verifier|parity-guard|regression|npc-lifelong|"
                             r"companion-elderly|study-tutor|soak-longrun)`", text):
            if m.group(1) not in registered:
                problems.append("%s：提到智能体 `%s`，但它没注册上" % (path.name, m.group(1)))


def check_no_internal_notes(problems: list) -> None:
    """正文里不许有给维护者看的内部注释。

    真实翻车：四份正文开头都写着
        > 本文件是 SKILL.md 的正文部分（不含 frontmatter）…
        > tools/build_skill.py 会把它拼上两套 frontmatter…
    这段**原样出现在平台上用户点开的 SKILL.md 里**（ClawHub 实测）。
    维护者说明应该放 `skill/README.md`。
    """
    for path, text in iter_bodies():
        for marker in INTERNAL_MARKERS:
            if marker in text:
                problems.append(
                    "%s：含维护者内部注释「%s」—— 它会原样出现在用户看到的技能页上，"
                    "请移到 skill/README.md" % (path.name, marker))


def main() -> int:
    bodies = list(iter_bodies())
    if not bodies:
        print("[FAIL] %s 与 %s 下都没有可检查的指引文本" % (SKILL_DIR, EXAMPLES_DIR))
        return 1

    problems: list = []
    for fn in (check_clone_targets, check_pip_targets, check_module_paths,
               check_cli_subcommands, check_agent_names, check_no_internal_notes,
               check_stale_navigation):
        try:
            fn(problems)
        except Exception as ex:                      # noqa: BLE001
            problems.append("%s 自身出错：%s" % (fn.__name__, ex))

    n_skill = len(list(SKILL_DIR.glob("SKILL.*.body.md")))
    n_ex = len(list(EXAMPLES_DIR.glob("*.py")))
    print("检查 %d 份指引文本（技能正文 %d + 示例脚本 %d，7 类）"
          % (len(bodies), n_skill, n_ex))
    if problems:
        print("[FAIL] 发现 %d 个问题：" % len(problems))
        for p in problems:
            print("  - %s" % p)
        return 1
    print("[OK] 指引与仓库现状一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
