"""独立跑 study-tutor —— 30 天学习陪伴的掌握度结构与停练衰减

    python agents/verifiers/study_tutor/run.py

等价于在仓库根执行（这里只是帮你把发现路径配好）：

    python -m pasm_skills run study-tutor
"""
import os
import subprocess
import sys

env = dict(os.environ)
# 源码方式跑时，用这个环境变量代替 entry point 来让基座发现本仓的智能体
env.setdefault("PASM_SKILLS_AGENT_MODULES", "pasm_agents.verifiers")

raise SystemExit(subprocess.call(
    [sys.executable, "-m", "pasm_skills", "run", "study-tutor"], env=env,
))
