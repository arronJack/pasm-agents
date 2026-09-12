# PASM Agents · 成品智能体集

> **本仓是智能体集：拿起来就能用的智能体。**
> 提供"写智能体"能力的**基座**在独立公开仓 **pasm-skills**。
>
> ```bash
> pip install pasm-agents      # 本仓（会自动带上基座 pasm-skills）
> ```

两类智能体，都在这里：

| | 个数 | 面向 | 例子 |
|---|---|---|---|
| **产品智能体** | 3 | 使用者 | 游戏 NPC / 老人陪伴 / 学习陪伴 |
| **验证智能体** | 7 | 开发者 | 核心契约 / 两仓对齐 / 回归基线 / 长效耐久 + 4 个领域验证 |

零 LLM 依赖、断网可用、状态持久化 —— **不是 mock，驱动的是真 PASM 引擎**（拿不到就降级，并在 `tier` 如实标注）。

---

## 一、产品智能体

### ① 游戏 NPC（`NpcAgent`）

```python
from pasm_agents import NpcAgent

npc = NpcAgent(agent_id="herbalist", persona={
    "name": "陈伯", "role": "河边摆摊的草药老头",
    "temper": 0.55, "energy": 0.40, "play": 0.30, "tone": "慢悠悠、爱讲道理",
})
npc.observe("玩家第一次来买跌打药", tags=["玩家", "买药"], salience=4)
print(npc.act())                 # 'talk' / 'wave' / 'peek' / ...
print(npc.chat("有跌打药吗"))     # 召回相关记忆
print(npc.mood)                  # 情绪（属性，不加括号）
npc.feedback("praise", action="talk")   # 显式夸"talk"这个动作 → 它会更常出现
npc.save()                       # ~/.pasm-agents/herbalist/
```

### ② 老人陪伴（`ElderlyCompanion`）

```python
from pasm_agents import ElderlyCompanion

comp = ElderlyCompanion(agent_id="chenxiulan", persona={
    "name": "陈秀兰", "age": 78, "tone": "慢、温和",
    "key_facts": [
        {"label": "用药", "content": "每天早 8 点吃降压药络活喜 5mg"},
        {"label": "过敏", "content": "青霉素过敏"},
        {"label": "家人", "content": "女儿在深圳，每周日来电话"},
        {"label": "本人", "content": "78 岁，独居"},
    ],
    "emergency_contact": {"name": "女儿小敏", "phone": "13900000000"},
    "medication_schedule": [{"name": "络活喜", "dose": "5mg", "hour": 8}],
})
print(comp.chat("我吃什么药"))            # 标签直查 → 命中率 100%
print(comp.detect_crisis("卫生间滑倒"))   # ['摔倒/外伤']
print(comp.escalate("卫生间滑倒"))        # 写入紧急记忆 + 返回升级上下文
for med in comp.due_medication(now_hour=8):
    print(f"⏰ 该吃 {med['name']} {med['dose']}")
```

> ⚠️ **不是医疗器械**，不替代任何医疗或急救服务。它只负责"记得住、认得清、说得暖"，
> **是否通知家人由调用方决定**。

### ③ 学习陪伴（`LearningTutor`）

```python
from pasm_agents import LearningTutor

t = LearningTutor(agent_id="xiaoya", persona={
    "name": "小雅", "grade": "五年级",
    "topics": ["分数加减", "面积计算", "行程问题", "鸡兔同笼"],
})
t.report("分数加减", 0.4)
print(t.pick_next())            # 最弱优先（20% 抖动防刷同一知识点）
print(t.mastery("面积计算"))
print(t.snapshot())             # 学情 JSON（mastery / weakest / average / tier）
```

---

## 二、验证智能体（给 PASM 核心做长期体检）

**只有跑久了才看得见的问题**（记忆丢失、情绪漂移、行为僵化、人格饱和）只能靠行为验证抓。

| 验证智能体 | 检查什么 | 需要哪个仓 |
|---|---|---|
| `core-verifier`     | 契约 / 安全底线 / 环境插件 | `core` |
| `parity-guard`      | 两仓核心内容逐字一致 | `core` + `studio` |
| `regression`        | 关键指纹与基线比对（基线锁定解释器档位） | `core` + `lite` |
| `npc-lifelong`      | 90 天 / 270 段经历 —— 核心能否正确记忆 NPC | `core` |
| `companion-elderly` | 30 天老人陪伴 —— 关键事实 100% 检索、危机命中 | `core` |
| `study-tutor`       | 30 天学习陪伴 —— 学情结构 + 巩固 | `core` |
| `soak-longrun`      | 6000 步认知 + 行为 + 记忆洪峰 —— 长效耐久 | `core` + `lite` |

**它们通过 entry point 自动被基座发现**（本仓 `pyproject.toml` 里声明了
`[project.entry-points."pasm_skills.agents"]`），所以：

```bash
pip install pasm-agents
python -m pasm_skills list                 # ← 7 个验证智能体会出现在这里
python -m pasm_skills run core-verifier
python -m pasm_skills run --all
python -m pasm_skills run regression --update     # 刷新事实基线（写 baselines/）
```

没装 PASM 核心时它们会 `SKIP` 并说明原因 —— **不会拿自研替身糊过去**。

---

## 三、30 秒上手

