# CustomerServiceAgent —— 智能客服

给站点 / 平台的客服智能体：**就资料作答 + 客诉自动转人工 + 可接大模型**。
（默认零 LLM 依赖、断网可用、状态落盘到 `~/.pasm-agents/<agent_id>/`，
资料库落在 `~/.pasm-agents/<agent_id>/kb/`）

> **稳定入口**：`from pasm_agents import CustomerServiceAgent`
> **实现**：[`agent.py`](agent.py) ｜ **直接跑** [`quickstart.py`](quickstart.py)

## 和另外三个产品的差别

另外三个（NPC / 老人陪伴 / 学习陪伴）继承基座的 `BaseAgent`，只要 `pasm-skills`。
本产品继承应用框架的 `BaseApplication`（`pasm-framework` 提供）——
因为"客服"的核心是**资料库**，而资料库是框架的 `knowledge_base` 插件。

`pasm-framework` 本身就是 `pasm-agents` 的依赖，所以 `pip install pasm-agents` 装完即可用。

## 能力

| 能力 | 说明 |
|---|---|
| **就资料作答** | 检索资料库，命中就给**带来源**的答复；**查不到如实说不知道，绝不编造** |
| **客诉自动转人工** | 认出四类必须升级的表达（投诉/曝光、法律/监管、安全/伤害、要求赔偿），回复末尾追加转人工提示 |
| **开箱可用** | 首次启动自动灌入 `DEFAULT_FAQ`，**不配任何东西**就能答上来 |
| **资料库按智能体隔离** | 每个 `agent_id` 一个库（`<persist_dir>/kb/`），两个客服不会互相串资料 |
| **可接大模型** | 传 `llm={...}` 启用 `llm_responder`；LLM 挂了自动回落模板，**永远有回应** |
| **状态可机读** | `snapshot()` 输出纯 dict — 档位 / 情绪 / 交互数 / 资料库规模 / 累计客诉 |

## 最小用法

```python
from pasm_agents import CustomerServiceAgent

cs = CustomerServiceAgent(agent_id="shop-cs", persona={
    "name": "小智", "role": "售后客服",
    "tone": "温暖、专业、耐心",
    "hotline": "400-000-0000",
})

print(cs.answer("怎么退货？"))          # 就资料作答（带来源）
cs.ingest_faq([{                        # 换成自己的业务知识
    "title": "会员日优惠",
    "content": "每月 8 日会员日，黄金会员全场额外 9 折。",
    "source": "faq", "tags": ["会员", "优惠"],
}])
print(cs.answer("会员日有什么优惠？"))

print(cs.needs_escalation("我要投诉你们"))   # -> '投诉/曝光'
print(cs.answer("我要投诉你们"))              # 回复末尾自动追加转人工提示
cs.save()
```

## API

| 方法 | 作用 |
|---|---|
| `answer(text, session_id=..., user_id=...)` | **主入口**：回答一个问题；命中客诉判据时追加转人工提示 |
| `ingest_faq(items)` | 把 FAQ / 产品文档喂进资料库（`ingest` 的别名，会落盘） |
| `needs_escalation(text)` | 这句该不该转人工？返回原因标签或 `None` |
| `escalate(text, ...)` | 记录一次客诉，返回升级上下文（交给你的通知渠道） |
| `kb_stats()` | 资料库规模 `{total, docs, qa}`；未启用资料库时返回 `None` |
| `snapshot()` | 可机读状态快照 |
| `handle(text, ...)` | 框架原始入口（不带客诉提示），需要自己编排时用 |
| `serve(host, port)` | 启动 HTTP 网关（**须**构造时传 `enable_gateway=True`） |

## persona 字段

| 字段 | 说明 |
|---|---|
| `name` / `role` | 客服称呼与角色 |
| `tone` | 语气描述 |
| `hotline` | 客服热线（会被转人工提示与"没查到"回复引用） |
| `temper` / `energy` / `play` | 情绪与行为权重（同其他产品） |

## 两类判据的分界（这是产品可信度的关键）

**答得上 vs 答不上** —— `_render_reply` 只认 `knowledge_facts()`（带 `source` 的知识）：

```python
cs.answer("怎么退货？")        # -> 关于您的问题，我们查到相关说明：签收后 7 天内…（资料来源：faq）
cs.answer("你们能送到火星吗？")  # -> 抱歉，我暂时没有查到关于这个问题的资料，已记录您的问题。
```

引擎的对话记忆**不带 `source`**，所以"用户上一轮自己说的话"不会被当资料答回去
（这是框架专门用 `knowledge_facts()` 拦住的翻车现场）。

**升级 vs 不升级** —— 词表只收**明确指向该场景**的说法：

```python
cs.needs_escalation("我要投诉你们，再不处理就曝光！")  # -> '投诉/曝光'
cs.needs_escalation("这个功能真难用啊")               # -> None（普通抱怨，不升级）
cs.needs_escalation("这个成分会让我过敏吗")           # -> None（这是提问，不是伤害报告）
cs.needs_escalation("我过敏了")                      # -> '安全/伤害'
```

判不出来就放行（**无法判定 = 不升级**），绝不硬猜。

## 已知短板（如实说明）

1. **没有对话式澄清**：用户问得太含糊时它只会照资料答或说查不到，不会反问"您指的是哪笔订单"。
2. **转人工只是"标记"**：它把客诉写进记忆并返回上下文，**真正通知人工**要靠你接通知渠道
   （`escalate()` 的返回值就是交给你的）。
3. **资料库检索是字面匹配 + 倒排索引**，不是向量检索：换个说法（"我不想留着这个了" vs "我要退货"）可能命中不到。

## 相关

- 技能包（平台上发布的那份）：`skill/SKILL.customer-service.body.md`
- 实现细节：[`agent.py`](agent.py)
- 底座：应用框架 `pasm-framework` 的 `BaseApplication`（资料库 / 会话 / 安全 / 温度插件）
- 完整生产系统（DB→KB 增量同步 / 真 MCP 服务 / Web 壳 / Studio 场景一键加载）：仓外独立包 `pasm-customer-service`
