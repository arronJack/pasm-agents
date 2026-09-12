# RegressionAgent —— 对事实基线（文件指纹 / 引擎清单 / 契约版本）逐项比对，抓静默退化

**结构层验证智能体** · CLI 名 `regression`

> **实现**：[`agent.py`](agent.py) ｜ **跑一下** [`run.py`](run.py)
>
> ```bash
> python agents/verifiers/regression/run.py
> # 等价于：python -m pasm_skills run regression
> ```

## 它查什么

| 查什么 |
|---|
| 认知层文件的**内容指纹**（哈希按行尾归一化后计算） |
| 引擎清单（`engine_api.available()` 的结果） |
| 契约版本号 |
| **解释器档位**（Python 版本 + torch 有无） |

> **档位必须一起比**：PASM-Lite 的具体引擎要 `import pasm_lite`（依赖 torch）才注册，
> 换个解释器清单就从 `['pasm','pasm-light']` 变成 `[]` —— 早期版本把这误报成
> `[FAIL] 能力消失`。现在档位不同会降级为 `[WARN] 档位不同·不可比`。
> **一个总报假红的验证器，比没有验证器更糟。**

## 跑出来是什么样

9 项，约 8 秒。基线文件在 `baselines/core.json`（要入库，供前后对比）。

## 怎么读结论

`[OK]` 通过 · `[WARN]` 值得看一眼 · `[FAIL]` 必须处理 · `[SKIP]` 条件不足跳过。

- `[WARN]` **不等于失败**，很多是真实的产品能力短板，要做的是**产品决策**。
- `[SKIP]` 一定要读 detail：它说「这次没查成」，不是「查了没问题」。
- 结论里的 `[仿生层 torch]` / `[轻量档]` 标注说明用哪一档跑的，**两档不能混着比**。

## 相关

- 分组索引：[`../README.md`](../README.md)
- 技能包：`skill/SKILL.verify.body.md`（平台上叫 `pasm-longterm-verify`）
- 阈值表写法与写新验证智能体：[基座 `pasm-skills`](https://github.com/arronJack/pasm-skills/blob/master/docs/BUILD-AGENT.md)
