"""PASM 产品智能体：以 PASM 引擎为基座的可装载、可记忆、可对话的智能体。

包内四个开箱即用的产品：

- :class:`NpcAgent`            游戏 NPC（河边草药老头、市集算命师、酒馆老板娘……）
- :class:`ElderlyCompanion`    老人陪伴（用药提醒、危机升级、关键事实记忆）
- :class:`LearningTutor`       学习陪伴（薄弱点定位、巩固计划、进度跟踪）
- :class:`CustomerServiceAgent` 智能客服（就资料作答、客诉转人工、可接大模型）

前三个基于基座的 :class:`BaseAgent` 实现，差异只在 persona、行为池和聊天模板。
第四个（智能客服）建在应用框架 ``pasm_framework.BaseApplication`` 上 ——
因为"客服"的核心能力是**资料库**，而资料库是框架的 ``knowledge_base`` 插件，
不是基座 SDK 里有的东西（``pasm-framework`` 本来就是本包的依赖）。

快速上手：

.. code-block:: python

    from pasm_agents import NpcAgent

    npc = NpcAgent(agent_id="herbalist", persona={
        "name": "陈伯",
        "role": "河边摆摊的草药老头",
        "temper": 0.55, "energy": 0.40, "play": 0.30,
    })
    npc.observe("玩家来买药", salience=3)
    print(npc.act())         # -> "wave" / "talk" / "peek" 等
    print(npc.chat("有跌打药吗"))
    npc.save()

数据落盘位置：``~/.pasm-agents/<agent_id>/``。Agent 可被反复加载、上次的状态/记忆自动恢复。
"""

from pasm_skills.sdk import (  # 基座仓提供
    BaseAgent, AgentState, _now, _core_available, _torch_available,
)
from .npc import NpcAgent, NPC_ACTIONS, NPC_PERSONA_TEMPLATE
from .companion import (
    ElderlyCompanion, CRISIS_KEYWORDS, LABEL_ALIASES, register_label_aliases,
)
from .tutor import LearningTutor

__version__ = "0.5.0"
__all__ = [
    "BaseAgent", "AgentState", "NpcAgent", "ElderlyCompanion", "LearningTutor",
    "CustomerServiceAgent",
    "NPC_ACTIONS", "NPC_PERSONA_TEMPLATE", "CRISIS_KEYWORDS", "LABEL_ALIASES",
    "DEFAULT_FAQ", "ESCALATION_RULES", "detect_escalation",
    "register_label_aliases",
    "_core_available", "_torch_available",
]

#: 智能客服（第 4 个产品）导出的名字 —— 由下面的 ``__getattr__`` **按需**导入。
_CS_EXPORTS = frozenset({
    "CustomerServiceAgent", "DEFAULT_FAQ", "ESCALATION_RULES", "detect_escalation",
})


def __getattr__(name: str):
    """按需导入智能客服（PEP 562），而不是在包顶部 import。

    为什么必须这样：``CustomerServiceAgent`` 建在应用框架 ``pasm_framework`` 上，
    而本包另外三个产品只需要基座 ``pasm_skills`` **就能跑**（缺引擎时降级到
    ``light`` 档，这是本包明确承诺的行为）。
    顶部 eager import 会让"只装了基座"的环境连 ``import pasm_agents``
    都直接 ``ModuleNotFoundError`` —— 那等于用一个新产品废掉了既有的降级路径。
    """
    if name in _CS_EXPORTS:
        try:
            from . import customer_service as _cs
        except ModuleNotFoundError as ex:
            if "pasm_framework" in str(ex):
                raise ImportError(
                    "CustomerServiceAgent 需要应用框架：pip install pasm-framework"
                    "（本包已把它列为依赖；源码方式运行时把它所在目录加进 PYTHONPATH）"
                ) from ex
            raise
        return getattr(_cs, name)
    raise AttributeError("module %r has no attribute %r" % (__name__, name))


def __dir__():
    return sorted(list(globals()) + list(_CS_EXPORTS))

#: 验证智能体在 `pasm_agents.verifiers` 子包里 —— **故意不在这里 import**。
#: 它们要读 PASM 核心仓，装在本仓的人多数只想用产品智能体，不该为此付出导入开销。
#: 基座通过 entry point（组名 `pasm_skills.agents`）按需加载。
VERIFIERS_SUBPACKAGE = "pasm_agents.verifiers"