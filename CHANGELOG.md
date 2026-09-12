# Changelog

本项目遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [0.4.0] — 2026-09-12

**本仓从 `pasm-skills` 里拆出来**，成为独立的成品智能体仓。基座（SDK / 框架 / 打包工具 / 脚手架）
留在 `pasm-skills`，本仓只放**具体智能体**。

### 拆仓动机

原来的 `pasm-skills` 既当框架又当成品智能体仓库，定位混了：
打开仓的人分不清"这是给我用的工具"还是"这是给我抄的参考实现"。
现在职责单一 —— **基座提供能力，本仓提供成品**。

### 本仓从 `pasm-skills` 迁入

| 迁入内容 | 原位置 | 现位置 |
|---|---|---|
| 3 个产品智能体 | `pasm_agents/{npc,companion,tutor}.py` | `pasm_agents/` |
| 产品智能体 CLI | `pasm_agents/cli.py` | `pasm_agents/cli.py` |
| **7 个验证智能体** | `pasm_skills/agents/*` | `pasm_agents/verifiers/*` |
| 4 份技能正文 | `skill/SKILL.*.body.md` | `skill/` |
| 事实基线 | `baselines/` | `baselines/` |
| 设计手册 | `docs/AGENTS.md` | `docs/AGENTS.md` |
| 30 秒示例 | `examples/*` | `examples/` |

产品智能体的基类 `BaseAgent` **没有跟过来** —— 它提升为基座的 `pasm_skills.sdk.BaseAgent`。
本仓改为 `from pasm_skills.sdk import BaseAgent`，并声明依赖 `pasm-skills>=0.4.0`。

### 新增 —— 验证智能体自动被基座发现

`pyproject.toml` 里声明：

```toml
[project.entry-points."pasm_skills.agents"]
pasm-verifiers = "pasm_agents.verifiers"
```

于是装上本仓后，**基座不需要改一行代码**：

```bash
pip install pasm-agents
python -m pasm_skills list            # 7 个验证智能体自动出现
python -m pasm_skills run --all
```

（本地开发时也可以 `PASM_SKILLS_PATH` 直接指目录，两种方式都支持。）

### 新增 —— 打包改用基座的打包库

`tools/build_skill.py` 从"自己实现一遍打包规则"改成"声明 4 个技能 + 调用
`pasm_skills.build.run_cli`"。归档规则（含 ZIP 结构自检）集中一处，不再各抄一份。

### 版本号对齐

本仓 `0.4.0` 与基座 `0.4.0` 同步 —— 便于一眼看出"哪个基座配哪套智能体"。

### 验证

- 3 个产品智能体：`pasm-agents demo npc|companion|tutor` 全跑通
- 7 个验证智能体：`python -m pasm_skills run --all` → **103 ok / 8 warn / 0 fail**
- 4 个技能包：`python tools/build_skill.py --zip --clean` 全部通过结构自检

---

> 0.3.0 及更早的历史见基座仓 `pasm-skills` 的 CHANGELOG（这些能力原先在那里开发）。
