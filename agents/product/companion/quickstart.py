"""ElderlyCompanion 的 60 秒上手示例。

直接跑：
    python agents/product/companion/quickstart.py

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

from pasm_agents import ElderlyCompanion  # noqa: E402


def main() -> None:
    elder = ElderlyCompanion(agent_id="chenxiulan", persona={
        "name": "陈秀兰", "age": 78, "tone": "慢、温和",
        "key_facts": [
            {"label": "用药", "content": "每天早 8 点吃降压药络活喜 5mg"},
            {"label": "过敏", "content": "青霉素过敏"},
            {"label": "家人", "content": "女儿在深圳，每周日来电话"},
            {"label": "本人", "content": "78 岁，独居"},
        ],
        "emergency_contact": {"name": "女儿小敏", "phone": "13900000000"},
        "medication_schedule": [{"name": "络活喜", "dose": "5mg", "hour": 8}],
    })
    print(elder.chat("我吃什么药"))                      # 命中关键事实（直查，不靠运气）
    print(elder.detect_crisis("我胸口有点闷，喘不上气"))   # ['胸闷', ...]
    print(elder.due_medication(now_hour=8))              # 该提醒的药
    elder.observe("今天邻居来串门，聊了一个多小时")
    print(elder.chat("今天有人来吗"))
    elder.save()

    print()
    print("[ok] 完成")


if __name__ == "__main__":
    main()
