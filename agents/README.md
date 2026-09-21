# PASM 智能体目录

**每个智能体一个文件夹** —— 打开哪一个，都能看到它自己的实现、说明和可跑示例，
不用在一个大包里翻。

```
agents/
├── product/          ← 面向使用者：拿去就能用
│   ├── npc/            游戏 NPC
│   ├── companion/      老人陪伴
│   ├── tutor/          学习陪伴
│   └── customer_service/  智能客服（唯一建在框架 BaseApplication 上的产品）
└── verifiers/        ← 面向开发者：给认知引擎做长期体检
    ├── core_verifier/      结构体检
    ├── parity_guard/       两仓一致性
    ├── regression/         静默退化
    ├── npc_lifelong/       90 天 NPC 行为体检
    ├── companion_elderly/  30 天陪伴行为体检（安全关键）
    ├── study_tutor/        30 天学习行为体检
    └── soak_longrun/       6000 步长效耐久
```

## 两类智能体，别混

| | `product/` | `verifiers/` |
|---|---|---|
| 面向谁 | 你的游戏 / 应用 / 产品 | 你自己的开发流程 |
| 干什么 | 真的陪你玩、陪老人、陪学生 | 回答「引擎跑久了还是好的吗」 |
| 生命周期 | 一直活着，**有状态** | 跑一次、出报告、退出 |
| 状态 | 落盘 `~/.pasm-agents/<id>/` | 无状态，**只读**被检查的仓库 |
| 典型用法 | `npc.chat("有跌打药吗")` | `python -m pasm_skills run core-verifier` |

## 每个文件夹里有什么

以 `agents/product/npc/` 为例，其余同构：

```
npc/
├── README.md        ← 功能 / API / 字段含义 / 输出样例
├── agent.py         ← 实现本体（唯一真相）
├── __init__.py      ← 转发，方便 from agents.product.npc import NpcAgent
└── quickstart.py    ← 可直接跑：python agents/product/npc/quickstart.py
```

## 一句话索引

### 成品智能体（`product/`）

| 智能体 | 一句话 | 主类 | 跑一下 |
|---|---|---|---|
| [`npc`](product/npc/) | 有记忆、有情绪、会被玩家夸/凶塑形的游戏 NPC | `NpcAgent` | `python agents/product/npc/quickstart.py` |
| [`companion`](product/companion/) | 记得住用药/过敏/家人，识别危机并升级到家人的陪伴 | `ElderlyCompanion` | `python agents/product/companion/quickstart.py` |
| [`tutor`](product/tutor/) | 按知识点追踪掌握度、最弱优先选题的学习陪伴 | `LearningTutor` | `python agents/product/tutor/quickstart.py` |

### 验证智能体（`verifiers/`）

| 智能体 | 查什么 | 实跑 |
|---|---|---|
| [`core_verifier`](verifiers/core_verifier/) | 引擎接口契约 / 认知层是否落盘 / 符号推理闭环 / 环境插件 / 安全底线 / 冒烟 | 33 项 · ~25s |
| [`parity_guard`](verifiers/parity_guard/) | 核心仓 ↔ Studio 镜像仓同名文件**逐字一致** | 2 项 · <1s |
| [`regression`](verifiers/regression/) | 对事实基线逐项比对，抓**静默退化** | 9 项 · ~8s |
| [`npc_lifelong`](verifiers/npc_lifelong/) | 90 天 × 270 段经历：里程碑记忆留没留住、同分检索崩不崩、行为会不会僵化 | 19 项 · ~7s |
| [`companion_elderly`](verifiers/companion_elderly/) | 30 天：关键事实检索、危机识别与升级、答复一致性 | 17 项 · ~10s |
| [`study_tutor`](verifiers/study_tutor/) | 30 天：掌握度结构、自适应选题、停练是否衰减 | 15 项 · ~5s |
| [`soak_longrun`](verifiers/soak_longrun/) | 6000 步认知 + 6000 步行为 + 记忆洪峰：性能衰减、人格饱和、状态可复现 | 15 项 · ~15s |

全跑一遍（当前实测 **103 ok / 8 warn / 0 fail**，约 1 分钟）：

```bash
python -m pasm_skills run --all
```

## 和 `pasm_agents` 包的关系

`agents/` 是**实现的家**；`pasm_agents/` 是**稳定入口**（聚合转发层）。

```python
# 两种写法等价；前者是公开 API，目录怎么重构都不受影响：
from pasm_agents import NpcAgent            # 推荐：稳定入口
from agents.product.npc import NpcAgent     # 也行：直接指到那个文件夹
```

> 为什么保留两层：已发布的技能文档、CLI、基座的发现机制都依赖 `pasm_agents.*`。
> 把入口和实现分开，**目录怎么整理都不会破坏用户已经写好的代码**。
