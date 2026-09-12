"""CoreVerifierAgent 的稳定入口 —— 实现在 `agents/verifiers/core_verifier/`（每个智能体一个文件夹）。

本模块只做转发：公开 API 与历史版本完全一致，
所以 `from pasm_agents import CoreVerifierAgent` 不受目录重构影响。
"""
from __future__ import annotations

from agents.verifiers.core_verifier import (  # noqa: F401
    CoreVerifierAgent,
)

__all__ = [
    "CoreVerifierAgent",
]
