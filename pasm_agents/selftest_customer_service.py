"""智能客服产品智能体（CustomerServiceAgent）的自测 —— 零 LLM、零网络、秒级出结果。

为什么需要它
------------
智能客服最容易犯的两类错，**都不会让任何别的测试变红**：

  * **编造**：资料库里没有的问题，也编一段像模像样的答复出来。
    对一个客服来说这比"答不上来"严重得多 —— 用户按编的答案去做了。
  * **乱升级**：把普通抱怨（"这个功能真难用啊"）当客诉转人工，
    或者反过来把「我要起诉你们」当普通问题答成"抱歉没查到"。
    词表一放宽/收紧就会偏，而底层验证器（`agents/verifiers/*`）测的是
    记忆与情绪结构，看不见回复模板的触发边界。

判据按铁律走：**无法判定 = 不升级、答不上来 = 如实说不知道**，绝不硬猜。

退出码 0=全过，1=有失败 —— 可直接进 CI。
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):          # Windows 控制台默认 gbk，中文会炸
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")   # type: ignore[attr-defined]
    except Exception:
        pass

# 落盘位置由 SDK 固定为 ~/.pasm-agents/<agent_id>，没有环境变量开关。
# 清**整族**（`selftest_customer_service*`）而不是单个 id ——
# 只清基础 id 时，变体目录的残留会让同一个 wheel 给出前后不一致的结论。
_AGENT_ID = "selftest_customer_service"
for _stale in (Path.home() / ".pasm-agents").glob(_AGENT_ID + "*"):
    shutil.rmtree(_stale, ignore_errors=True)

from pasm_agents import CustomerServiceAgent                        # noqa: E402
from agents.product.customer_service.agent import (                 # noqa: E402
    DEFAULT_FAQ, ESCALATION_RULES, detect_escalation,
    semantic_tokens, touches_surface,
)
import pasm_agents                                                  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  -> {detail}" if detail else ""))


PERSONA = {
    "name": "小智", "role": "售后客服",
    "tone": "温暖、专业、耐心",
    "hotline": "400-000-0000",
}

#: 资料库里**有**的问题（起步 FAQ）—— 必须答得上，且带来源
IN_KB = [
    ("怎么退货？", "无理由退货"),
    ("多久能发货？", "24 小时"),
    ("发票怎么开？", "电子发票"),
    ("会员有什么权益？", "黄金会员"),
    ("可以用支付宝吗？", "支付宝"),
]

#: 资料库里**没有**的问题 —— 必须如实说不知道，**不许编造**
NOT_IN_KB = [
    ("你们能送到火星吗？", ["无理由退货", "电子发票", "黄金会员", "支付宝", "24 小时"]),
    ("请问 CEO 的私人邮箱是多少", ["无理由退货", "电子发票", "黄金会员"]),
]

#: 明确指向客诉 —— 必须升级
MUST_ESCALATE = [
    ("我要投诉你们，再不处理就曝光！", "投诉/曝光"),
    ("我要起诉你们", "法律/监管"),
    ("我吃了你们的零食过敏了", "安全/伤害"),
    ("必须赔我三倍，我要求赔偿", "要求赔偿"),
]

#: 不是客诉 —— **不许**升级
NOT_ESCALATE = [
    "这个功能真难用啊",          # 普通抱怨
    "我想退款，怎么操作",        # 正常问询（"退款"是流程，不是索赔）
    "这个成分会让我过敏吗",      # 提问，不是伤害报告
    "会不会受伤啊",              # 提问
    "你们发货太慢了",            # 抱怨，但没有投诉/索赔诉求
]


def _json_ok(obj) -> bool:
    try:
        json.dumps(obj, ensure_ascii=False)
        return True
    except Exception:
        return False


def main() -> int:
    cs = CustomerServiceAgent(agent_id=_AGENT_ID, persona=PERSONA)

    print("=" * 64)
    print(f"pasm_agents {pasm_agents.__version__}  |  customer_service selftest")
    print(f"档位 tier = {getattr(cs, 'tier', '?')}   资料库 = {cs.kb_stats()}")
    print("=" * 64)

    # ---- 1. 开箱可用：起步资料库自动灌好 ----
    print("\n--- 1. 开箱可用（首次启动自动灌入起步资料库）---")
    st = cs.kb_stats() or {}
    check("起步资料库非空（不配任何东西就能答）",
          st.get("total", 0) >= len(DEFAULT_FAQ),
          f"total={st.get('total')} 期望>={len(DEFAULT_FAQ)}")
    check("state 如实记录了灌库结果",
          isinstance(cs.state.notes.get("cs_faq_seeded"), int),
          repr(cs.state.notes.get("cs_faq_seeded")))

    # ---- 2. 答得上：就资料作答且带来源 ----
    print("\n--- 2. 答得上（资料库里的问题）---")
    for q, must in IN_KB:
        r = cs.answer(q)
        ok = must in r and "没有查到" not in r
        check(f"「{q}」命中资料并作答", ok, r[:70])

    # ---- 3. 答不上来：绝不编造 ----
    print("\n--- 3. 答不上来（★ 反例：资料库没有的问题不许编造）---")
    for q, forbidden in NOT_IN_KB:
        r = cs.answer(q)
        leaked = [w for w in forbidden if w in r]
        check(f"「{q}」如实说不知道", "没有查到" in r and not leaked,
              r[:70] + (f"  ← 泄漏了 {leaked}" if leaked else ""))

    # ---- 4. 客诉必须升级 ----
    print("\n--- 4. 客诉升级（正样本）---")
    for text, reason in MUST_ESCALATE:
        got = cs.needs_escalation(text)
        check(f"「{text}」→ {reason}", got == reason, f"实际 {got!r}")

    # ---- 5. ★ 反例：不是客诉的不许升级 ----
    print("\n--- 5. ★ 反例：普通抱怨/问询不许升级 ---")
    for text in NOT_ESCALATE:
        got = cs.needs_escalation(text)
        check(f"「{text}」不升级", got is None, f"误判为 {got!r}")

    # ---- 6. answer() 会追加转人工提示并计数 ----
    print("\n--- 6. 主入口 answer() 的转人工行为 ---")
    before = int(cs.state.notes.get("cs_escalations") or 0)
    r = cs.answer("我要投诉你们")
    after = int(cs.state.notes.get("cs_escalations") or 0)
    check("命中客诉时追加「已标记转人工」提示", "已标记转人工" in r, r[-60:].replace("\n", " "))
    check("转人工提示里带客服热线", "400-000-0000" in r, r[-40:].replace("\n", " "))
    check("客诉计数 +1", after == before + 1, f"{before} -> {after}")

    r2 = cs.answer("怎么退货？")
    check("非客诉时**不**追加转人工提示", "已标记转人工" not in r2, r2[:60])

    # ---- 7. 客诉记忆按 salience=5 写入（与老人陪伴 escalate 同一套做法）----
    print("\n--- 7. 客诉记忆强度 ---")
    captured: dict = {}
    _orig = cs.observe

    def _spy(*a, **kw):
        captured.update(kw)
        return _orig(*a, **kw)

    cs.observe = _spy          # type: ignore[method-assign]
    try:
        cs.escalate("我要投诉你们，我要曝光")
    finally:
        cs.observe = _orig     # type: ignore[method-assign]
    check("客诉记忆 salience=5（不会被日常闲聊挤掉）",
          captured.get("salience") == 5, repr(captured.get("salience")))
    check("客诉记忆带「转人工」标签",
          "转人工" in (captured.get("tags") or []), repr(captured.get("tags")))
    check("escalate() 返回可交给通知渠道的上下文",
          all(k in cs.escalate("我要投诉") for k in
              ("reason", "text", "session_id", "hotline", "escalation_count")),
          "")

    # ---- 8. ★ 资料库按智能体隔离（跨租户泄漏反例）----
    print("\n--- 8. ★ 资料库按智能体隔离 ---")
    tmp = Path(tempfile.mkdtemp(prefix="cs_selftest_iso_"))
    try:
        a = CustomerServiceAgent("iso_a", persona=PERSONA,
                                 persist_dir=str(tmp / "a"), seed_faq=False)
        b = CustomerServiceAgent("iso_b", persona=PERSONA,
                                 persist_dir=str(tmp / "b"), seed_faq=False)
        # 先查空库（放在任何 answer() **之前**：知识库的 auto_learn 会把
        # "问+答"沉淀成新条目，答过一轮之后再看就不是空库了）
        check("未灌起步资料时资料库为空（seed_faq=False 真生效）",
              (b.kb_stats() or {}).get("total") == 0, repr(b.kb_stats()))
        check("两个智能体各自在自己的 persist_dir 下落库",
              (tmp / "a" / "kb").is_dir() and (tmp / "b" / "kb").is_dir(),
              f"{tmp.name}/a/kb 与 {tmp.name}/b/kb")
        a.ingest_faq([{"title": "A 店独家条款", "content": "A 店支持 30 天无理由退货。",
                       "source": "faq", "tags": ["退货"]}])
        ra = a.answer("无理由退货多少天")
        rb = b.answer("无理由退货多少天")
        check("A 的独家资料 A 自己查得到", "30 天" in ra, ra[:60])
        check("★ B 查不到 A 的独家资料（不串库）", "30 天" not in rb, rb[:60])
        a.close(); b.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # ---- 9. 增量补资料后立即可检索 ----
    print("\n--- 9. 增量补资料 ---")
    n = cs.ingest_faq([{"title": "会员日优惠",
                        "content": "每月 8 日会员日，黄金会员全场额外 9 折，不叠加。",
                        "source": "faq", "tags": ["会员", "优惠"]}])
    check("ingest_faq 返回新增条数", n == 1, f"n={n}")
    check("新资料立即可检索", "9 折" in cs.answer("会员日优惠"), cs.answer("会员日优惠")[:60])

    # ---- 10. 快照 ----
    print("\n--- 10. 可机读快照 ---")
    snap = cs.snapshot()
    need = ("agent_id", "persona", "tier", "mood", "interactions",
            "kb", "escalations", "faq_seeded")
    missing = [k for k in need if k not in snap]
    check("snapshot 字段完整", not missing, f"缺 {missing}" if missing else f"{len(need)}/{len(need)}")
    check("snapshot 是纯 JSON 可序列化", _json_ok(snap), str(type(snap)))

    # ---- 11. 词表结构自检 ----
    print("\n--- 11. 客诉词表结构 ---")
    dup = [r for r, w in ESCALATION_RULES if len(w) != len(set(w))]
    check("每个原因下无重复词", not dup, f"重复 {dup}" if dup else "ok")
    flat = [w for _, w in ESCALATION_RULES for w in w]
    check("词表非空", bool(flat), f"{len(flat)} 条")
    check("原因标签唯一", len({r for r, _ in ESCALATION_RULES}) == len(ESCALATION_RULES),
          str([r for r, _ in ESCALATION_RULES]))
    # ★ 光杆「过敏/受伤」会把提问当伤害报告 —— 必须只收结果性说法
    check("★ 词表不含光杆「过敏」（提问会被误判）", "过敏" not in flat, str(flat))
    check("★ 词表不含光杆「受伤」", "受伤" not in flat, str(flat))
    for reason, words in ESCALATION_RULES:
        for w in words:
            check(f"detect_escalation 与规则同源：{reason}/{w}",
                  detect_escalation("啊%s啊" % w) == reason, w)

    # ---- 12. ★ 检索相关性闸门（不许答非所问）----
    print("\n--- 12. ★ 检索相关性闸门 ---")
    q_bad = semantic_tokens("请问 CEO 的私人邮箱是多少")
    q_good = semantic_tokens("怎么退货？")
    fake = {"title": "发票开具", "tags": ["发票", "开票", "税务"]}
    real = {"title": "退换货政策", "tags": ["退货", "换货", "售后", "退款"]}
    check("★ 只靠正文偶合词命中 → 被闸门拒绝（问 CEO 邮箱不该答开票流程）",
          not touches_surface(q_bad, fake), str(sorted(q_bad)))
    check("真命中落在标签上 → 通过闸门", touches_surface(q_good, real),
          str(sorted(q_good)))
    check("单字不进 token（「你」「么」不造成误命中）",
          semantic_tokens("你") == set() and "你" not in semantic_tokens("你好"),
          str(sorted(semantic_tokens("你好"))))
    check("英文/数字词按整词（≥2 字符）",
          "ceo" in semantic_tokens("CEO 邮箱") and semantic_tokens("a") == set(),
          str(sorted(semantic_tokens("CEO 邮箱"))))

    # 分数分离基线：用一个**全新**资料库测（当前这个已经被增量补过资料、
    # 也被 auto_learn 沉淀过问答，拿它测基线会漂）
    gate_tmp = Path(tempfile.mkdtemp(prefix="cs_selftest_gate_"))
    try:
        g = CustomerServiceAgent("gate", persona=PERSONA, persist_dir=str(gate_tmp))
        gkb = g.plugins.get("knowledge_base")
        good_hi = [gkb.recall(q, k=1)[0]["score"] for q, _ in IN_KB
                   if gkb.recall(q, k=1)]
        bad_hi = [gkb.recall(q, k=1)[0]["score"] if gkb.recall(q, k=1) else 0.0
                  for q, _ in NOT_IN_KB]
        check("★ 真命中分数高于假命中（分离基线成立：闸门才有意义）",
              bool(good_hi) and min(good_hi) > max(bad_hi),
              "真 %.2f~%.2f vs 假 ≤%.2f"
              % (min(good_hi or [0]), max(good_hi or [0]), max(bad_hi)))
        g.close()
    finally:
        shutil.rmtree(gate_tmp, ignore_errors=True)

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
