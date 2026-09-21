"""CustomerServiceAgent —— 智能客服：就资料作答 / 客诉转人工 / 可接大模型。

实现正文在 `agent.py`；本文件只做转发，方便 `from <包路径> import CustomerServiceAgent`。
"""
from __future__ import annotations

from .agent import (  # noqa: F401
    CustomerServiceAgent,
    DEFAULT_FAQ,
    DEFAULT_PERSONA,
    ESCALATION_RULES,
    detect_escalation,
)

__all__ = [
    "CustomerServiceAgent",
    "DEFAULT_FAQ",
    "DEFAULT_PERSONA",
    "ESCALATION_RULES",
    "detect_escalation",
]
