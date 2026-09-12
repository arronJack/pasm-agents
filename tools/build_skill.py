"""构建本仓的技能包（4 个：3 个产品智能体 + 1 个验证智能体）。

规则全在基座的 `pasm_skills.build` 里（归档结构、frontmatter、ZIP 自检）——
本仓只声明"我有哪些技能"。这也正是基座存在的意义之一。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pasm_skills.build import ProjectMeta, SkillSpec, run_cli  # noqa: E402

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

if __name__ == "__main__":
    raise SystemExit(run_cli(SKILLS, META, root=ROOT))
