"""LearningTutor 的稳定入口 —— 实现在 `agents/product/tutor/`（每个智能体一个文件夹）。

本模块只做转发：公开 API 与历史版本完全一致，
所以 `from pasm_agents import LearningTutor` 不受目录重构影响。
"""
from __future__ import annotations

from agents.product.tutor import (  # noqa: F401
    LearningTutor,
    DEFAULT_TOPICS,
)

__all__ = [
    "LearningTutor",
    "DEFAULT_TOPICS",
]
