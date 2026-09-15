"""游戏 NPC 产品智能体（NpcAgent）的自测 —— 零 LLM、零网络、秒级出结果。

为什么需要它
------------
`NpcAgent` 的卖点是"**记得住玩家**"。但"记得住"有三个很容易被写坏的边界，
而且坏了以后**没有任何别的测试会报错** —— 底层 90 天验证器
（`agents/verifiers/npc_lifelong`）测的是记忆引擎，不是这一层回复模板：

  1. **问身份 vs 提"名字"**：触发词里只要留一个光杆「名字」，
     「我给你起个名字吧 / 我名字叫张三 / 这花有名字吗」就全被当成在问 NPC 是谁。
     2026-09-15 探针实测：4/4 误触发（和 `pasm_companion` 曾经误判"能力"是同一类坑）。
  2. **人设不能泄漏**：模板里写死「老朽」，卖花的小姑娘也会说"老朽还记着呢"。
     **自称必须由 persona 决定**（`self_ref`，留空用中性「我」）。
  3. **"共同经历"要真的是经历**：NPC 的自我介绍（`bootstrap_event` 写入）
     与玩家刚说的话（`chat()` 自动入库，标题前缀「对话：」）都不是"上次那件事"，
     却被"记得"分支念了出来 —— 实测会输出「我叫阿宝，平和。，记得。」这种错位句子。

顺带记一条容易踩的底层事实：``recall()`` 返回的 fact **不含 `category` 字段**
（实测恒为 ``None``），所以这里只能靠 tags 与标题前缀判别，不能按 category 过滤。

退出码 0=全过，1=有失败 —— 可直接进 CI。
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):          # Windows 控制台默认 gbk，中文会炸
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")   # type: ignore[attr-defined]
    except Exception:
        pass

# 落盘位置由 SDK 固定为 ~/.pasm-agents/<agent_id>，没有环境变量开关。
# 用专用 id 并在开跑前清掉残留，否则上一轮的情绪/记忆会带进本轮，断言就变成"看运气"。
_AGENT_ID = "selftest_npc"

#: 本自检共用到 5 个 id（`_AGENT_ID` 及其 `_ref/_brief/_fresh/_real` 变体）。
#: **必须整族清掉**，只清基础 id 是不够的 —— 变体目录的残留会改变召回排序，
#: 于是同一个 wheel 在不同机器/同一机器连跑两次会给出不同结论
#: （2026-09-15 实测：pip 装出的包 9/12 → 10/12 → 清干净后稳定 12/12）。
#: 护栏不可重复 = 比没有护栏更坏：它会把"机器脏"说成"能力坏"。
for _stale in (Path.home() / ".pasm-agents").glob(_AGENT_ID + "*"):
    shutil.rmtree(_stale, ignore_errors=True)

from pasm_agents import NpcAgent, NPC_PERSONA_TEMPLATE          # noqa: E402
from agents.product.npc.agent import _is_shared_memory           # noqa: E402
import pasm_agents                                               # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  -> {detail}" if detail else ""))


PERSONA = {
    "name": "小翠", "role": "卖花的小姑娘", "tone": "活泼俏皮",
    "temper": 0.6, "energy": 0.7, "play": 0.8,
}

#: 真的在问 NPC 是谁 —— 应当触发自我介绍
ASKS_IDENTITY = ["你叫什么", "你是谁", "你叫啥", "你的名字是什么", "怎么称呼你", "你是哪位"]

#: 提到"名字"但**不是**在问 NPC 是谁 —— 不许触发自我介绍
NOT_ASKING_IDENTITY = ["我给你起个名字吧", "我名字叫张三", "这花有名字吗",
                       "这个名字好玩", "名字取得不错", "你名字好听"]

#: 与 NPC 无关的闲聊 —— 没有真实经历时，不许念出「记得」
SMALL_TALK = ["今天天气不错", "我想出去走走", "随便聊聊", "好无聊啊", "帮我拿个东西"]

#: 这些自称只能来自 persona，不许在模板里写死
BORROWED_SELF_REF = ["老朽", "老夫", "老身", "本座", "在下", "老奴"]

#: 自我介绍分支的**签名**。不能用「回复里含 role」当判据 ——
#: 兜底句、记忆回显里都可能合法地带上 role/昵称，那会把正常的兜底误判成抢答
#: （2026-09-15 本轮真踩过：三条兜底句被当成"误触发"）。
IDENTITY_MARK = f"{PERSONA['name']}道："


def main() -> int:
    npc = NpcAgent(agent_id=_AGENT_ID, persona=PERSONA)
    print("=" * 64)
    print(f"pasm_agents {pasm_agents.__version__}  |  npc selftest")
    print(f"档位 tier = {getattr(npc, 'tier', '?')}   (light 为断网可用的纯内置档)")
    print("=" * 64)

    # ---- 1. 问身份：正样本必须介绍自己 ----
    print("\n--- 1. 问身份（正样本必须自我介绍）---")
    miss = []
    for q in ASKS_IDENTITY:
        r = npc.chat(q)
        if IDENTITY_MARK not in r:
            miss.append((q, r))
        print(f"   [{'ok' if IDENTITY_MARK in r else 'MISS'}] {q} -> {r}")
    check("问身份都能自我介绍", not miss,
          f"漏 {miss}" if miss else f"{len(ASKS_IDENTITY)}/{len(ASKS_IDENTITY)}")

    # ---- 2. 提"名字" ≠ 问身份：不许抢答 ----
    print("\n--- 2. 提「名字」≠ 问身份（负样本不许自我介绍）---")
    fp = []
    for q in NOT_ASKING_IDENTITY:
        r = npc.chat(q)
        bad = IDENTITY_MARK in r
        if bad:
            fp.append((q, r))
        print(f"   [{'误触发' if bad else 'ok'}] {q} -> {r}")
    check("「名字」不误判为问身份", not fp,
          f"误触发 {fp}" if fp else f"0/{len(NOT_ASKING_IDENTITY)} 误触发")

    # ---- 3. 自称由 persona 决定 ----
    print("\n--- 3. 自称必须来自 persona（不许写死）---")
    check("默认模板 self_ref 留空", NPC_PERSONA_TEMPLATE.get("self_ref") == "",
          repr(NPC_PERSONA_TEMPLATE.get("self_ref")))
    leaked = []
    for q in ASKS_IDENTITY + SMALL_TALK:
        r = npc.chat(q)
        hit = [b for b in BORROWED_SELF_REF if b in r]
        if hit:
            leaked.append((q, r, hit))
    check("默认人设不出现借来的自称", not leaked, f"{leaked}" if leaked else "0 命中")

    named = NpcAgent(agent_id=_AGENT_ID + "_ref",
                     persona=dict(PERSONA, self_ref="老夫"))
    named.observe("玩家救过我", brief="差点淹死", tags=["玩家", "救命"], salience=5, category="重大")
    r_ref = named.chat("你还记得什么")
    check("self_ref 可被 persona 覆盖（老夫）", "老夫" in r_ref, r_ref)

    # ---- 4. brief 为空时回退到 title，不留空占位 ----
    print("\n--- 4. 记忆回显不留空占位 ---")
    n2 = NpcAgent(agent_id=_AGENT_ID + "_brief", persona=PERSONA)
    n2.observe("玩家救过我", salience=5, tags=["玩家", "救命"])     # 故意不传 brief
    r2 = n2.chat("你还记得什么")
    check("brief 为空时回退到 title", "玩家救过我" in r2, r2)
    empty_slot = bool(re.search(r"上次[，,、]\s*[^，,、]", r2))
    check("不出现「上次，」空占位", not empty_slot, r2)

    # ---- 5. 没有真实经历时不念「记得」 ----
    print("\n--- 5. 没有真实经历时不念「记得」---")
    n3 = NpcAgent(agent_id=_AGENT_ID + "_fresh", persona=PERSONA)
    ghosts = []
    for q in SMALL_TALK:
        r = n3.chat(q)
        if "记得" in r:
            ghosts.append((q, r))
        print(f"   {q} -> {r}")
    check("自我介绍/玩家原话不被当作共同经历", not ghosts,
          f"错位回显 {ghosts}" if ghosts else f"0/{len(SMALL_TALK)}")

    # ---- 6. 有真实经历时仍要记得 ----
    print("\n--- 6. 真实里程碑仍能召回 ---")
    n4 = NpcAgent(agent_id=_AGENT_ID + "_real", persona=PERSONA)
    n4.observe("玩家在河边把我拉了上来", brief="我差点淹死",
               tags=["玩家", "河边", "救命"], salience=5, category="重大")
    r4 = n4.chat("还记得河边那次吗")
    # 注意：里程碑分支的固定句式是「……我还记**着**呢」，不是「记得」——
    # 断言别只认「记得」，否则会把正确行为判成失败（本轮的第二个假红）。
    check("真实里程碑能召回", ("记" in r4) and ("淹死" in r4 or "河边" in r4), r4)

    # ---- 7. _is_shared_memory 语义（直接钉住判别函数）----
    print("\n--- 7. 共同经历判别函数 ---")
    cases = [
        ({"title": "对话：随便聊聊", "tags": ["随便"]}, False, "玩家原话"),
        ({"title": "我是卖花的小姑娘", "tags": ["我", "小翠", "自我介绍"]}, False, "自我介绍"),
        ({"title": "玩家救了我", "brief": "差点淹死", "tags": ["玩家", "救命"]}, True, "真实事件"),
        ({"title": "", "tags": []}, True, "无标题（交由调用方按 brief 兜底）"),
    ]
    bad = [(c[2], _is_shared_memory(c[0]), c[1]) for c in cases if _is_shared_memory(c[0]) != c[1]]
    check("判别函数四类全对", not bad, f"{bad}" if bad else f"{len(cases)}/{len(cases)}")

    # ---- 8. 结构自检 ----
    print("\n--- 8. 结构 ---")
    check("自我介绍带哨兵标签",
          "自我介绍" in n4.bootstrap_event()[0]["tags"],
          str(n4.bootstrap_event()[0]["tags"]))
    check("动作池非空", bool(npc.action_pool()), str(npc.action_pool()))

    print("\n" + "=" * 64)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"结果：{passed}/{len(RESULTS)} 通过")
    for name, ok, _ in RESULTS:
        if not ok:
            print(f"  FAIL -> {name}")
    print("=" * 64)
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
