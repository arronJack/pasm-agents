"""LearningTutor —— 学习陪伴：掌握度 / 自适应选题 / 学情导出

实现正文在 `agent.py`；本文件只做转发，方便 `from <包路径> import LearningTutor`。
"""
from __future__ import annotations

from .agent import (  # noqa: F401
    LearningTutor,
    DEFAULT_TOPICS,
)

__all__ = [
    "LearningTutor",
    "DEFAULT_TOPICS",
]
