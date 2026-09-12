# CoreVerifierAgent —— 引擎接口契约、认知层是否落盘、符号推理闭环、环境插件、安全底线、冒烟

**结构层验证智能体** · CLI 名 `core-verifier`

> **实现**：[`agent.py`](agent.py) ｜ **跑一下** [`run.py`](run.py)
>
> ```bash
> python agents/verifiers/core_verifier/run.py
> # 等价于：python -m pasm_skills run core-verifier
> ```

## 它查什么

| 组 | 查什么 |
|---|---|
| 接口契约 | `pasm/engine_api.py` 的六必需签名是否齐、`conforms()` 是否通过 |
| 认知层落盘 | `memory_layers` / `learning` / 符号层等关键模块是否**真的存在于磁盘**（不是只在 import 缓存里） |
| 符号推理闭环 | 符号层能否被真实调用并回传结果 |
| 环境插件 | `envs.py` 的网格 / 非网格环境是否可用 |
| 安全底线 | 自伤 / 危机干预 / 未成年人保护 / 隐私是否落盘 |
| 冒烟 | 基础 import 与最小调用是否通过 |

## 跑出来是什么样

33 项断言，约 25 秒。核心侧当前有 1 条 `[WARN]`：尚无独立的安全底线层（若由应用层承担，需在那侧确认并写入文档）。

## 怎么读结论

`[OK]` 通过 · `[WARN]` 值得看一眼 · `[FAIL]` 必须处理 · `[SKIP]` 条件不足跳过。

- `[WARN]` **不等于失败**，很多是真实的产品能力短板，要做的是**产品决策**。
- `[SKIP]` 一定要读 detail：它说「这次没查成」，不是「查了没问题」。
- 结论里的 `[仿生层 torch]` / `[轻量档]` 标注说明用哪一档跑的，**两档不能混着比**。

## 相关

- 分组索引：[`../README.md`](../README.md)
- 技能包：`skill/SKILL.verify.body.md`（平台上叫 `pasm-longterm-verify`）
- 阈值表写法与写新验证智能体：[基座 `pasm-skills`](https://github.com/arronJack/pasm-skills/blob/master/docs/BUILD-AGENT.md)
