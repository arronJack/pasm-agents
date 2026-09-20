"""游戏 NPC 产品智能体。

设定一个角色 + 性格，让它能：

- **记住** 玩家的名字、来过几次、做过什么（持久化）
- **回应** 玩家的对话（基于 persona + 检索 + 情绪，纯模板渲染）
- **做出** 当前阶段解锁的动作（动作池随 ``growth_stage`` 升级）
- **被反馈** 调整行为（夸/戳/训都会改变动作权重）

快速开始：

.. code-block:: python

    from pasm_agents import NpcAgent

    npc = NpcAgent(agent_id="herbalist", persona={
        "name": "陈伯", "role": "河边摆摊的草药老头",
        "temper": 0.55, "energy": 0.40, "play": 0.30,
        "tone": "慢悠悠、爱讲道理、说话带点草药味",
    })
    npc.observe("玩家来买跌打药", salience=3, tags=["玩家"])
    print(npc.act())                 # 'wave'
    print(npc.chat("有跌打药吗"))     # '陈伯笑呵呵……'
    npc.feedback("praise", action="talk")
    npc.save()
"""

from __future__ import annotations

import random
from typing import Any, Dict, List

from pasm_skills.sdk import BaseAgent


# 动作池随成长阶段解锁 —— 与 pet_behavior.ARCH_META 的阶段思路对齐
# 0: wave / hop / peek
# 1: + ball
# 2: + dance / spin
# 3: + think
NPC_ACTIONS: Dict[int, List[str]] = {
    0: ["wave", "hop", "peek", "talk"],
    1: ["wave", "hop", "peek", "talk", "ball"],
    2: ["wave", "hop", "peek", "talk", "ball", "dance", "spin"],
    3: ["wave", "hop", "peek", "talk", "ball", "dance", "spin", "think"],
}


NPC_PERSONA_TEMPLATE: Dict[str, Any] = {
    "name": "未命名 NPC",
    "role": "村民",
    "temper": 0.5,   # 主动性
    "energy": 0.5,   # 活跃度
    "play":   0.5,   # 俏皮度
    "tone":   "平和",
    # 自称（可选）。**留空 = 用中性「我」**。
    # 老派角色可以写 "老夫" / "老朽" / "本座"；但绝不能把它写成默认值 ——
    # 那样「卖花的小姑娘」也会说"老朽还记着呢"（人设泄漏，见 selftest_npc）。
    "self_ref": "",
}


#: 「在问 NPC 是谁」的触发词。**必须专指问身份，别放光杆「名字」进去** ——
#: 「我名字叫张三 / 这花有名字吗 / 我给你起个名字吧」都不是在问 NPC 是谁，
#: 而光杆「名字」会把它们全部误判成自我介绍（2026-09-15 探针实测 4/4 误触发）。
_IDENTITY_QUERIES: tuple = (
    "你叫什么", "你叫啥", "你叫甚", "你是谁", "你是哪位", "你是什么人",
    "你的名字", "怎么称呼", "如何称呼",
)

#: 带这些标签的记忆**不是**"我和玩家共同的经历"，不该被当作"上次那件事"回显。
#: 「自我介绍」由 :meth:`NpcAgent.bootstrap_event` 写入。
_NOT_SHARED_TAGS: tuple = ("自我介绍",)

#: 标题带这些前缀的记忆同样不算共同经历 ——
#: 「对话：」是 :meth:`BaseAgent.chat` 把**玩家刚说的话**自动入库的，
#: 把两秒前的问话当"上次那件事"念回去，读起来是错位的。
_NOT_SHARED_TITLE_PREFIXES: tuple = ("对话：",)

#: 里程碑标记词：带这些标签之一的记忆，才配说"上次……我还记着呢"。
#: 也用作「回忆探询」的兜底检索探针 —— **两处必须同源**，否则会悄悄走偏。
_MILESTONE_TAGS: tuple = ("玩家", "救命", "重大")

#: 「回忆探询」：玩家在问"你还记得吗 / 你还记得什么"。
#: 这类问句里**没有可检索的内容词**，按字面检索常常一条都召不回 ——
#: 引擎分词对长句会截断候选词（4 字优先、只留前 10 个），
#: 于是「还记得河边那次吗」比「河边那次」更容易**一条都召不回**：
#: 玩家说得越自然，NPC 反而越"记不住"（真实用户会遇到的失败模式，
#: 见 selftest_npc 的第 3/4/6 项）。
_RECALL_QUERIES: tuple = (
    "还记得", "记不记得", "记得吗", "记得么", "记得没",
    "记得什么", "记得哪些", "记得谁", "记得啥",
)


