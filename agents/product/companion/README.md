# ElderlyCompanion —— 老人陪伴

给独居老人做陪伴：**关键事实永不丢、用药按时提醒、危机自动升级到家人**。
（零 LLM 依赖、断网可用、状态落盘到 `~/.pasm-agents/<agent_id>/`）

> **稳定入口**：`from pasm_agents import ElderlyCompanion`
> **实现**：[`agent.py`](agent.py) ｜ **直接跑** [`quickstart.py`](quickstart.py)

## 能力

| 能力 | 说明 |
|---|---|
| **关键事实永不丢** | 用药 / 过敏 / 家人 / 本人信息单独存一层、**按标签直查**（命中率 100%），不会被日常闲聊挤掉 |
| **用药提醒** | 按 `medication_schedule` 的钟点判断该不该提醒，返回「还没吃的药」 |
| **危机升级** | 识别胸闷 / 摔倒 / 意识异常 / 轻生念头等表达，生成含紧急联系人与现场快照的升级信息 |
| **陪伴对话** | 情绪 + 记忆渲染的回应，语气跟着老人当天状态走 |

## 最小用法

```python
from pasm_agents import ElderlyCompanion

elder = ElderlyCompanion(agent_id="chenxiulan", persona={
    "name": "陈秀兰", "age": 78, "tone": "慢、温和",
    "key_facts": [
        {"label": "用药", "content": "每天早 8 点吃降压药络活喜 5mg"},
        {"label": "过敏", "content": "青霉素过敏"},
        {"label": "家人", "content": "女儿在深圳，每周日来电话"},
        {"label": "本人", "content": "78 岁，独居"},
    ],
    "emergency_contact": {"name": "女儿小敏", "phone": "13900000000"},
    "medication_schedule": [{"name": "络活喜", "dose": "5mg", "hour": 8}],
})
print(elder.chat("我吃什么药"))                      # 命中关键事实（直查，不靠运气）
print(elder.detect_crisis("我胸口有点闷，喘不上气"))   # ['胸闷', ...]
print(elder.due_medication(now_hour=8))              # 该提醒的药
elder.observe("今天邻居来串门，聊了一个多小时")
print(elder.chat("今天有人来吗"))
elder.save()
```

## API

| 方法 | 作用 |
|---|---|
| `chat(text)` | 说一句话。老人问「我吃什么药」会命中关键事实层 |
| `detect_crisis(text)` | 扫一遍危机表达，返回命中的类别列表（空 = 没有） |
| `escalate(reason)` | 生成升级信息（紧急联系人 + 当时快照 + 建议动作） |
| `due_medication(now_hour=)` | 这个点该提醒哪些药 |
| `observe(...)` / `save()` | 同 `BaseAgent` |

## persona 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` / `age` / `tone` | ✅ | 称呼、年龄、语气 |
| `key_facts` | ✅ | `[{"label": "用药", "content": "每天早8点吃降压药络活喜5mg"}, …]`。`label` 是**检索键**，用 用药 / 过敏 / 家人 / 本人 这几个词 |
| `emergency_contact` | ✅ | `{"name": "女儿小敏", "phone": "139…"}` |
| `medication_schedule` | 建议 | `[{"name": "络活喜", "dose": "5mg", "hour": 8}]` |

⚠️ **这不是医疗器械**，也不替代任何医疗或急救服务。它只做「记得住、问得到、异常时提醒到人」；
用药调整、诊断、急救必须由专业人员做出。

## 已知短板（如实说明）

纯口语问句的检索命中率约 **0.5**：底层是**字面匹配** —— 老人说「我叫什么名字」，
而记忆里存的是「姓名」这个标签，就问不到。这是核心的能力短板，不是本类的问题。
把 `key_facts` 的 `label` 写全（含常见口语说法）能显著提高命中率。

## 配套的验证智能体

[`../../verifiers/companion_elderly/`](../../verifiers/companion_elderly/) —— 跑 30 天，把「关键事实按标签直查」判为 **FAIL 级**（命中率必须 100%），把「纯口语跨表述检索」判为 WARN 级 —— 安全和体验分开要求。

## 相关

- 技能包（平台上发布的那份）：`skill/SKILL.companion.body.md`
- 实现细节：[`agent.py`](agent.py)
- 底座：基座 `pasm-skills` 的 `BaseAgent`（<https://github.com/arronJack/pasm-skills/blob/master/docs/TUTORIAL.md>）
