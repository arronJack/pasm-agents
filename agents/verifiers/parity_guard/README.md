# ParityGuardAgent —— 核心仓 ↔ Studio 镜像仓的同名文件是否逐字一致（防两仓分叉）

**结构层验证智能体** · CLI 名 `parity-guard`

> **实现**：[`agent.py`](agent.py) ｜ **跑一下** [`run.py`](run.py)
>
> ```bash
> python agents/verifiers/parity_guard/run.py
> # 等价于：python -m pasm_skills run parity-guard
> ```

## 它查什么

| 查什么 |
|---|
| 两仓同名文件逐个比对，**行尾差异（CRLF/LF）忽略** |
| 不一致就报具体文件名 + 差异摘要 |

它守的是一个真实风险：`E:/AI/PASM`（核心）与 `E:/AI/pasm_qclaw`（Studio）**推同一个远端**，
历史上分叉过。改了一边忘了另一边，症状要等很久才暴露。

## 跑出来是什么样

2 项，**不到 1 秒**。适合放进每次提交前的钩子。

## 怎么读结论

`[OK]` 通过 · `[WARN]` 值得看一眼 · `[FAIL]` 必须处理 · `[SKIP]` 条件不足跳过。

- `[WARN]` **不等于失败**，很多是真实的产品能力短板，要做的是**产品决策**。
- `[SKIP]` 一定要读 detail：它说「这次没查成」，不是「查了没问题」。
- 结论里的 `[仿生层 torch]` / `[轻量档]` 标注说明用哪一档跑的，**两档不能混着比**。

## 相关

- 分组索引：[`../README.md`](../README.md)
- 技能包：`skill/SKILL.verify.body.md`（平台上叫 `pasm-longterm-verify`）
- 阈值表写法与写新验证智能体：[基座 `pasm-skills`](https://github.com/arronJack/pasm-skills/blob/master/docs/BUILD-AGENT.md)
