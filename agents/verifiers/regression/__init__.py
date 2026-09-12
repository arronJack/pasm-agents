"""RegressionAgent —— 静默退化：对事实基线（文件指纹 / 引擎清单 / 契约版本）逐项核对

实现正文在 `agent.py`；本文件只做转发，方便 `from <包路径> import RegressionAgent`。
"""
from __future__ import annotations

from .agent import RegressionAgent  # noqa: F401

__all__ = ["RegressionAgent"]
