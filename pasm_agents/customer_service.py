"""CustomerServiceAgent 的稳定入口 —— 实现在 `agents/product/customer_service/`。

本模块只做转发：公开 API 与目录结构无关，
`from pasm_agents import CustomerServiceAgent` 不受重构影响。

与另外三个产品的一处**实质差别**：本产品建在应用框架的 ``BaseApplication`` 上
（需要 ``pasm-framework``，而它本来就是 ``pasm-agents`` 的依赖），
因为"客服"的核心能力是**资料库** —— 那是框架的 ``knowledge_base`` 插件，
不是基座 SDK 里有的东西。
"""
from __future__ import annotations

from agents.product.customer_service import (  # noqa: F401
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