def _is_shared_memory(f: Dict[str, Any]) -> bool:
    """这条记忆算不算"我和玩家共同的经历"（决定要不要说"上次……我还记着呢"）。

    ``recall()`` 返回的 fact **不含 category 字段**，所以只能看 tags 与标题前缀。
    """
    tags = f.get("tags") or []
    if any(t in tags for t in _NOT_SHARED_TAGS):
        return False
    return not str(f.get("title") or "").startswith(_NOT_SHARED_TITLE_PREFIXES)


class NpcAgent(BaseAgent):
    """可装载的游戏 NPC。

    persona 必填项：``name``、``role``。其余有合理默认值。
    """

    def __init__(self, agent_id: str, persona: Dict[str, Any], **kw):
        # 用模板补齐缺失键
        merged = dict(NPC_PERSONA_TEMPLATE)
        merged.update(persona or {})
        super().__init__(agent_id=agent_id, persona=merged, **kw)

    # ------- 检索 ---------------------------------------------------

    def recall(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """检索记忆（含「回忆探询」兜底）。

        为什么要覆盖
        ------------
        玩家最自然的问法恰恰最难召回到东西：「还记得河边那次吗」比「河边那次」
        更容易**一条都召不回**。根因在引擎的分词——它按 4 字→3 字→2 字的顺序
        生成候选 n-gram 后**只保留前 10 个**，长句里真正能对上记忆的短词
        （「河边」）会在截断中被丢掉。结果是**玩家说得越客气越完整，NPC 越像失忆**。

        策略：先按原句检索；只有当**召回为空**、且这句话确实是在问
        "你还记得吗"时，才用共同经历的标记词（:data:`_MILESTONE_TAGS`）再探一次。
        纯追加——原有能召回的场景行为完全不变，不会引入新的误召回。
        """
        hits = super().recall(query, k=k)
        if hits:
            return hits
        q = query or ""
        if not any(t in q for t in _RECALL_QUERIES):
            return hits
        return super().recall(" ".join(_MILESTONE_TAGS), k=k)

    # ------- 阶段 / 动作 --------------------------------------------

    def action_pool(self) -> List[str]:
        stage = self.state.growth_stage
        # 不超过表里最大的阶段
        stage = min(stage, max(NPC_ACTIONS))
        return list(NPC_ACTIONS.get(stage, NPC_ACTIONS[0]))

    def grow(self) -> int:
        """升级一档（按交互数自动触发也可手动调）。"""
        if self.state.growth_stage < max(NPC_ACTIONS):
            self.state.growth_stage += 1
        return self.state.growth_stage

    # ------- 引导 ---------------------------------------------------

    def bootstrap_event(self) -> List[Dict[str, Any]]:
        p = self.persona
        return [{
            "title": f"我{'' if p['role'].startswith('是') else '是'}{p['role']}",
            "brief": f"我叫{p['name']}，{p.get('tone','')}。",
            "tags": ["我", p["name"], p["role"], "自我介绍"],
            "salience": 3,
            "category": "自我",
        }]

    # ------- 聊天渲染 ----------------------------------------------

    def _render_reply(
        self,
        text: str,
        facts: List[Dict[str, Any]],
        mood: float,
    ) -> str:
        p = self.persona
        name = p["name"]
        role = p["role"]
        # 自称由 persona 决定；留空用中性「我」
        self_ref = p.get("self_ref") or "我"

        # 命中了"在问我是谁" → 介绍自己
        if any(k in text for k in _IDENTITY_QUERIES):
            return f"{name}道：{role}，{p.get('tone','')}。"

        # 命中了"第一次遇见玩家"这类里程碑 → 表达记得
        for f in facts:
            if not _is_shared_memory(f):
                continue
            if f.get("sal", 0) >= 4 and any(
                t in (f.get("tags") or []) for t in _MILESTONE_TAGS
            ):
                brief = (f.get("brief") or f.get("title") or "").strip()
                if brief:
                    return f"{name}眯起眼：上次{ brief[:16] }，{self_ref}还记着呢。"

        # 命中任何**共同经历** → 提及
        for f in facts:
            if not _is_shared_memory(f):
                continue
            brief = (f.get("brief") or f.get("title") or "").strip()
            if brief:
                return f"{name}点头道：{ brief[:24] }，记得。"

        # 情绪温度调节
        if mood > 0.4:
            lead = random.choice([f"{name}笑呵呵", f"{name}热情招呼", f"{name}迎上来"])
        elif mood < -0.3:
            lead = random.choice([f"{name}皱眉", f"{name}没好气地", f"{name}冷冷"])
        else:
            lead = random.choice([f"{name}应声", f"{name}抬头看", f"{name}慢悠悠答"])

        # 兜底句
        defaults = [
            # 用 self_ref 而不是 role：`……这事{role}我也说不准` 会读成
            # 「这事卖花的小姑娘我也说不准」，句子是拧的。
            f"……这事{self_ref}也说不准。",
            f"你问这个啊，让我想想……",
            f"（摆摆手）下次再说吧。",
        ]
        return f"{lead}：" + random.choice(defaults)