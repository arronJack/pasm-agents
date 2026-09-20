"""独立跑 surface-guard —— V1↔V2 稳定表面守门（4 产品 + 3 技能 + 框架表面）

    python agents/verifiers/surface_guard/run.py

等价于在仓库根执行（这里只是帮你把发现路径配好）：

    python -m pasm_skills run surface-guard
"""
import os
import subprocess
import sys
from pathlib import Path

# 源码方式跑：基座（pasm-skills）可能还没装 —— 把本仓和它一起放到 PYTHONPATH 上。
# 只设 PASM_SKILLS_AGENT_MODULES 是不够的：那让基座能找到本仓的智能体，
# 但基座本身得先能被 import，否则 `python -m pasm_skills` 直接报
# "No module named 'pasm_skills'" —— README 承诺的「clone 后直接跑」就断了。
_REPO = Path(__file__).resolve().parents[3]
env = dict(os.environ)
env["PYTHONPATH"] = os.pathsep.join(
    p for p in (str(_REPO), str(_REPO.parent / "pasm-skills"),
                env.get("PYTHONPATH", "")) if p
)
# 用这个环境变量代替 entry point，让基座发现本仓的智能体
env.setdefault("PASM_SKILLS_AGENT_MODULES", "pasm_agents.verifiers")

# 还是找不到基座就直说该怎么修，不要让用户去猜 ImportError
if subprocess.call([sys.executable, "-c", "import pasm_skills"], env=env) != 0:
    print(
        "找不到基座 pasm-skills —— 本仓的验证智能体跑在它之上。\n"
        "  · 已装过就用：python -m pasm_skills run <name>\n"
        "  · 只想跑源码：把 pasm-skills 与 pasm-agents clone 到同一层目录",
        file=sys.stderr,
    )
    raise SystemExit(2)

raise SystemExit(subprocess.call(
    [sys.executable, "-m", "pasm_skills", "run", "surface-guard"], env=env,
))
