"""独立跑 core-verifier —— 引擎接口契约、认知层是否落盘、符号推理闭环、环境插件、安全底线、冒烟

    python agents/verifiers/core_verifier/run.py

等价于在仓库根执行（这里只是帮你把发现路径配好）：

    python -m pasm_skills run core-verifier
"""
import os
import subprocess
import sys

env = dict(os.environ)
# 源码方式跑时，用这个环境变量代替 entry point 来让基座发现本仓的智能体
env.setdefault("PASM_SKILLS_AGENT_MODULES", "pasm_agents.verifiers")

raise SystemExit(subprocess.call(
    [sys.executable, "-m", "pasm_skills", "run", "core-verifier"], env=env,
))
