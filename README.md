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
| **产品智能体** | 4 | 使用者 | 游戏 NPC / 老人陪伴 / 学习陪伴 / 智能客服 |
| **验证智能体** | 7 | 开发者 | 核心契约 / 两仓对齐 / 回归基线 / 长效耐久 + 4 个领域验证 |

零 LLM 依赖、断网可用、状态持久化 —— **不是 mock，驱动的是真 PASM 引擎**（拿不到就降级，并在 `tier` 如实标注）。

---

## 〇、PASM 生态索引（六仓同频）

| 仓 | 角色 | 可见性 | 版本 |
|---|---|---|---|
| `pasm-skills` | 基座：`BaseAgent` + 认知能力层 | 公开 | 0.5.0 |
| **`pasm-agents`（本仓）** | **成品智能体集** | 公开 | **0.5.0** |
| `pasm-mcp-server` | MCP 接入层：给任意 AI 客户端装长期记忆 | 公开 | 0.2.0 |
| `PASM-Lite` | 教学版 + 认知引擎接口 | 公开 | — |
| `PASM` | 核心引擎（七层仿生 / 世界模型） | **私有** | 0.7.2 |
| `pasm-qclaw` | 桌面应用发行通道 | 公开 | 0.30.2 |

地址：
[Gitee](https://gitee.com/arronzheng/pasm-agents) ·
[GitHub](https://github.com/arronJack/pasm-agents)

> **0.4.5 起依赖 `pasm-skills>=0.5.0`**：本仓智能体自动获得认知能力层
> （语义检索 / 遗忘曲线 / 记忆巩固 / 焦点栈），无需改代码 —— 基座升级，智能体受益。

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

### ④ 智能客服（`CustomerServiceAgent`）

唯一建在**应用框架**（`pasm-framework` 的 `BaseApplication`）上的产品 ——
因为"客服"的核心能力是**资料库**，而资料库是框架的 `knowledge_base` 插件。

```python
from pasm_agents import CustomerServiceAgent

cs = CustomerServiceAgent(agent_id="shop-cs", persona={
    "name": "小智", "role": "售后客服", "hotline": "400-000-0000",
})
print(cs.answer("怎么退货？"))       # 就资料作答（带来源）——起步 FAQ 已自动灌好
print(cs.answer("你们能送到火星吗？")) # 查不到就如实说不知道，**绝不编造**
print(cs.answer("我要投诉你们！"))    # 自动追加【已标记转人工】并写进记忆

cs.ingest_faq([{"title": "会员日优惠",
                "content": "每月 8 日会员日，黄金会员额外 9 折。",
                "source": "faq", "tags": ["会员", "优惠"]}])
print(cs.snapshot())                # 档位 / 情绪 / 交互数 / 资料库规模 / 累计客诉
```

两条产品承诺各自都有"静默失效"的退化方式，所以都有**反例护栏**盯着：

| 承诺 | 退化方式 | 怎么防 |
|---|---|---|
| 就资料作答 | 命中什么就答什么 → **答非所问** | 命中必须落在条目的标题/标签上；查不到必须说"没有查到" |
| 客诉转人工 | 永不升级 / 乱升级 | 四类客诉必中；普通抱怨与提问必不中 |
| 资料库隔离 | 两个客服共用一个库 → 跨租户泄漏 | 每个 `agent_id` 一个库 |

> 资料库默认落在 `~/.pasm-agents/<agent_id>/kb/`，**不跟随插件那个全机共享的
> `~/.pasm_framework/kb`** —— 不隔离时 A 店的 FAQ 会出现在 B 店的答复里。
>
> 完整生产系统（DB→KB 增量同步 / 真 MCP 服务 / Web 壳 / Studio 场景一键加载）
> 在独立包 **`pasm-customer-service`**。

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
| `product-verifier`  | **产品层本身**：4 个产品的公开 API、隔离性、真实行为与反例 | 无（只需基座） |

> **上面 7 个查的都是 `pasm.cognitive`（核心认知层）**，产品层长期没人验 ——
> 这正是本仓自己记在案的已知缺口：**核心全绿不代表产品是好的**。
> `product-verifier`（2026-09-16 新增）补上它：公开 API 是否齐全、
> 四个产品能不能真的干活（tutor 掌握度该涨的涨该跌的跌、companion 关键事实答得上、
> npc 被夸后行为真的变、客服答非所问要被拦住），以及**反例**（不存在的智能体名必须报错、
> 日常闲聊不许误报危机、普通抱怨不许判成客诉、两个客服不许串资料库、
> 自检不许污染用户真实数据目录）。
>
> 它上线当场就抓到一个真 bug：`ElderlyCompanion.chat()` 在用户自定义 persona
> 用 `value`/`text` 写关键事实时抛 `KeyError: 'content'`（硬取字段名）→ 已修。

**它们通过 entry point 自动被基座发现**（本仓 `pyproject.toml` 里声明了
`[project.entry-points."pasm_skills.agents"]`），所以：

```bash
pip install pasm-agents
python -m pasm_skills list                 # ← 8 个验证智能体会出现在这里
python -m pasm_skills run core-verifier
python -m pasm_skills run --all
python -m pasm_skills run regression --update     # 刷新事实基线（写 baselines/）
```

没装 PASM 核心时它们会 `SKIP` 并说明原因 —— **不会拿自研替身糊过去**。

---

## 三、30 秒上手

```bash
pip install pasm-agents

# 四个产品智能体各有预置剧本
pasm-agents demo npc
pasm-agents demo companion
pasm-agents demo tutor
pasm-agents demo customer-service

# 交互模式（quit 退出并 save）
pasm-agents run npc --id=my_herbalist
pasm-agents run companion --id=my_companion --persona-file=personas/chenxiulan.json

pasm-agents list
pasm-agents inspect my_herbalist

# 产品层护栏（零网络、秒级；四个产品全跑）
pasm-agents selftest all
```

或直接从源码跑 —— **每个智能体自己文件夹里就有可跑示例**：

```bash
git clone https://gitee.com/arronzheng/pasm-agents
cd pasm-agents

python agents/product/npc/quickstart.py              # 游戏 NPC
python agents/product/companion/quickstart.py        # 老人陪伴
python agents/product/tutor/quickstart.py            # 学习陪伴
python agents/product/customer_service/quickstart.py # 智能客服

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
│   │   ├── tutor/                     学习陪伴
│   │   └── customer_service/          智能客服（建在框架 BaseApplication 上）
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
│   ├── npc.py / companion.py / tutor.py / customer_service.py → 转发到 agents/product/*
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
