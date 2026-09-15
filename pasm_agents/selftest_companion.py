"""老人陪伴产品智能体（ElderlyCompanion）的自测 —— 零 LLM、零网络、秒级出结果。

为什么需要它
------------
`ElderlyCompanion` 承诺的三件事里，第一件是 **"关键事实永不丢"** ——
查不到老人对什么过敏、吃什么药，不是"体验差一点"，是**事故**。
这类能力靠人肉点几遍是守不住的：改动 `_label_query` 的别名表、
调整 `_render_reply` 的判定顺序，都可能让某一路直查**静默失效**，
而底层记忆层的 30 天验证器（`agents/verifiers/companion_elderly`）**照常全绿** ——
因为它测的是记忆引擎，不是这条产品层的口语直查通路。

所以本文件专门盯住**产品层契约**，把下面几条钉死：

  1. **口语 → 标签直查**：同一件事实，老人用十来种说法问，都必须命中
     （FAIL 级：任一说法漏了就算失败）；
  2. **无中生有防护**：跟关键事实无关的问句（"今天天气不错"）**不许**吐出一条事实，
     宁可回"我在听"；
  3. **危机识别**：四类危机各有正样本，且日常话不得误报；
  4. **升级语义**：`escalate()` 只准备上下文（含紧急联系人），**不自己打电话**；
  5. **用药提醒纯时间比对**：整点相等才返回，不涉药理判断；
  6. **落盘**：save 后重建实例，关键事实仍在；
  7. **不说工程术语**：回复里不许出现 salience / token / 标签 / 检索 这类词。

为什么这个模块**在包里**而不是只在仓库的 `tools/` 下
--------------------------------------------------
技能正文推荐的安装方式是 `pip install pasm-agents`，而 pip 装出来的 wheel **不含 `tools/`**
（`packages.find` 只收 `pasm_agents*` 与 `agents*`）。也就是说：如果护栏只放在 `tools/`，
那么**照文档做的用户根本跑不了它** —— 文档教了一条他自己没有的命令。
放进包内之后，两种用户都能跑：

    python -m pasm_agents.selftest_companion      # pip 安装的用户（推荐）
    python tools/selftest_companion.py            # 仓库源码用户（薄壳转发到上面那个）

退出码 0=全过，1=有失败 —— 可直接进 CI。
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):          # Windows 控制台默认 gbk，中文会炸
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")   # type: ignore[attr-defined]
    except Exception:
        pass

# 落盘位置由 SDK 固定为 ~/.pasm-agents/<agent_id>，没有环境变量开关。
# 所以这里用专用 agent_id，并在开跑前清掉上一轮的残留 ——
# 否则上次 escalate 压低的情绪会带进本轮，断言就变成"看运气"。
# 清的是 **整族**（`selftest_companion*`），不是单个 id：本自检现在只用基础 id，
# 但一旦有人加了 `_xxx` 变体而忘了同步清理，残留就会让同一个 wheel 给出不同结论。
# 护栏不可重复 = 比没有护栏更坏：它会把"机器脏"说成"能力坏"。
_AGENT_ID = "selftest_companion"
for _stale in (Path.home() / ".pasm-agents").glob(_AGENT_ID + "*"):
    shutil.rmtree(_stale, ignore_errors=True)

from pasm_agents import ElderlyCompanion, CRISIS_KEYWORDS, LABEL_ALIASES  # noqa: E402
import pasm_agents  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  -> {detail}" if detail else ""))


PERSONA = {
    "name": "陈秀兰", "age": 78, "tone": "慢、温和",
    "key_facts": [
        {"label": "用药", "content": "每天早 8 点吃降压药络活喜 5mg"},
        {"label": "过敏", "content": "青霉素过敏"},
        {"label": "家人", "content": "女儿在深圳，每周日来电话"},
        {"label": "本人", "content": "78 岁，独居"},
    ],
    "emergency_contact": {"name": "女儿小敏", "phone": "13900000000"},
    "medication_schedule": [{"name": "络活喜", "dose": "5mg", "hour": 8}],
}

#: 同一件事实的多种口语说法 —— 这里就是"老人会怎么说"的清单。
#: 加方言时，先把它加进本表（测试先行），再补 `LABEL_ALIASES`
#: （或用 `pasm_agents.register_label_aliases({"用药": ("喝汤药",)})` 运行时加，不必改源码）。
#:
#: ⚠️ 2026-09-15 扩容：原表 21 条，是**作者自己会怎么问**；真机反馈回来的缺口是
#: 「我家里人呢」——「家里人」三个字不等于表里的「家人」，正则不命中就掉进兜底闲聊。
#: 教训：口语词表要按"老人怎么说"列，不是按"标签长什么样"列。故此处刻意扩到 46 条，
#: 覆盖 直系/配偶/姻亲/孙辈 + 服药各种问法 + 身份/年龄/住址各种问法，且**负样本不放松**。
SPOKEN = {
    "用药": ["我吃什么药", "我早上该吃什么药", "我吃的什么药", "我要吃药了吗",
             "药吃几粒", "我有降压药吗", "我的药呢", "药还有吗", "我几点吃药",
             "今天吃药了没有", "我一天吃几次药", "要服药了吗"],
    "过敏": ["我对什么过敏", "我对什么药过敏", "我不能吃什么", "我有什么忌口",
             "我忌口吗", "什么东西我不能吃", "我对青霉素过敏吗"],
    "家人": ["我家里人呢", "我儿子什么时候回来", "我闺女在哪", "谁给我打电话",
             "我老伴呢", "我孙子呢", "谁会来看我", "我家里都有谁", "我姑娘呢",
             "我儿媳妇呢", "我女婿呢", "我兄弟呢", "我姐妹在哪", "我娃呢",
             "我爹呢", "我妈呢", "谁会来看望我"],
    "本人": ["我叫什么名字", "我多大了", "我住哪", "我是谁", "我叫啥",
             "我几岁", "我多少岁", "我住在哪里", "我姓什么", "我老家哪"],
}

#: 期望命中标签 → 该标签事实 content 里的独有关键词
KEYWORDS = {
    "用药": ["络活喜", "降压"],
    "过敏": ["青霉素"],
    "家人": ["女儿", "深圳"],
    "本人": ["78", "独居"],
}

#: 负样本：与四类关键事实无关，**不该**吐出任何一条事实。
#: 扩大词表的代价是误命中风险上升 —— 所以负样本也要跟着扩，把"扩词"和"别乱吐"钉在一起。
NEGATIVE = ["今天天气不错", "我想吃面条", "邻居家的猫又来了", "睡不着觉",
            "我想出去走走", "好无聊啊", "帮我倒杯水", "电视怎么开",
            "外面下雨了吗", "我想听戏", "这屋有点冷"]


def main() -> int:
    comp = ElderlyCompanion(agent_id=_AGENT_ID, persona=PERSONA)

    print("=" * 64)
    print(f"pasm_agents {pasm_agents.__version__}  |  companion selftest")
    print(f"档位 tier = {getattr(comp, 'tier', '?')}   (light 为断网可用的纯内置档)")
    print("=" * 64)

    # ---- 1. 口语直查：每种说法都要命中 ----
    print("\n--- 1. 口语 → 标签直查（FAIL 级：必须全中）---")
    total = hit = 0
    for label, asks in SPOKEN.items():
        for q in asks:
            total += 1
            reply = comp.chat(q)
            ok = any(k in reply for k in KEYWORDS[label])
            hit += 1 if ok else 0
            print(f"   [{'ok' if ok else 'MISS'}] {label} | {q}\n         -> {reply}")
    check("口语直查全覆盖", hit == total, f"{hit}/{total}")

    # ---- 2. 无中生有防护 ----
    print("\n--- 2. 无中生有防护（无关问句不许吐事实）---")
    ghosts = []
    for q in NEGATIVE:
        reply = comp.chat(q)
        leaked = [k for kws in KEYWORDS.values() for k in kws if k in reply]
        if leaked:
            ghosts.append((q, reply, leaked))
        print(f"   {q} -> {reply}")
    check("无关问句 0 泄漏", not ghosts, f"泄漏 {ghosts}" if ghosts else "0 条泄漏")

    # ---- 3. 危机识别 ----
    print("\n--- 3. 危机识别 ---")
    crisis_cases = [
        ("我胸口有点闷，喘不上气", True),
        ("在卫生间滑倒了，起不来", True),
        ("今天有点头晕，眼前发黑", True),
        ("活着没意思，不想活了", True),
        ("今天天气不错，我吃了两个包子", False),
        ("女儿说明天来看我", False),
    ]
    bad = []
    for text, expect in crisis_cases:
        cats = comp.detect_crisis(text)
        ok = (len(cats) > 0) == expect
        if not ok:
            bad.append((text, cats, expect))
        print(f"   {text!r} -> {cats}")
    check("危机识别正负样本全对", not bad, f"{bad}" if bad else f"{len(crisis_cases)}/{len(crisis_cases)}")
    check("四类危机类别齐备", len(CRISIS_KEYWORDS) >= 4, f"{list(CRISIS_KEYWORDS)}")

    # ---- 4. 升级语义 ----
    print("\n--- 4. 危机升级（只准备上下文，不代替人做决定）---")
    info = comp.escalate("卫生间滑倒")
    need = ["agent_id", "persona_name", "reason", "suggested_action",
            "emergency_contact", "snapshot", "ts"]
    missing = [k for k in need if k not in info]
    check("escalate 返回结构完整", not missing, f"缺 {missing}" if missing else "7/7 字段齐")
    check("紧急联系人随上下文返回",
          info.get("emergency_contact", {}).get("phone") == "13900000000",
          str(info.get("emergency_contact")))
    check("情绪被压低（负向）", comp.mood < 0.0, f"mood={comp.mood}")
    print(f"   suggested_action: {info.get('suggested_action')}")

    # ---- 5. 用药提醒：纯时间比对 ----
    print("\n--- 5. 用药提醒 ---")
    due8 = comp.due_medication(now_hour=8)
    due9 = comp.due_medication(now_hour=9)
    check("8 点返回络活喜", len(due8) == 1 and due8[0]["name"] == "络活喜", str(due8))
    check("9 点返回空", len(due9) == 0, str(due9))

    # ---- 6. 落盘 ----
    print("\n--- 6. 状态落盘 ---")
    comp.save()
    comp2 = ElderlyCompanion(agent_id=_AGENT_ID, persona=PERSONA)
    r2 = comp2.chat("我对什么过敏")
    check("重载后关键事实仍在", "青霉素" in r2, r2)

    # ---- 7. 不说工程术语 ----
    print("\n--- 7. 回复自然度 ---")
    jargon = ["salience", "token", "embedding", "prompt", "标签", "记忆层", "检索", "向量"]
    leaked = [(q, j) for q in list(SPOKEN["家人"]) + NEGATIVE
              for j in jargon if j in comp.chat(q)]
    check("回复不含工程术语", not leaked, f"{leaked}" if leaked else "0 命中")

    # ---- 8. 别名表结构自检 ----
    print("\n--- 8. 别名表结构 ---")
    dup = [lab for lab, pats in LABEL_ALIASES.items() if len(pats) != len(set(pats))]
    check("别名表无重复项", not dup, f"重复 {dup}" if dup else f"{len(LABEL_ALIASES)} 个标签")
    check("四个内置标签都在表里",
          {"用药", "过敏", "家人", "本人"} <= set(LABEL_ALIASES), str(list(LABEL_ALIASES)))

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
