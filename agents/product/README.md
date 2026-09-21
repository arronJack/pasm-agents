# 成品智能体（product/）

拿去就能用的四个智能体。默认零 LLM 依赖、断网可用、状态落盘到 `~/.pasm-agents/<agent_id>/`。

| 智能体 | 给谁用 | 主类 | 一句话 |
|---|---|---|---|
| [`npc`](npc/) | 游戏 | `NpcAgent` | 记住玩家做过什么；同一句话在不同情绪下说法不同；被夸的动作做得多 |
| [`companion`](companion/) | 独居老人 | `ElderlyCompanion` | 关键事实（用药/过敏/家人/本人）**按标签直查**；用药提醒；危机升级 |
| [`tutor`](tutor/) | 学生 | `LearningTutor` | 每个知识点一个掌握度；最弱优先出题；学情可机读导出 |
| [`customer_service`](customer_service/) | 站点/平台客服 | `CustomerServiceAgent` | 就资料作答（查不到如实说不知道）；客诉自动转人工；可接大模型 |

## 共同的底座

NPC / 老人陪伴 / 学习陪伴都继承基座的 `BaseAgent`（`pasm_skills.sdk.BaseAgent`）——
记忆读写、情绪、动作选择、反馈、持久化都在那里；
每个智能体只定自己的 **persona / 动作池 / 回复模板**。

**智能客服是唯一的例外**：它继承应用框架的 `BaseApplication`
（`pasm_framework.BaseApplication`）—— 因为"客服"的核心能力是**资料库**，
而资料库是框架的 `knowledge_base` 插件，不是基座 SDK 里有的东西。
`pasm-framework` 本来就是本包的依赖，所以 `pip install pasm-agents` 装完即可用。

```python
from pasm_agents import NpcAgent        # 四个类都从同一个包出
```

> ⚠️ 智能客服的那几个名字（`CustomerServiceAgent` 等）是**按需导入**的：
> 只装了基座 `pasm-skills` 的环境里，`import pasm_agents` 与另外三个产品照常可用
> （降级 `light` 档），只有真的去拿客服智能体时才会要求框架存在。

## 档位（每个智能体都会如实申报）

| tier | 含义 | 怎么达到 |
|---|---|---|
| `bionic` | 完整 PASM 核心 + 真实情绪模块 | 解释器里有 torch |
| `core` | PASM 核心（记忆 + 学习，无情绪模块） | 核心仓在路径上 |
| `light` | 纯内置实现（重要度淘汰 + 字面检索 + softmax 权重） | 任何机器，默认 |

`agent.tier` 与落盘 JSON、`summary()` 都带这个字段，**不会偷偷降级**。
