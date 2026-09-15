"""ElderlyCompanion 的稳定入口 —— 实现在 `agents/product/companion/`（每个智能体一个文件夹）。

本模块只做转发：公开 API 与历史版本完全一致，
所以 `from pasm_agents import ElderlyCompanion` 不受目录重构影响。
"""
from __future__ import annotations

from agents.product.companion import (  # noqa: F401
    ElderlyCompanion,
    CRISIS_KEYWORDS,
    LABEL_ALIASES,
    random_kind,
    register_label_aliases,
)

__all__ = [
    "ElderlyCompanion",
    "CRISIS_KEYWORDS",
    "LABEL_ALIASES",
    "random_kind",
    "register_label_aliases",
]
