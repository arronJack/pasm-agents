# skill/ —— 技能正文与打包（维护者向）

本目录存放**技能正文**，`tools/build_skill.py` 把正文拼上 frontmatter 生成可直接上传的技能包。

## 为什么正文单独放

正文只有一份，而两个平台的元数据要求不同。分开维护必然漂移，所以拆开：

```
skill/SKILL.<name>.body.md        正文（本目录，不含 frontmatter）
        │
        ├─ tools/build_skill.py 拼上 zip-root 形态 frontmatter  → SKILL.md 落在 ZIP 根目录
        └─ tools/build_skill.py 拼上 slug-dir 形态 frontmatter  → <slug>/SKILL.md
```

形态名按**归档结构**取，不按平台名 —— 平台会变，结构不会。

## ⚠️ 正文里不许出现的东西

这几条都是踩过的坑，改正文时请守住：

1. **不许写"本文件是 SKILL.md 的正文部分…"之类的维护者注释。**
   早期四份正文都带了这句，结果**原样出现在平台上用户看到的技能页里**。
   维护者说明写在本文件，不写进正文。
2. **不许让用户去 `pasm-skills` 仓找智能体。**
   2026-09-12 拆仓后基座**刻意不含任何智能体**，那条指令必然失败。
   智能体在本仓（`pasm-agents`）。已有自动检查兜底：
   ```bash
   python tools/check_skill_docs.py     # 退出码 1 = 有正文写错了
   ```
3. **安装方式以 `pip install pasm-agents` 为主**，`git clone` 只作为"没有 PyPI 环境时"的备选，
   并且必须写清**两个仓都要**。
4. **引用的 API 必须真实存在**。改正文前先跑一遍：
   ```bash
   python tools/check_skill_docs.py && python -c "from pasm_agents import NpcAgent, ElderlyCompanion, LearningTutor; print('ok')"
   ```

## 现有正文

| 正文 | 技能名 | 说明 |
|---|---|---|
| `SKILL.npc.body.md` | `pasm-npc` | 游戏 NPC：记忆 / 情绪 / 反馈塑形 |
| `SKILL.companion.body.md` | `pasm-companion` | 老人陪伴：关键事实 / 用药提醒 / 危机升级 |
| `SKILL.tutor.body.md` | `pasm-tutor` | 学习陪伴：掌握度 / 自适应选题 / 学情导出 |
| `SKILL.verify.body.md` | `pasm-longterm-verify` | 验证层：7 个智能体对认知引擎做结构与行为体检 |

## 加一个新技能

1. 写正文 `skill/SKILL.<name>.body.md`
2. 在 `tools/build_skill.py` 的 `SKILLS` 里加一条 `SkillSpec`
   （技能名 + 正文文件名 + 中英描述 + 归档形态元信息）
3. 打包并自检：
   ```bash
   python tools/build_skill.py --zip --clean
   # 校验产物（默认落在本仓的兄弟目录 <仓的父目录>/pasm-agents-dist/）
   python -c "import glob,os,zipfile,sys; d=os.path.join(os.path.dirname(os.getcwd()),'pasm-agents-dist'); [print(os.path.basename(z), zipfile.ZipFile(z).namelist()) for z in sorted(glob.glob(os.path.join(d,'*.zip')))]"
   # 每个都期望 ['SKILL.md']
   ```

## 打包产物去哪

`<仓的父目录>/pasm-agents-dist/`（在仓库外，即与 `pasm-agents` 同级）：
`zip-root/<name>/SKILL.md`、`slug-dir/<name>/SKILL.md` 与根目录下的 ZIP。
路径由 `pasm_skills.build.build_all()` 推导（`root.parent / "<仓名>-dist"`），**不写死盘符**。
上传步骤见该目录下的 `UPLOAD-CHECKLIST.md`。