```bash
pip install pasm-agents

# 三个产品智能体各有预置剧本
pasm-agents demo npc
pasm-agents demo companion
pasm-agents demo tutor

# 交互模式（quit 退出并 save）
pasm-agents run npc --id=my_herbalist
pasm-agents run companion --id=my_companion --persona-file=personas/chenxiulan.json

pasm-agents list
pasm-agents inspect my_herbalist
```

或直接从源码跑 —— **每个智能体自己文件夹里就有可跑示例**：

```bash
git clone https://gitee.com/arronzheng/pasm-agents
cd pasm-agents

python agents/product/npc/quickstart.py         # 游戏 NPC
python agents/product/companion/quickstart.py   # 老人陪伴
python agents/product/tutor/quickstart.py       # 学习陪伴

python agents/verifiers/parity_guard/run.py     # 验证智能体同理（<1s，最快）
```

> 想看某个智能体**到底怎么写的**：打开 `agents/product/npc/agent.py`，
> 旁边就是它的 `README.md`（功能 / API / persona 字段 / 输出样例）。
> 索引在 [`agents/README.md`](agents/README.md)。

---

## 四、档位透明（永不隐藏降级）

| tier | 依赖 | 得到什么 |
|---|---|---|
| `light` | 无 | 纯内置：重要度淘汰 + 字面检索 + 性格/反馈加权 |
| `core` | 能 `import pasm.cognitive`（**不需要 torch**） | 真 `memory_layers` + `learning.LearningEngine` |
| `bionic` | 上面 + torch | 再加真情绪 / 人格模块 |

每个智能体的 `summary()` 与落盘 JSON 都带 `tier` 字段。

## 五、目录：**每个智能体一个文件夹**

打开 `agents/` 下的任意一个文件夹，都能看到它自己的**实现 + 说明 + 可跑示例** ——
不用在一个大包里翻。

```
pasm-agents/
├── agents/                          ★ 智能体目录（每个智能体一个文件夹）
│   ├── README.md                    一句话索引：10 个智能体，两类
│   ├── product/                     面向使用者
│   │   ├── npc/                       游戏 NPC
│   │   │   ├── README.md              功能 / API / persona 字段 / 输出样例
│   │   │   ├── agent.py               ★ 实现本体
│   │   │   ├── __init__.py            转发
│   │   │   └── quickstart.py          python agents/product/npc/quickstart.py
│   │   ├── companion/                 老人陪伴
│   │   └── tutor/                     学习陪伴
│   └── verifiers/                   面向开发者
│       ├── README.md                  结构层 / 行为层两层说明
│       ├── core_verifier/             结构体检
│       ├── parity_guard/              两仓一致性
│       ├── regression/                静默退化
│       ├── npc_lifelong/              90 天 NPC 行为体检
│       ├── companion_elderly/         30 天陪伴行为体检（安全关键）
│       ├── study_tutor/               30 天学习行为体检
│       └── soak_longrun/              6000 步长效耐久
│
├── pasm_agents/                     ★ 聚合转发层（公开 API 的稳定入口）
│   ├── __init__.py                    from pasm_agents import NpcAgent
│   ├── npc.py / companion.py / tutor.py        → 转发到 agents/product/*
│   ├── verifiers/                     → 转发到 agents/verifiers/*（基座靠它发现）
│   └── cli.py                         pasm-agents 命令行
│
├── skill/                           4 份技能正文（3 产品 + 1 验证）
├── tools/                           打包脚本 + 技能文档一致性检查
├── examples/                        跨智能体的综合示例
├── baselines/                       事实基线（regression 用，入库）
└── docs/AGENTS.md                   设计手册（选型分析 + 真问题表）
```

> **为什么保留 `agents/` 和 `pasm_agents/` 两层？**
> `agents/` 是**实现的家**，`pasm_agents/` 是**稳定入口**。
> 已发布的技能文档、CLI、以及基座的发现机制都依赖 `pasm_agents.*` ——
> 把入口和实现分开，**以后目录怎么整理都不会破坏用户已经写好的代码**：
>
> ```python
> from pasm_agents import NpcAgent            # 推荐：稳定入口
> from agents.product.npc import NpcAgent     # 也行：直接指到那个文件夹
> ```

## 六、相关仓

| 仓 | 定位 | 关系 |
|---|---|---|
| **pasm-skills** | 基座：SDK / 框架 / 打包工具 / 脚手架 | ← **本仓依赖它** |
| **本仓 pasm-agents** | 成品智能体集 | |
| PASM | 认知引擎核心 | 私有；智能体可选驱动它 |
| PASM-Lite | 教学与认知引擎协议 | 公开 |
| pasm-qclaw | 桌面应用发行 | 公开 |

想**自己写一个智能体**？看基座仓的
[`docs/BUILD-AGENT.md`](https://gitee.com/arronzheng/pasm-skills/blob/master/docs/BUILD-AGENT.md) 与
`templates/` —— 本仓的源码就是最好的例子。

## 七、技能包

4 个技能包（3 产品 + 1 验证），各自独立、可单独上传：

```bash
python tools/build_skill.py --zip --clean
# 产物：../pasm-agents-dist/{zip-root,slug-dir}/<name>/SKILL.md + <name>-<ver>.zip
```

## 八、许可证

MIT。技能包在部分平台需按平台要求标 `MIT-0`（比 MIT 更宽松，**允许无署名使用**）——
`tools/build_skill.py` 里对两种形态分别处理，详见基座仓的 `docs/SKILL-FORMAT.md`。
