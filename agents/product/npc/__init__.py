"""NpcAgent —— 游戏 NPC：记忆 / 情绪 / 反馈塑形

实现正文在 `agent.py`；本文件只做转发，方便 `from <包路径> import NpcAgent`。
"""
from __future__ import annotations

from .agent import (  # noqa: F401
    NpcAgent,
    NPC_ACTIONS,
    NPC_PERSONA_TEMPLATE,
)

__all__ = [
    "NpcAgent",
    "NPC_ACTIONS",
    "NPC_PERSONA_TEMPLATE",
]
