"""ParityGuardAgent —— 两仓一致性：核心仓 ↔ Studio 仓同名文件逐字比对

实现正文在 `agent.py`；本文件只做转发，方便 `from <包路径> import ParityGuardAgent`。
"""
from __future__ import annotations

from .agent import ParityGuardAgent  # noqa: F401

__all__ = ["ParityGuardAgent"]
