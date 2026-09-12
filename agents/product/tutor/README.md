# LearningTutor —— 学习陪伴

给学生的陪伴式学习助手：**薄弱点定位 + 最弱优先选题 + 鼓励式对话 + 学情可机读导出**。
（零 LLM 依赖、断网可用、状态落盘到 `~/.pasm-agents/<agent_id>/`）

> **稳定入口**：`from pasm_agents import LearningTutor`
> **实现**：[`agent.py`](agent.py) ｜ **直接跑** [`quickstart.py`](quickstart.py)

## 能力

| 能力 | 说明 |
|---|---|
| **掌握度追踪** | 每个知识点一个 0~1 掌握度，用 EMA 平滑，越近的表现权重越高 |
| **最弱优先选题** | `pick_next()` 有 80% 概率挑最薄弱的知识点，20% 随机防「只刷熟题」的假象 |
| **鼓励式对话** | 按当前掌握度与近期表现渲染语气；说「我不会」和说「我会了」给不同反馈 |
| **学情可机读导出** | `snapshot()` 输出纯 dict — 学生 / 各知识点掌握度 / 最弱项 / 平均 / 档位，画像层可直接消费 |

## 最小用法

```python
from pasm_agents import LearningTutor

tutor = LearningTutor(agent_id="xiaoya", persona={
    "name": "小雅", "grade": "五年级",
    "topics": ["分数加减", "面积计算", "行程问题", "鸡兔同笼"],
})
tutor.report("分数加减", 0.4)       # 这次做对了 40%
tutor.report("分数加减", 0.5)
tutor.report("面积计算", 0.9)
print(tutor.pick_next())             # 最该练的那个知识点
print(tutor.chat("分数加减好难"))      # 鼓励式回应，不是打击式
print(tutor.snapshot())              # 可机读学情
tutor.save()
```

## API

| 方法 | 作用 |
|---|---|
| `report(topic, score)` | 报一次表现（`score` 0~1）；内部按 EMA 更新并落盘 |
| `pick_next()` | 下一题该练哪个知识点 |
| `mastery(topic)` | 看某个知识点当前掌握度 |
| `snapshot()` | 学情快照（纯 JSON 可序列化的 dict） |
| `chat(text)` | 说一句话（「好难」/「我会了」/「我哪里不行」有不同回应） |
| `save()` | 落盘 |

## persona 字段

| 字段 | 说明 |
|---|---|
| `name` / `grade` | 学生称呼与年级 |
| `topics` | 知识点列表，例如 `["分数加减", "面积计算", "行程问题"]` |
| `tone` | 语气描述 |

## 学情快照长什么样

```python
t.snapshot()
# {
#   "student": "小雅", "grade": "五年级",
#   "mastery": {"分数加减": 0.12, "面积计算": 0.27, "行程问题": 0.168},
#   "weakest": "图形对称",
#   "average": 0.145,
#   "history_size": 3,
#   "tier": "light"
# }
```

**这个 dict 就是给画像层 / 报表 / 家长端用的** —— 不用解析自然语言。

## 已知短板（如实说明）

学习层**没有遗忘曲线**：停练 25 天的知识点和昨天练的一样强。
长期学情会因此失真（「三个月前会的」看起来还在）。`study_tutor` 验证智能体专门盯着这一项。

## 配套的验证智能体

[`../../verifiers/study_tutor/`](../../verifiers/study_tutor/) —— 跑 30 天 × 6 个知识点，断言掌握度结构、自适应选题与停练衰减 —— 它压出的「无遗忘曲线」是核心的真实产品缺口。

## 相关

- 技能包（平台上发布的那份）：`skill/SKILL.tutor.body.md`
- 实现细节：[`agent.py`](agent.py)
- 底座：基座 `pasm-skills` 的 `BaseAgent`（<https://github.com/arronJack/pasm-skills/blob/master/docs/TUTORIAL.md>）
