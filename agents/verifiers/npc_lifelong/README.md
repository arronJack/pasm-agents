# NpcLifelongAgent —— 90 天 × 270 段经历下的记忆保持与行为多样性

**行为层验证智能体** · CLI 名 `npc-lifelong`

> **实现**：[`agent.py`](agent.py) ｜ **跑一下** [`run.py`](run.py)
>
> ```bash
> python agents/verifiers/npc_lifelong/run.py
> # 等价于：python -m pasm_skills run npc-lifelong
> ```

## 它查什么

| 查什么 | 判据 |
|---|---|
| 里程碑记忆留没留住 | 第 1 天埋的 `salience=5` 事件在 90 天后还能检索到 |
| 同分检索会不会崩 | 60 条同分记忆下 `recall_layers` 不抛异常 |
| 情绪会不会漂 | 情绪值始终有界、单步跳变不超过阈值、跨度足够（不是一条直线） |
| 行为会不会僵化 | 动作分布熵 ≥ 0.65；尾部动作仍有概率；被夸/被凶后分布**真的变化** |
| 人格会不会饱和 | 人格三维不长期贴在 ±1 |

## 跑出来是什么样

19 项，约 7 秒。**首轮就压出一个必然崩溃的核心 bug**：同分排序时元组退化到比较 `dict`，60 条同分必现 `TypeError`。

## 怎么读结论

`[OK]` 通过 · `[WARN]` 值得看一眼 · `[FAIL]` 必须处理 · `[SKIP]` 条件不足跳过。

- `[WARN]` **不等于失败**，很多是真实的产品能力短板，要做的是**产品决策**。
- `[SKIP]` 一定要读 detail：它说「这次没查成」，不是「查了没问题」。
- 结论里的 `[仿生层 torch]` / `[轻量档]` 标注说明用哪一档跑的，**两档不能混着比**。

## 配套的成品智能体

[`../../product/npc/`](../../product/npc/) —— 它检修的就是这个智能体。

## 相关

- 分组索引：[`../README.md`](../README.md)
- 技能包：`skill/SKILL.verify.body.md`（平台上叫 `pasm-longterm-verify`）
- 阈值表写法与写新验证智能体：[基座 `pasm-skills`](https://github.com/arronJack/pasm-skills/blob/master/docs/BUILD-AGENT.md)
