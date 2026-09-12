# StudyTutorAgent —— 30 天学习陪伴的掌握度结构与停练衰减

**行为层验证智能体** · CLI 名 `study-tutor`

> **实现**：[`agent.py`](agent.py) ｜ **跑一下** [`run.py`](run.py)
>
> ```bash
> python agents/verifiers/study_tutor/run.py
> # 等价于：python -m pasm_skills run study-tutor
> ```

## 它查什么

| 查什么 | 判据 |
|---|---|
| 掌握度结构 | 每个知识点有独立数值、在 0~1 内、随表现变化 |
| 自适应选题 | 明显薄弱的知识点应被优先选中 |
| 学情快照可机读 | `snapshot()` 的键齐全、可 JSON 序列化 |
| **停练是否衰减** | 前 5 天练、之后彻底停练的知识点，掌握度应随时间下降 |
| 鼓励式回应 | 「我不会」不能得到打击式回答 |

## 跑出来是什么样

15 项，约 5 秒。当前 1 条 `[WARN]`：**无遗忘曲线** —— 停练 25 天与昨天练的一样强，这是核心的真实产品缺口。

## 怎么读结论

`[OK]` 通过 · `[WARN]` 值得看一眼 · `[FAIL]` 必须处理 · `[SKIP]` 条件不足跳过。

- `[WARN]` **不等于失败**，很多是真实的产品能力短板，要做的是**产品决策**。
- `[SKIP]` 一定要读 detail：它说「这次没查成」，不是「查了没问题」。
- 结论里的 `[仿生层 torch]` / `[轻量档]` 标注说明用哪一档跑的，**两档不能混着比**。

## 配套的成品智能体

[`../../product/tutor/`](../../product/tutor/) —— 它检修的就是这个智能体。

## 相关

- 分组索引：[`../README.md`](../README.md)
- 技能包：`skill/SKILL.verify.body.md`（平台上叫 `pasm-longterm-verify`）
- 阈值表写法与写新验证智能体：[基座 `pasm-skills`](https://github.com/arronJack/pasm-skills/blob/master/docs/BUILD-AGENT.md)
