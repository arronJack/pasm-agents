"""检查技能正文里的"指引"是否和仓库现状一致。

为什么需要它
------------
`skill/SKILL.*.body.md` 是**给智能体读的操作说明** —— 里面写着"装什么、clone 哪个仓、跑什么命令"。
仓库一重构（比如 2026-09-12 把智能体从 `pasm-skills` 拆到 `pasm-agents`），
正文就会**静默失准**：文档说 `git clone pasm-skills && run --all`，
而那个仓里已经一个智能体都没有了。**没有任何测试会因此变红**，但用户照做就是跑不动。

这类"文档与结构脱节"最适合用机器查 —— 它不需要理解语义，只需要盯住几条硬事实：

  1. 本仓（智能体仓）的正文里，**不许**让人去 clone `pasm-skills` 找智能体；
  2. 正文里出现的 `pip install X` / `git clone .../X`，X 必须是已知存在的仓；
  3. 正文里出现的 `pasm_skills.xxx` / `pasm_agents.xxx` 模块路径必须真实可导入；
  4. 正文里出现的 CLI 子命令必须在对应 CLI 里存在。

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

#: 已知仓库（出现在 clone / pip install 里就必须是这些之一）
KNOWN_REPOS = {"pasm-skills", "pasm-agents", "pasm-qclaw", "PASM-Lite", "PASM"}

#: 本仓是智能体仓 —— 智能体在这儿，不在基座仓
SELF_REPO = "pasm-agents"
BASE_REPO = "pasm-skills"

#: 基座 CLI 的子命令（与实际实现保持一致）
BASE_CLI_SUBCMDS = {"list", "agents", "repos", "selftest", "run"}


def iter_bodies():
    for p in sorted(SKILL_DIR.glob("SKILL.*.body.md")):
        yield p, p.read_text(encoding="utf-8")


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
    for path, text in iter_bodies():
        for m in re.finditer(r"pip install\s+(?:-e\s+)?([A-Za-z0-9_\-.\[\]]+)", text):
            pkg = re.split(r"[\[>=<]", m.group(1))[0]
            if not pkg or pkg.startswith("."):
                continue
            if pkg not in KNOWN_REPOS and pkg not in ("-e",):
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
        problems.append("无法加载注册表（%s）—— 检查 PYTHONPATH 是否含基座仓" % ex)
        return
    registered = set(names())
    for path, text in iter_bodies():
        for m in re.finditer(r"`(core-verifier|parity-guard|regression|npc-lifelong|"
                             r"companion-elderly|study-tutor|soak-longrun)`", text):
            if m.group(1) not in registered:
                problems.append("%s：提到智能体 `%s`，但它没注册上" % (path.name, m.group(1)))


def main() -> int:
    bodies = list(iter_bodies())
    if not bodies:
        print("[FAIL] %s 下没有 SKILL.*.body.md" % SKILL_DIR)
        return 1

    problems: list = []
    for fn in (check_clone_targets, check_pip_targets, check_module_paths,
               check_cli_subcommands, check_agent_names):
        try:
            fn(problems)
        except Exception as ex:                      # noqa: BLE001
            problems.append("%s 自身出错：%s" % (fn.__name__, ex))

    print("检查 %d 份技能正文" % len(bodies))
    if problems:
        print("[FAIL] 发现 %d 个问题：" % len(problems))
        for p in problems:
            print("  - %s" % p)
        return 1
    print("[OK] 指引与仓库现状一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
