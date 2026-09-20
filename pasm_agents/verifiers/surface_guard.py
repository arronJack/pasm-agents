"""SurfaceGuardAgent 的稳定入口 —— 实现在 `agents/verifiers/surface_guard/`（每个智能体一个文件夹）。

本模块只做转发：公开 API 与历史版本保持一致，
所以 `from pasm_agents import SurfaceGuardAgent` 不受目录重构影响。
"""
from __future__ import annotations

from agents.verifiers.surface_guard import (  # noqa: F401
    SurfaceGuardAgent,
)

__all__ = ["SurfaceGuardAgent"]
