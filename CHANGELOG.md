# Changelog

本项目遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [0.4.3] — 2026-09-12

### 修复 —— 安装态下 `regression` 把基线写进了 site-packages

`pip install pasm-agents` 之后跑 `python -m pasm_skills run regression`，
基线被写到了**安装目录里**（`…/site-packages/agents/baselines/core.json`），
并且**完全忽略仓库里入库的那份基线**。

两个后果：

- 安装区可能只读（系统级安装 / 容器）→ 直接失败；
- 就算写成功，用户看到「首次运行：已建立基线」以为自己有基线了，
  实际上与维护者/队友那份毫无关系 → **回归比对从此没有意义**。

根因是 `_repo_root()` 的兜底分支 `here.parents[2]` 在安装态下算不到仓库根
（在源码树里它正好是对的，装到 site-packages 后只能落在安装区内）。
**这是 0.4.2 目录重构之前就存在的问题，与那次重构无关。**

现在的行为：

| 运行方式 | 基线落点 | 说明 |
|---|---|---|
| 源码树内（`git clone` 后跑） | `<repo>/baselines/` | 与入库基线同一份，人与人可比（**行为不变**） |
| 已安装（`pip install`） | `~/.pasm-agents/baselines/` | 只对本机有效，并显式 `[WARN]` 说明它与仓库基线不是同一份 |

顺带把兜底从"猜一个路径"改成返回 `None` —— 猜错了比直说找不到更危险。

### 修复 —— 验证智能体的 `run.py` 在纯源码模式下跑不起来

README 承诺「每个智能体自己文件夹里就有可跑示例」，但 7 个 `run.py` 只设了
`PASM_SKILLS_AGENT_MODULES`（让基座发现本仓的智能体），**没保证基座本身能被 import**
→ `git clone` 之后直接跑会报 `No module named 'pasm_skills'`。
（同目录的 `quickstart.py` 有完整引导，所以只有 `run.py` 断。）

现在 `run.py` 会把本仓与同级 `pasm-skills` 一起放进 `PYTHONPATH`；
两条路都走不通时直接打印修复指引，而不是抛一个 `ImportError` 让用户猜。

> 另修 `tools/check_skill_docs.py` 的提示文案：它只说"检查 PYTHONPATH 是否含基座仓"，
> 但实际最常见的缺法是**缺本仓** —— 文案改成"两个仓都要在"。

> 本次**没有改任何技能正文**，4 个技能包内容与已发布版本逐字一致
> （仅 frontmatter 的 `version` 随版本号走），**无需重新上传平台**。

## [0.4.2] — 2026-09-12

### 重构 —— **每个智能体一个文件夹**（`agents/`）

十个智能体此前全挤在 `pasm_agents/` 一个包里，想单独看某一个得先翻整包。
现在每个智能体都有自己的家：

```
agents/
├── product/{npc,companion,tutor}/        面向使用者
└── verifiers/{core_verifier,…,soak_longrun}/   面向开发者
     每个文件夹：README.md + agent.py + __init__.py (+ quickstart.py / run.py)
```

`pasm_agents/` 退化为**聚合转发层**（10 个 3 行薄壳）。
这样分层是为了满足一条硬约束：**已发布的技能包、CLI、基座发现机制
全部依赖 `pasm_agents.*`，不能因为整理目录而破坏用户已经写好的代码。**

| 之前 | 现在 |
|---|---|
| `from pasm_agents import NpcAgent` | ✅ 不变 |
| `pasm_agents.verifiers`（entry point） | ✅ 不变 |
| `pasm_agents/verifiers/npc_lifelong.py`（技能正文点过名） | ✅ 文件仍在（薄壳），只是指向新实现 |
| 想看实现 → `pasm_agents/npc.py` | 现在去 `agents/product/npc/agent.py`（旁边就是它的 README） |

**因此本次不改动任何已上传的技能包** —— 四个技能（v0.4.1，已在 WorkBuddy 审核中、
在 ClawHub 发布）的正文一字未动，它们引用的路径全部仍然有效。

### 新增 —— 每个智能体的 README + 可直接跑的示例

- `agents/README.md`：一句话索引（10 个智能体、两类、实跑耗时）+ 两层结构说明
- `agents/product/<name>/README.md`：能力表 / 最小用法 / API 表 / persona 字段含义 / 输出样例 / **已知短板如实说明**
- `agents/product/<name>/quickstart.py`：`python agents/product/npc/quickstart.py` 直接看到效果
- `agents/verifiers/<name>/README.md`：它查什么（分项表格） / 实跑规模 / 已经抓到过什么
- `agents/verifiers/<name>/run.py`：帮你配好发现路径，等价于 `python -m pasm_skills run <name>`

### 修复 —— 搬迁暴露出的**真 bug**：回归基线被静默写到了错误位置

`regression` 用 `Path(__file__).resolve().parents[2]` 推仓库根。文件从
`pasm_agents/verifiers/regression.py` 搬到 `agents/verifiers/regression/agent.py` 后，
`parents[2]` 从「仓库根」变成了「`agents/`」—— 于是它在 `agents/baselines/` **新建了一份基线**，
真基线被遮蔽，表面看每项都「与基线一致」。

**这是最危险的一类失效**：检查全绿，但它比对的是自己刚写的一份，从此不再有任何约束力。
已改为**向上找 `pyproject.toml`** 定位仓库根，搬到哪里都对。

> 教训写进 docs/AGENTS.md 了：**凡是按目录深度推算路径的地方，都会在某次重构后静默失效。**

### 验证

- 全量 **103 ok / 8 warn / 0 fail** —— 与重构前逐项一致
- 三个 `quickstart.py` + 两个 `run.py` 实跑通过
- `tools/check_skill_docs.py`（6 类）通过
- **wheel 构建 + 解包安装测试**：在仓库外（模拟 `pip install`）导入
  `from pasm_agents import NpcAgent` / `pasm_agents.verifiers` / `agents.product.tutor` 全部通过

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
