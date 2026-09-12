"""LearningTutor 的 60 秒上手示例。

直接跑：
    python agents/product/tutor/quickstart.py

（pip install pasm-agents 之后可以把上面那段 sys.path 引导删掉）
"""
import sys
from pathlib import Path

# 从源码直接跑时用（pip install pasm-agents 之后可以删掉这几行）：
#   把仓库根加进 sys.path，才能 import pasm_agents
_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO))
try:
    import pasm_agents  # noqa: F401
except ImportError:
    _sib = _REPO.parent / "pasm-skills"
    if _sib.is_dir():
        sys.path.insert(0, str(_sib))

from pasm_agents import LearningTutor  # noqa: E402


def main() -> None:
    tutor = LearningTutor(agent_id="xiaoya", persona={
        "name": "小雅", "grade": "五年级",
        "topics": ["分数加减", "面积计算", "行程问题", "鸡兔同笼"],
    })
    tutor.report("分数加减", 0.4)       # 这次做对了 40%
    tutor.report("分数加减", 0.5)
    tutor.report("面积计算", 0.9)
    print(tutor.pick_next())             # 最该练的那个知识点
    print(tutor.chat("分数加减好难"))      # 鼓励式回应，不是打击式
    print(tutor.snapshot())              # 可机读学情
    tutor.save()

    print()
    print("[ok] 完成")


if __name__ == "__main__":
    main()
