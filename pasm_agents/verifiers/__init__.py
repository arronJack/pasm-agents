"""内置智能体集合。

导入本包即完成注册（`agent.register` 装饰器在导入时生效）。
新增智能体：在本目录放一个 `.py`，用 `@register` 装饰类，然后在下面 import 一次。
"""
from __future__ import annotations

from . import core_verifier, parity_guard, regression    # noqa: F401
# 领域智能体：把"长期验证"从结构层推进到行为层
from . import npc_lifelong, companion_elderly, study_tutor, soak_longrun   # noqa: F401
# v0.30.8 产品层体检：以上全部只体检 pasm.cognitive（核心认知层），
# **产品层本身（npc/companion/tutor 的公开 API 与真实行为）长期没人验** ——
# 这正是本仓自己记在案的已知缺口。核心全绿不代表产品是好的。
from . import product_verifier                          # noqa: F401

__all__ = ["core_verifier", "parity_guard", "regression",
           "npc_lifelong", "companion_elderly", "study_tutor", "soak_longrun",
           "product_verifier"]
