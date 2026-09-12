"""ElderlyCompanion —— 老人陪伴：关键事实 / 用药提醒 / 危机升级

实现正文在 `agent.py`；本文件只做转发，方便 `from <包路径> import ElderlyCompanion`。
"""
from __future__ import annotations

from .agent import (  # noqa: F401
    ElderlyCompanion,
    CRISIS_KEYWORDS,
    random_kind,
)

__all__ = [
    "ElderlyCompanion",
    "CRISIS_KEYWORDS",
    "random_kind",
]
