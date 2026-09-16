"""ProductVerifierAgent 的稳定入口 —— 实现在 `agents/verifiers/product_verifier/`（每个智能体一个文件夹）。

本模块只做转发：公开 API 与历史版本保持一致，
所以 `from pasm_agents import ProductVerifierAgent` 不受目录重构影响。
"""
from __future__ import annotations

from agents.verifiers.product_verifier import (  # noqa: F401
    ProductVerifierAgent,
)

__all__ = ["ProductVerifierAgent"]
