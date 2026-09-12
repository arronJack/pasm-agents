"""NpcAgent 的 60 秒上手示例。

直接跑：
    python agents/product/npc/quickstart.py

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

from pasm_agents import NpcAgent  # noqa: E402


def main() -> None:
    npc = NpcAgent(agent_id="herbalist", persona={
        "name": "陈伯", "role": "河边摆摊的草药老头",
        "temper": 0.55, "energy": 0.40, "play": 0.30,
        "tone": "慢悠悠、爱讲道理",
    })
    npc.observe("玩家第一次来买跌打药", tags=["玩家", "买药"], salience=4, category="日常")
    print(npc.act())                        # 'talk' / 'wave' / 'peek' / ...
    print(npc.chat("有跌打药吗"))            # 召回相关记忆
    print(npc.mood)                         # 情绪值（属性，不加括号）
    npc.feedback("praise", action="talk")   # 明确夸 "talk" 这个动作
    npc.save()

    print()
    print("[ok] 完成")


if __name__ == "__main__":
    main()
