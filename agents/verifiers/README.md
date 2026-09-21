# 验证智能体（verifiers/）

**面向开发者**：回答一个问题 ——「认知引擎跑久了，还是好的吗？」

它们不是会聊天的角色，而是**体检工具**：跑完输出 `[OK] / [WARN] / [FAIL] / [SKIP]`，
可以存 JSON、可以接 CI、可以前后对比。零依赖、断网可用、**只读**被检查的仓库。

## 分两层

| 层 | 查什么 | 成员 |
|---|---|---|
| **结构层** | 东西在不在、接线对不对 | `core_verifier` / `parity_guard` / `regression` |
| **行为层** | 跑起来表现对不对 | `npc_lifelong` / `companion_elderly` / `study_tutor` / `soak_longrun` |
| **产品层** | 交付给用户的四个智能体本身好不好（2026-09-16 新增） | `product_verifier` |

**三者不能互相替代**：结构全绿**不能**保证 NPC 记得住玩家 ——
看文件列表永远看不出「情绪会不会漂」；
而**核心全绿也不能保证产品是好的** —— 上面两层查的全是 `pasm.cognitive`，
产品层（`pasm_agents` 的 npc / companion / tutor）长期**没有任何人验**，
这正是本仓自己记在案的已知缺口。`product-verifier` 补上它，且上线当场就抓到
一个真 bug：`ElderlyCompanion.chat()` 在用户自定义 persona 用 `value`/`text`
写关键事实时抛 `KeyError: 'content'`（代码硬取字段名）→ 已修并加了回归断言。

## 怎么跑

```bash
python -m pasm_skills run core-verifier     # 单个
python -m pasm_skills run --all             # 全部（约 1 分钟）
```

每个文件夹里都有一个 `run.py`，可以直接 `python agents/verifiers/<名字>/run.py`，
它会自动把发现路径配好。

## 怎么读结论

- `[WARN]` **不等于失败**。有些 WARN 是**真实的产品能力短板**（例：「停练的知识点不衰减」
  = 学习层没有遗忘曲线）—— 要做的是**产品决策**，不是改验证器把灯弄绿。
- `[SKIP]` 的 detail **一定要读**：它说明「这次没查成」，不是「查了没问题」。
- 结论里的 `[仿生层 torch]` / `[轻量档]` 标注说明这条是用哪一档跑的。**两档结论不能混着比。**

## 它们已经抓到的真问题

`npc_lifelong` 上线首轮就压出一个**必然崩溃**的核心 bug：
`memvec.recall_layers` 在同分记忆排序时元组退化到比较 `dict`，60 条同分必现 `TypeError`。
这类问题静态看代码看不出来，只有真跑 270 段经历才会现形。
