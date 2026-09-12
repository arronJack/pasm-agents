# SoakLongrunAgent —— 6000 步认知 + 6000 步行为 + 记忆洪峰

**行为层验证智能体** · CLI 名 `soak-longrun`

> **实现**：[`agent.py`](agent.py) ｜ **跑一下** [`run.py`](run.py)
>
> ```bash
> python agents/verifiers/soak_longrun/run.py
> # 等价于：python -m pasm_skills run soak-longrun
> ```

## 它查什么

| 查什么 | 判据 |
|---|---|
| 性能是否衰减 | 末段耗时 / 首段耗时 不超过阈值（长跑不该越跑越慢） |
| 行为多样性 | 6000 步后动作分布熵仍高（没有坍缩到一两个动作） |
| **人格是否饱和钉死** | 人格不能被一路推到 ±1 卡住 —— 那是几千步才发作的问题，短测看不见 |
| 状态可复现 | 同样输入下落盘状态一致 |
| 记忆洪峰 | 容量触顶后系统仍稳定（不崩、不无限增长） |

## 跑出来是什么样

15 项，约 15 秒。当前 2 条 `[WARN]`：轻量档与仿生档的人格都会被推到 ±1 并卡死，此后不可塑。

## 怎么读结论

`[OK]` 通过 · `[WARN]` 值得看一眼 · `[FAIL]` 必须处理 · `[SKIP]` 条件不足跳过。

- `[WARN]` **不等于失败**，很多是真实的产品能力短板，要做的是**产品决策**。
- `[SKIP]` 一定要读 detail：它说「这次没查成」，不是「查了没问题」。
- 结论里的 `[仿生层 torch]` / `[轻量档]` 标注说明用哪一档跑的，**两档不能混着比**。

## 相关

- 分组索引：[`../README.md`](../README.md)
- 技能包：`skill/SKILL.verify.body.md`（平台上叫 `pasm-longterm-verify`）
- 阈值表写法与写新验证智能体：[基座 `pasm-skills`](https://github.com/arronJack/pasm-skills/blob/master/docs/BUILD-AGENT.md)
