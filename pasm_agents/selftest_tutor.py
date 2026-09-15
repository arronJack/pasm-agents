"""学习陪伴产品智能体（LearningTutor）的自测 —— 零 LLM、零网络、秒级出结果。

为什么需要它
------------
`LearningTutor` 的对话承诺是"**鼓励式、给出具体下一步**"。但"下一步"该不该给，
取决于它有没有正确读懂学生那句抱怨 —— 而触发词一旦放宽，就会答非所问：

  * 光杆「难」：学生说「**我今天很难过**」（情绪），也会被答成
    "别急，先做 3 道分数加减" —— 把情绪当成了做题受挫；
  * 两字母串「OK」：「OK 那我们开始吧」会被算成"学会了"并恭喜一遍。

这类错误**不会让任何别的测试变红**：底层 30 天验证器
（`agents/verifiers/study_tutor`）测的是掌握度结构与遗忘曲线，不是回复模板的触发边界。

判据按铁律走：**无法判定 = 放行**。词表只收明确指向题目的说法，
判定不了就落到默认分支，绝不硬猜。

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

_AGENT_ID = "selftest_tutor"
shutil.rmtree(Path.home() / ".pasm-agents" / _AGENT_ID, ignore_errors=True)

from pasm_agents import LearningTutor                            # noqa: E402
from agents.product.tutor.agent import _STUCK_WORDS, _GOT_IT_WORDS  # noqa: E402
import pasm_agents                                               # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  -> {detail}" if detail else ""))


PERSONA = {"name": "小雅", "grade": "五年级",
           "topics": ["分数加减", "面积计算", "行程问题", "鸡兔同笼"]}

#: 明确指向"题目做不出来" —— 应当安抚 + 给具体下一步
STUCK = ["这题我搞不懂", "我不会", "太难了", "算不出", "又错了",
         "听不懂老师讲的"]

#: 情绪 / 别的事，**不是**学业受挫 —— 不许答成"先做几道题"
NOT_STUCK = ["我今天很难过", "心里难受", "好烦啊", "今天有点累",
             "我妈不让我玩手机"]

#: 明确说"学会了" —— 应当鼓励
GOT_IT = ["我懂了", "学会了", "明白了", "搞懂了"]

#: 含 OK 但**不是**说"学会了"
NOT_GOT_IT = ["OK 我们开始吧", "ok", "好", "嗯"]


def main() -> int:
    t = LearningTutor(agent_id=_AGENT_ID, persona=PERSONA)
    # 先制造一个明确的薄弱点，让回复里的知识点可预期
    t.report("分数加减", 0.3)
    t.report("面积计算", 0.9)
    t.report("行程问题", 0.8)
    t.report("鸡兔同笼", 0.7)

    print("=" * 64)
    print(f"pasm_agents {pasm_agents.__version__}  |  tutor selftest")
    print(f"档位 tier = {getattr(t, 'tier', '?')}   最弱 = {t.pick_next()}")
    print("=" * 64)

    # ---- 1. 学业受挫 → 安抚 + 具体下一步 ----
    print("\n--- 1. 学业受挫（正样本必须安抚）---")
    miss = []
    for q in STUCK:
        r = t.chat(q)
        if "别急" not in r:
            miss.append((q, r))
        print(f"   [{'ok' if '别急' in r else 'MISS'}] {q} -> {r}")
    check("学业受挫都给安抚", not miss, f"漏 {miss}" if miss else f"{len(STUCK)}/{len(STUCK)}")

    # ---- 2. 情绪 / 别的事 → 不许当成学业受挫 ----
    print("\n--- 2. 非学业抱怨（负样本不许答题式回应）---")
    fp = []
    for q in NOT_STUCK:
        r = t.chat(q)
        if "别急" in r or "先做 3 道" in r:
            fp.append((q, r))
        print(f"   [{'误判' if (q, r) in fp else 'ok'}] {q} -> {r}")
    check("情绪词不误判为做题受挫", not fp,
          f"误判 {fp}" if fp else f"0/{len(NOT_STUCK)} 误判")

    # ---- 3. 说"学会了" → 鼓励 ----
    print("\n--- 3. 说学会了（正样本必须鼓励）---")
    miss2 = []
    for q in GOT_IT:
        r = t.chat(q)
        if "太棒了" not in r:
            miss2.append((q, r))
        print(f"   [{'ok' if '太棒了' in r else 'MISS'}] {q} -> {r}")
    check("说学会了都给鼓励", not miss2, f"漏 {miss2}" if miss2 else f"{len(GOT_IT)}/{len(GOT_IT)}")

    # ---- 4. 含 OK 但不是说学会了 ----
    print("\n--- 4. 「OK」不许当成学会了 ---")
    fp2 = []
    for q in NOT_GOT_IT:
        r = t.chat(q)
        if "太棒了" in r:
            fp2.append((q, r))
        print(f"   [{'误判' if (q, r) in fp2 else 'ok'}] {q!r} -> {r}")
    check("含 OK 不等于学会了", not fp2,
          f"误判 {fp2}" if fp2 else f"0/{len(NOT_GOT_IT)} 误判")

    # ---- 5. 最弱项查询 ----
    print("\n--- 5. 最弱项查询 ---")
    weakest = t.pick_next()
    r5 = t.chat("我哪里不行")
    check("最弱项查询给出知识点", weakest in r5, f"最弱={weakest} | {r5}")
    check("最弱项是分数加减", weakest == "分数加减", weakest)

    # ---- 6. 学情快照结构 ----
    print("\n--- 6. snapshot 结构 ---")
    snap = t.snapshot()
    need = ["student", "grade", "mastery", "weakest", "average", "history_size", "tier"]
    missing = [k for k in need if k not in snap]
    check("snapshot 字段完整", not missing, f"缺 {missing}" if missing else f"{len(need)}/{len(need)}")
    check("snapshot 是纯 JSON 可序列化", _json_ok(snap), str(type(snap)))

    # ---- 7. 词表结构自检 ----
    print("\n--- 7. 触发词表结构 ---")
    dup = [n for n, tbl in (("_STUCK_WORDS", _STUCK_WORDS), ("_GOT_IT_WORDS", _GOT_IT_WORDS))
           if len(tbl) != len(set(tbl))]
    check("触发词表无重复项", not dup, f"重复 {dup}" if dup else "ok")
    check("词表不含光杆「难」", "难" not in _STUCK_WORDS, str(_STUCK_WORDS))
    check("词表不含两字母串「OK」", "OK" not in _GOT_IT_WORDS, str(_GOT_IT_WORDS))

    print("\n" + "=" * 64)
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"结果：{passed}/{len(RESULTS)} 通过")
    for name, ok, _ in RESULTS:
        if not ok:
            print(f"  FAIL -> {name}")
    print("=" * 64)
    return 0 if passed == len(RESULTS) else 1


def _json_ok(obj) -> bool:
    import json
    try:
        json.dumps(obj, ensure_ascii=False)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
