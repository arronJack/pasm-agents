# NpcAgent —— 游戏 NPC

给游戏装一个**有记忆、有情绪、会被玩家反馈塑形**的 NPC。
（零 LLM 依赖、断网可用、状态落盘到 `~/.pasm-agents/<agent_id>/`）

> **稳定入口**：`from pasm_agents import NpcAgent`
> **实现**：[`agent.py`](agent.py) ｜ **直接跑** [`quickstart.py`](quickstart.py)

## 能力

| 能力 | 说明 |
|---|---|
| **记忆** | 玩家做过的事逐条入库；重要度 `salience` 分 1/3/5，容量触顶时按「重要度 + 新旧」淘汰 —— 里程碑（"玩家救了我一命"）不会被日常琐事挤掉 |
| **情绪** | 有随事件变化的情绪值（`mood`，是**属性**不加括号）；同一句话在高兴和生气时说出来的不一样 |
| **动作** | 从动作池里选一个执行，动作池随成长阶段解锁；被夸的动作做得多，被凶的做得少 |
| **持久化** | 落盘到 `~/.pasm-agents/<agent_id>/`，跨进程自动恢复上次状态 |

## 最小用法

```python
from pasm_agents import NpcAgent

npc = NpcAgent(agent_id="herbalist", persona={
    "name": "陈伯", "role": "河边摆摊的草药老头",
    "temper": 0.55, "energy": 0.40, "play": 0.30,
    "tone": "慢悠悠、爱讲道理",
})
npc.observe("玩家第一次来买跌打药", tags=["玩家", "买药"], salience=4, category="日常")
print(npc.act())                        # 'talk' / 'wave' / 'peek' / ...
print(npc.chat("有跌打药吗"))            # 召回相关记忆
print(npc.mood)                         # 情绪值（属性，不加括号）
npc.feedback("praise", action="talk")   # 明确夸 "talk" 这个动作
npc.save()
```

## API

| 方法 | 作用 |
|---|---|
| `observe(title, brief="", tags=None, *, salience=1, category="日常")` | 记一件事。`salience`：1 日常 / 3 值得记 / 5 里程碑 |
| `chat(text)` | 说一句话（内部自动召回相关记忆来渲染语气） |
| `act()` | 从当前动作池挑一个执行，返回动作名 |
| `feedback(kind, action=)` | 给反馈。`kind` = `praise` / `poke` / `scold` / `hug`；**一定要带 `action=`** |
| `feel(event, valence)` | 手动注入一次情绪事件（-1 ~ +1） |
| `mood` | 当前情绪值（**属性**，不是方法） |
| `recall(query, k=5)` | 手动检索记忆 |
| `grow()` | 升一个成长阶段 |
| `save()` | 落盘（`act` / `chat` 也会自动存） |

## persona 字段

| 字段 | 含义 | 高 → 偏向 | 低 → 偏向 |
|---|---|---|---|
| `temper` | 脾气 | 主动搭话、反应大 | 沉默、旁观 |
| `energy` | 精力 | 走动、干活 | 休息、打盹 |
| `play` | 玩心 | 蹦跳、逗趣 | 正经、务实 |

再加 `tone`（语气描述，写进回复模板）与 `role`（身份，用于自我介绍）。

## 动作池随成长阶段解锁

| 阶段 | 动作 |
|---|---|
| 0（初始） | `wave` `hop` `peek` `talk` |
| 1 | + `ball` |
| 2 | + `dance` `spin` |
| 3 | + `think` |

改动作池要同时改两处：本类的 `action_pool()` 与 `NPC_ACTIONS`（阶段表）。

## 配套的验证智能体

[`../../verifiers/npc_lifelong/`](../../verifiers/npc_lifelong/) —— 跑 90 天 / 270 段经历，断言核心能否正确记忆、里程碑会不会被挤掉、情绪会不会漂、行为会不会僵化。

## 相关

- 技能包（平台上发布的那份）：`skill/SKILL.npc.body.md`
- 实现细节：[`agent.py`](agent.py)
- 底座：基座 `pasm-skills` 的 `BaseAgent`（<https://github.com/arronJack/pasm-skills/blob/master/docs/TUTORIAL.md>）
