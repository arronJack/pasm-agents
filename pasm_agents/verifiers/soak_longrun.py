"""SoakLongrunAgent 的稳定入口 —— 实现在 `agents/verifiers/soak_longrun/`（每个智能体一个文件夹）。

本模块只做转发：公开 API 与历史版本完全一致，
所以 `from pasm_agents import SoakLongrunAgent` 不受目录重构影响。
"""
from __future__ import annotations

from agents.verifiers.soak_longrun import (  # noqa: F401
    SoakLongrunAgent,
)

__all__ = [
    "SoakLongrunAgent",
]
