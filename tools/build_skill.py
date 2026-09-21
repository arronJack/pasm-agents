"""构建本仓的技能包（5 个：4 个产品智能体 + 1 个验证智能体）。

规则全在基座的 `pasm_skills.build` 里（归档结构、frontmatter、ZIP 自检）——
本仓只声明"我有哪些技能"。这也正是基座存在的意义之一。

三种产物（`skill/SKILL.*.body.md` 是唯一正文真相源）
----------------------------------------------------
1. `<仓>-dist/zip-root/<name>/SKILL.md` —— **WorkBuddy 开放平台**要的形态；
2. `<仓>-dist/slug-dir/<name>/SKILL.md` —— **ClawHub** 要的形态（一层 slug 目录）；
3. `skills/<name>/SKILL.md`（**就在本仓里、要提交**）—— **Agent Skills 开放生态**
   （`npx skills add arronJack/pasm-agents` → skills.sh 索引 → Claude Code / Cursor /
   Cline / Copilot / Gemini CLI 等约 48 个 agent 表面）。

第 3 种为什么必须落在仓库里：`npx skills add <owner/repo>` 是**从 GitHub 仓库读文件**的，
它只认 `skills/<name>/SKILL.md` 这类约定路径；而 `skill/SKILL.*.body.md`
**它看不见**（文件名不是 `SKILL.md`）。所以前两种形态发得再对，这个渠道也是 0。

改正文后忘了重新生成 `skills/` 就会**静默发旧内容** —— 所以有 `--check-repo`：
它比对"仓库里已提交的 `skills/`"与"按当前正文+版本号应当生成的内容"，不一致就退出 1。
发版前跑一次，或交给 CI。**别手改 `skills/` 下的文件**（改正文，然后 `--repo` 重新生成）。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pasm_skills.build import (  # noqa: E402
    ProjectMeta, SkillSpec, ind, read_version, run_cli,
)

META = ProjectMeta(
    author="arronzheng",
    homepage="https://github.com/arronJack/pasm-agents",
    repository="https://gitee.com/arronzheng/pasm-agents",
)

SKILLS = [
    SkillSpec(
        name="pasm-npc",
        body_file="SKILL.npc.body.md",
        display_name_zh="PASM 游戏 NPC 智能体",
        display_name_en="PASM game NPC agent",
        desc_zh=(
            "PASM 游戏 NPC 智能体——给游戏装一个有记忆、有情绪、会被玩家反馈塑形的 NPC。"
            "当需要 NPC 记住玩家做过什么、同一句话在不同情绪下说法不同、"
            "行为偏好能被玩家长期塑形（夸它多做 / 凶它少做），"
            "或要给现有游戏后接一层认知内核时使用。"
            "零 LLM 依赖、断网可用、状态持久化到 ~/.pasm-agents/<id>/。"
            "关键词：PASM、游戏 NPC、NpcAgent、记忆、情绪、人格、行为权重、salience、"
            "长期陪伴、离线智能体。"
        ),
        desc_en=(
            "PASM game NPC agent - drop an NPC into your game that actually remembers the player, "
            "has emotion, and gets shaped by player feedback over time. "
            "Use when NPCs must recall what the player did, vary a line by mood, "
            "or shift behavioural preference through long-term praise/scolding, "
            "or when you want to bolt a cognitive core onto an existing game. "
            "Zero LLM dependency, offline-runnable, state persists to ~/.pasm-agents/<id>/. "
            "Keywords: pasm, npc, game agent, memory, emotion, persona, salience, offline."
        ),
        plain_desc=(
            "Game NPC agents built on the PASM cognitive engine. NpcAgent gives you an NPC with "
            "persistent memory (salience-aware eviction so landmark events are never pushed out by "
            "trivia), persona-weighted action selection (temper/energy/play drive the baseline), and "
            "feedback-driven shaping - praise or scold a SPECIFIC action and the behaviour "
            "distribution actually moves. Emotion modulates replies. Growth stages unlock new actions "
            "(wave/hop/peek -> ball -> dance/spin -> think). Zero LLM dependency, offline-runnable, "
            "state persists to ~/.pasm-agents/<id>/. Tier label (light/core/bionic) exposed on every "
            "agent so callers always know which engine path is live."
        ),
        plain_category="agents",
        plain_tags=["ai-agents", "pasm", "npc", "game", "memory", "emotion"],
        plain_license="MIT-0",
    ),
    SkillSpec(
        name="pasm-companion",
        body_file="SKILL.companion.body.md",
        display_name_zh="PASM 老人陪伴智能体",
        display_name_en="PASM elderly companion agent",
        desc_zh=(
            "PASM 老人陪伴智能体——给独居老人做关键事实记忆、用药提醒与危机升级。"
            "当需要长期记住老人的用药/过敏/家人/本人信息且不允许被闲聊挤掉、"
            "需要按时提醒吃药、需要识别危机表达（胸闷/摔倒/意识异常/轻生念头）"
            "并升级到紧急联系人时使用。关键事实走标签直查，命中率 100%。"
            "零 LLM 依赖、断网可用。注意：不是医疗器械，不替代任何医疗或急救服务。"
            "关键词：PASM、老人陪伴、ElderlyCompanion、关键事实、用药提醒、危机升级、"
            "紧急联系人、独居老人、离线陪伴。"
        ),
        desc_en=(
            "PASM elderly companion agent - key-fact memory, medication reminders and crisis "
            "escalation for people living alone. Use when medications/allergies/family details must "
            "be remembered with 100% label-based retrieval and must never be evicted by small talk, "
            "when medication times need prompting, or when crisis phrases (chest tightness, falls, "
            "altered consciousness, self-harm ideation) must be escalated to an emergency contact. "
            "Zero LLM dependency, offline-runnable. NOT a medical device; does not replace medical or "
            "emergency services. Keywords: pasm, elderly companion, key facts, medication reminder, "
            "crisis escalation, emergency contact, offline."
        ),
        plain_desc=(
            "Elderly companion agents built on the PASM cognitive engine. ElderlyCompanion stores "
            "key facts (medication, allergies, family, self) at salience 5 on first start and retrieves "
            "them by label at 100% hit rate - it can never forget what the user is allergic to. "
            "detect_crisis() recognises four crisis classes (chest/cardiac, fall/trauma, altered "
            "consciousness, self-harm) and escalate() writes an unevictable emergency memory and "
            "returns the escalation context (contact, suggested action, snapshot) for your notifier. "
            "due_medication() does time-based medication prompting. Zero LLM dependency, "
            "offline-runnable. NOT a medical device. Keywords: pasm, elderly care, companion, "
            "medication, crisis escalation, memory, offline."
        ),
        plain_category="agents",
        plain_tags=["ai-agents", "pasm", "elderly-care", "companion", "safety", "memory"],
        plain_license="MIT-0",
    ),
    SkillSpec(
        name="pasm-tutor",
        body_file="SKILL.tutor.body.md",
        display_name_zh="PASM 学习陪伴智能体",
        display_name_en="PASM learning tutor agent",
        desc_zh=(
            "PASM 学习陪伴智能体——按知识点追踪掌握度、最弱优先选题、鼓励式对话。"
            "当需要追踪每个知识点的掌握度而不是只记总分、需要自适应推荐最该练的题、"
            "需要鼓励式回复而不是打击式反馈、或需要一份可机读的学情快照"
            "接进画像/报表/家长端时使用。report() 用 EMA 平滑，snapshot() 输出纯 JSON。"
            "零 LLM 依赖、断网可用。关键词：PASM、学习陪伴、LearningTutor、掌握度、"
            "薄弱点定位、自适应选题、学情快照、画像、错题。"
        ),
        desc_en=(
            "PASM learning tutor agent - per-topic mastery tracking, weakest-first question "
            "selection and encouraging dialogue. Use when you need mastery per knowledge point rather "
            "than a single total score, adaptive next-question choice, non-discouraging feedback, or a "
            "machine-readable learning snapshot to feed into a profile/report/parent portal. "
            "report() applies EMA smoothing; snapshot() returns plain JSON (mastery/weakest/average). "
            "Zero LLM dependency, offline-runnable. Keywords: pasm, tutor, learning companion, "
            "mastery, weakest-topic, adaptive practice, student profile, offline."
        ),
        plain_desc=(
            "Learning tutor agents built on the PASM cognitive engine. LearningTutor tracks per-topic "
            "mastery with an EMA (single bad attempt does not crater it), selects the weakest topic "
            "next (with 20% jitter to avoid grinding one topic), replies in an encouraging template "
            "that admits difficulty and offers the smallest actionable step, and exports a stable "
            "machine-readable snapshot (mastery / weakest / average / history_size / tier) for "
            "downstream profile engines. Wrong answers are stored as salience-3 memories so related "
            "mistakes can be recalled. Zero LLM dependency, offline-runnable. "
            "Keywords: pasm, tutor, mastery, adaptive practice, student profile, offline."
        ),
        plain_category="agents",
        plain_tags=["ai-agents", "pasm", "tutor", "education", "mastery", "offline"],
        plain_license="MIT-0",
    ),
    SkillSpec(
        name="pasm-cs-agent",
        body_file="SKILL.cs-agent.body.md",
        display_name_zh="PASM 智能客服智能体",
        display_name_en="PASM customer-service agent",
        desc_zh=(
            "PASM 智能客服智能体——就自己的资料作答、答不上来如实说、客诉自动转人工。"
            "当需要基于自有 FAQ/产品文档回答客户问题、需要答不上来时如实说明"
            "而不是编造、需要自动识别客诉（投诉曝光/法律监管/安全事故/要求赔偿）"
            "并交出转人工上下文、或需要把客服接成程序内调用/HTTP 接口/站点挂件/大模型平台工具时使用。"
            "资料库可增量喂养并去重，按智能体隔离不串库，可选接任意大模型。"
            "关键词：PASM、智能客服、CustomerServiceAgent、资料库、FAQ、客诉转人工、"
            "知识库、多租户隔离、MCP、离线可用。"
        ),
        desc_en=(
            "PASM customer-service agent - answers strictly from your own knowledge base, says "
            "\"I don't know\" instead of making things up, and auto-escalates complaints to a human. "
            "Use when a bot must answer from your FAQ/product docs, must admit ignorance rather than "
            "hallucinate, must detect complaint classes (public complaint, legal, safety incident, "
            "damages claim) and hand over escalation context, or when you need customer service as "
            "an in-process call, HTTP endpoint, site widget or LLM-platform tool. "
            "Incremental, de-duplicated knowledge ingestion; per-agent KB isolation (no cross-tenant "
            "leakage); vendor-neutral optional LLM. Keywords: pasm, customer service, knowledge base, "
            "FAQ, escalation, multi-tenant isolation, MCP, offline."
        ),
        plain_desc=(
            "Customer-service agents built on the PASM cognitive engine. CustomerServiceAgent answers "
            "only from knowledge facts (entries carrying a source) and applies a relevance gate that "
            "requires the match to land on the entry's title or tags - so it refuses to answer instead "
            "of answering the wrong thing (measured: true hits score 6.0-24.5 while a bogus hit via one "
            "incidental word scored 2.29). Complaint phrases in four classes are detected and escalated "
            "into salience-5 memory that small talk can never evict, returning escalation context for "
            "your notifier. Knowledge is ingested incrementally with content-fingerprint de-duplication, "
            "and each agent gets its own KB directory so multiple tenants on one host cannot leak into "
            "each other. Optional vendor-neutral LLM with automatic fallback to KB answering. "
            "Keywords: pasm, customer service, knowledge base, FAQ, escalation, offline."
        ),
        plain_category="agents",
        plain_tags=["ai-agents", "pasm", "customer-service", "knowledge-base", "support", "offline"],
        plain_license="MIT-0",
    ),
    SkillSpec(
        name="pasm-longterm-verify",
        body_file="SKILL.verify.body.md",
        display_name_zh="PASM 长期验证智能体",
        display_name_en="PASM long-term verification agents",
        desc_zh=(
            "PASM 长期验证智能体工坊——用可重复运行的智能体回答「认知引擎跑久了还是好的吗」。"
            "当需要验证记忆会不会丢、情绪会不会漂、行为会不会僵化、长期陪伴功能能不能上、"
            "或要在 CI/定时任务里对认知引擎做结构与行为双重体检时使用。"
            "关键词：PASM、长期验证、智能体、记忆保持、情绪漂移、人格饱和、遗忘曲线、"
            "soak 长跑、回归基线、parity 校验、core-verifier、npc-lifelong、companion-elderly、"
            "study-tutor、soak-longrun。"
        ),
        desc_en=(
            "PASM long-term verification agents - repeatable, dependency-free agents that answer "
            "\"is the cognitive engine still healthy after long runs?\". Use when checking memory "
            "retention, emotion drift, behavioural rigidity, long-run degradation, cross-repo parity, "
            "or when adding structural + behavioural health checks to CI."
        ),
        plain_desc=(
            "Long-term verification agents for the PASM cognitive engine. Answers \"is it still healthy "
            "after long runs?\" with repeatable, stdlib-only checks: memory retention and salience-aware "
            "eviction, emotion drift, behavioural entropy collapse, persona saturation, forgetting curve, "
            "6000-step soak degradation, and cross-repo parity. Scenarios drive the real engine in an "
            "isolated subprocess and emit JSON-archivable, baseline-diffable findings."
        ),
        plain_category="developer-tools",
        plain_tags=["testing", "verification", "ai-agents", "memory", "long-running"],
        plain_license="MIT-0",
    ),
]

# ============================================================ 仓库内 skills/（开放生态）
REPO_SKILLS_DIR = ROOT / "skills"


def _repo_frontmatter(spec: SkillSpec, version: str) -> str:
    """写给 Agent Skills 开放生态的 frontmatter。

    刻意**比 zip-root 精简**：该生态只要求 `name` + `description`，
    多塞平台专属字段反而会让别的 agent 解析器犯迷糊。
    `description` 用**英文** —— 这个生态的检索以英文为主
    （中文用户走 WorkBuddy / ClawHub 那两条线）。
    `license` 用 **MIT**（= 本仓 LICENSE），不是 ClawHub 强制的 MIT-0：
    这里是自家公开仓，没有"强制 MIT-0"的外部约束。
    """
    return "\n".join([
        "---",
        "name: %s" % spec.name,
        "description: %s" % ind(spec.desc_en),
        "version: %s" % version,
        "license: MIT",
        "author: %s" % META.author,
        "homepage: %s" % META.homepage,
        "repository: %s" % META.repository,
        "---",
        "",
    ])


def _repo_skill_files(version: str):
    """算出 `skills/<name>/SKILL.md` 应有的内容。返回 [(路径, 内容), ...]。"""
    out = []
    for spec in SKILLS:
        body_path = ROOT / "skill" / spec.body_file
        body = body_path.read_text(encoding="utf-8")
        out.append((REPO_SKILLS_DIR / spec.name / "SKILL.md",
                    _repo_frontmatter(spec, version) + body))
    return out


def write_repo_skills() -> int:
    """生成 `skills/<name>/SKILL.md`（要提交进仓库）。"""
    version = read_version(ROOT)
    for dest, content in _repo_skill_files(version):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        print("[OK] 已生成 %s" % dest.relative_to(ROOT))
    return 0


def check_repo_skills() -> int:
    """校验已提交的 `skills/` 是否与正文/版本号同步（陈旧即失败）。"""
    version = read_version(ROOT)
    stale, missing = [], []
    for dest, content in _repo_skill_files(version):
        rel = dest.relative_to(ROOT)
        if not dest.exists():
            missing.append(str(rel))
            continue
        if dest.read_text(encoding="utf-8").replace("\r\n", "\n") != content.replace("\r\n", "\n"):
            stale.append(str(rel))
    if missing or stale:
        for n in missing:
            print("[FAIL] 缺失：%s（跑 tools/build_skill.py --repo 生成）" % n)
        for n in stale:
            print("[FAIL] 陈旧：%s（正文或版本号已变，跑 tools/build_skill.py --repo 重新生成）" % n)
        print("[FAIL] 仓库内 skills/ 与源不同步 —— 直接提交会让开放生态拿到旧内容。")
        return 1
    print("[OK] 仓库内 skills/ 与正文/版本号同步（%d 个技能）" % len(SKILLS))
    return 0


if __name__ == "__main__":
    # 先摘掉本脚本自己的两个开关，剩下的原样交给基座的 run_cli
    _argv = sys.argv[1:]
    _do_repo = "--repo" in _argv
    _do_check = "--check-repo" in _argv
    _argv = [a for a in _argv if a not in ("--repo", "--check-repo")]

    _rc = 0
    if _do_repo:
        _rc |= write_repo_skills()
    if _do_check:
        _rc |= check_repo_skills()
    if _argv:                      # 还有构建参数才跑打包（避免 --repo 单独用时重打包）
        _rc |= run_cli(SKILLS, META, root=ROOT, argv=_argv)
    elif not (_do_repo or _do_check):
        _rc |= run_cli(SKILLS, META, root=ROOT, argv=[])
    raise SystemExit(_rc)
