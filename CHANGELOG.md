# Changelog

本项目遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [0.4.1] — 2026-09-12

### 修复 —— 已发布技能的正文（ClawHub v0.2.1，**33 次下载**）会让人跑不动

已发布那份正文让用户 `git clone pasm-skills` 再跑 `run core-verifier` —— 拆仓后这条路
**必然失败**（基座 0 个智能体）。已下载的人不会自动更新，所以新版正文**在最前面加了自救章节**：

> **⚠️ 如果你装的是 0.2.x** —— 症状（`list` 显示 0 个 / 报"未知智能体"）、
> 原因（拆仓后旧文档指向了错仓，**不是你的操作错了**）、修复（三条命令）。
> 附一句自检口诀：**`list` 显示 0 个 = 你只有基座**。

同时基座 CLI 也在**运行时报**这条指引（见 pasm-skills 0.4.1）—— 双保险：
用户哪怕拿着旧文档，也会在第一条命令就被指对方向。

### 变更 —— 四份正文补「功能说明」与「基座介绍」

正文此前直接进用法，没说清"这东西给我什么"和"它建在什么之上"。现在每份都有两节：

- **「这个技能给你什么」**：能力表（记忆 / 情绪 / 动作 / 持久化 …）+ 常用方法一行速查
- **「它跑在什么之上：基座 pasm-skills」**：两仓分工表 + 装 `pasm-agents` 自动带基座 +
  "只装基座会看到 0 个智能体（刻意如此）" + 基座教程链接

### 修复 —— 正文里的维护者内部注释泄漏到用户页面

四份正文开头都带着给维护者看的
`> 本文件是 SKILL.md 的正文部分（不含 frontmatter）…` —— 它**原样出现在 ClawHub 的技能页上**
（用户点开 SKILL.md 就看到构建说明）。已全部清除；维护者说明改放 `skill/README.md`，
并在那里写明"这几条不许再写回正文"。

### 修复 —— 过期模块路径

`SKILL.npc.body.md` 里的 `pasm_agents/base.py` 已不存在（拆仓时提升为基座的 `pasm_skills/sdk/base.py`）。

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
