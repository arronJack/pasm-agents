# Changelog

本项目遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [0.4.1] — 2026-09-12

### 修复 —— 拆仓后**四份技能正文全部失准**（会直接影响已发布的技能）

0.4.0 拆仓时改了代码与包结构，**但正文里的操作指引没跟着改**。正文是给智能体读的说明书，
里面写着"装什么、clone 哪个仓、跑什么命令" —— 拆仓后它们全错了：

| 正文里的原话 | 拆仓后的事实 |
|---|---|
| `git clone .../pasm-skills` + `cd pasm-skills` + `pip install -e .` | 智能体在 `pasm-agents`，基座仓里**一个智能体都没有** |
| `pip install pasm-skills[torch]` | 应该装 `pasm-agents[torch]`（基座不含智能体） |
| `git clone .../pasm-skills` 然后 `python -m pasm_skills run --all` | 只装基座跑出来是 **0 个智能体**，不是验证结果 |

**这类问题没有任何测试会变红** —— 代码全绿、包也打得出来，但用户照做就是跑不动。
而且**已经发出去的 v0.2.1 正文（ClawHub）同样带着这个错**（当时还是单仓，改动后失效）。
所以必须修，而且必须让机器以后能拦住它。

已修：
- `skill/SKILL.npc.body.md` / `SKILL.companion.body.md` / `SKILL.tutor.body.md`：
  安装指引改为 clone/安装 `pasm-agents`；档位表的 `pip install pasm-skills[torch]` 同步
- `skill/SKILL.verify.body.md`：新增 **§0.5「两个仓的分工」**（先看这节，否则命令跑不动），
  定位与运行指引全部改到 `pasm-agents`；补上"只装基座会显示 0 个智能体"的显式警告；
  纯源码跑的场景给出 `PYTHONPATH=两仓 + PASM_SKILLS_AGENT_MODULES` 的完整写法

### 新增 —— `tools/check_skill_docs.py`：把这类错交给机器拦

盯住四条硬事实，不需要理解语义：

1. 本仓正文里**不许"只 clone 基座仓"**（同时 clone 两仓是合法的，用于纯源码跑）
2. `git clone` / `pip install` 的目标必须是已知仓库
3. 正文里写的模块路径（`pasm_skills.*` / `pasm_agents.*`）必须**真能 import**
4. 基座 CLI 子命令、验证智能体名必须**真实存在**

已做反向验证：故意把正文改回错误指引 → 检查器报 `[FAIL]` 并指出是哪份文件；
改回来 → `[OK] 指引与仓库现状一致`。已接入 CI。

### 变更

- 版本 0.4.1，依赖 `pasm-skills>=0.4.1`（与基座对齐）

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
