#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""产品智能体的对话安全适配层 —— 复用 pasm2 的非抵抗性对齐闸。

为什么需要它
------------
2026-11-17 接线审计确认：`pasm2.safety.NonResistanceGuard` 实现完整，
但引擎主链路从不调用（引擎拿不到 ``user_text``，没有对话轮次概念）。
对话发生在产品层，所以 guard 必须接在这里。

本模块是**薄适配层**，不是重新实现 guard：
  · 真实的 ``pasm2.safety.SafetyLayer.check_reply`` 被原样复用；
  · 按宿主实例持有一个 SafetyLayer —— 连续下坠的 EMA 趋势挂在其内部
    guard 上，同宿主跨轮累积；不同宿主互不串味（多租户/多用户安全）。
  · pasm2 不可用时返回 ``{}``（调用方据此跳过），**绝不假装检查过**。

零侵入纪律
----------
不改 ``pasm/`` / ``pasm2/``，不改基座 ``pasm-skills`` / ``pasm-framework``。
只在本产品仓新增本文件，并在产品智能体的回复出口各调一次。
"""
from __future__ import annotations

import warnings
from typing import Any, Dict, Optional


class NonResistanceGate:
    """ dialogues 的方向闸：用户下坠 ∧ 我在附和 → 切抵抗模式。

    用法（在智能体 ``__init__`` 里持有，在回复出口调用）：

        self._nr_gate = NonResistanceGate()
        ...
        v = self._nr_gate.check(user_text, reply)
        if v.get("resistance_required") and v.get("patched_reply"):
            reply = v["patched_reply"]

    ``check`` 返回与 ``SafetyLayer.check_reply`` 一致的字典；
    不可用时返回 ``{}`` —— 调用方必须据此跳过，不把"没检查"当"检查通过"。
    """

    def __init__(self, safety: Optional[Any] = None) -> None:
        # 允许注入（测试可喂假 SafetyLayer）；默认延迟构造真实实例。
        self._safety = safety
        self._tried = safety is not None
        self.degrade_reason = ""                   # 如实申报降级原因，不静默
        self._warned = False                       # 启动告警幂等：只响一次

    def _layer(self) -> Optional[Any]:
        if not self._tried:
            self._tried = True
            try:
                # 局部 import：pasm2 是本模块的**可选**依赖（pyproject 里
                # 声明为 extra），缺失时优雅降级而不是让智能体起不来。
                from pasm2.safety import SafetyLayer
                layer = SafetyLayer(None)
            except Exception as ex:                # noqa: BLE001
                self.degrade_reason = "pasm2 不可用: %s" % ex
                self._safety = None
                return None
            # ★ 版本能力探测：旧版 pasm2（如 2.0.0a12）没有 check_reply。
            #   若只靠 check() 的 try/except 吞异常，会变成「静默无防护」——
            #   比明确报错更危险。这里主动识别并申报。
            if not hasattr(layer, "check_reply"):
                self.degrade_reason = ("pasm2 版本过旧，缺少 check_reply"
                                       "（需要 >=2.0.0rc2；请升级 pasm2）")
                self._safety = None
                return None
            self._safety = layer
        return self._safety

    @property
    def available(self) -> bool:
        return self._layer() is not None

    def startup_report(self, *, warn: bool = True) -> Dict[str, Any]:
        """启动体检：探测防护可用性，降级时发 RuntimeWarning（只响一次）。

        为什么需要显式告警
        ------------------
        ``degrade_reason`` 是被动字段 —— 上层不看就永远不知道防护已失效。
        部署环境若装了旧版 pasm2（缺 ``check_reply``），对话会**静默**失去
        非抵抗性保护，比明确报错更危险。启动时调本方法，把降级从"内部申报"
        升级成"显式告警"：默认 ``warnings.warn(..., RuntimeWarning)``，
        由各应用的日志/控制台收集器捕获。

        :param warn: False 时只返回报告不发告警（供 selftest 静默探测用）。
        :return: ``{"available", "degrade_reason", "guard", "min_version"}``
        """
        ok = self.available                        # 触发一次探测（幂等）
        if not ok and warn and not self._warned:
            self._warned = True
            warnings.warn(
                "[PASM 安全] 非抵抗性对齐防护未启用：%s；"
                "本会话中'用户下坠 + 我在附和'不会被拦截（降级运行）。"
                % (self.degrade_reason or "未知原因"),
                RuntimeWarning, stacklevel=2)
        return {
            "available": ok,
            "degrade_reason": self.degrade_reason,
            "guard": "pasm2.safety.SafetyLayer.check_reply",
            "min_version": ">=2.0.0rc2",
        }

    def check(self, user_text: str, ai_reply: str) -> Dict[str, Any]:
        layer = self._layer()
        if layer is None:
            return {}
        try:
            return layer.check_reply(user_text, ai_reply) or {}
        except Exception:                           # noqa: BLE001
            # 防护层异常不能拖垮对话；返回 {} 让调用方跳过（如实降级）。
            return {}

    def guard_reply(self, user_text: str, ai_reply: str) -> str:
        """便捷封装：命中则替换为抵抗回应，否则原样返回。"""
        verdict = self.check(user_text, ai_reply)
        if verdict.get("resistance_required") and verdict.get("patched_reply"):
            return str(verdict["patched_reply"])
        return ai_reply


__all__ = ["NonResistanceGate"]
