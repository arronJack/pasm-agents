"""独立跑 parity-guard —— 核心仓 ↔ Studio 镜像仓的同名文件是否逐字一致（防两仓分叉）

    python agents/verifiers/parity_guard/run.py

等价于在仓库根执行（这里只是帮你把发现路径配好）：

    python -m pasm_skills run parity-guard
"""
import os
import subprocess
import sys

env = dict(os.environ)
# 源码方式跑时，用这个环境变量代替 entry point 来让基座发现本仓的智能体
env.setdefault("PASM_SKILLS_AGENT_MODULES", "pasm_agents.verifiers")

raise SystemExit(subprocess.call(
    [sys.executable, "-m", "pasm_skills", "run", "parity-guard"], env=env,
))
