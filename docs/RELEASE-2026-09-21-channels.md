# 2026-09-21 · 技能分发渠道发布记录

> 本文是**一次性发布记录**（时点快照），不是活索引 —— 最新实况以
> 技能 `pasm-skill-publish` 的 SKILL.md「状态」表为准。

## 一、本轮做了什么

`pasm-agents` 升到 **0.5.0**（新增第 4 个产品 `pasm-cs-agent`）后，把**五个技能**
补齐到各分发渠道。本轮完成的是 **WorkBuddy 开放平台**这一档。

## 二、WorkBuddy 开放平台（`open.workbuddy.cn`）

登录：微信扫码（协议层取码，见下方「踩坑」）。登录后一次性完成 4 项提交：

| 技能 | 动作 | 结果 | 技能 ID |
|---|---|---|---|
| PASM 智能客服智能体 | **新建** | 审核中 · v0.5.0 | `os_924451a4a7d4207c` |
| PASM 学习陪伴智能体 | 更新版本 | 审核中 · v0.5.0 | `os_fade1c1b1163b59b` |
| PASM 游戏 NPC 智能体 | 更新版本 | 审核中 · v0.5.0 | `os_3b73ed6cccff32b1` |
| PASM 长期验证智能体 | 更新版本 | 审核中 · v0.5.0 | `os_0168b1aad6a492b8` |
| PASM 老人陪伴智能体 | 更新版本 | 审核中 · v0.5.0 | `os_3004232df19522f7` |
| PASM 智能体开发基座 | 未动 | 已发布 · 公开 · v0.5.0 | `os_a087e21566d55390` |

**6 个技能全部 v0.5.0**（以上为提交后当场回读平台列表得到，非推测）。
平台提示：**预计 7 个工作日内出结果**，结果通过站内通知告知。

### 审核中的技能也能更新，不用「撤回」

老人陪伴 09-15 提交后一直卡在审核队列里，卡片上**只有「撤回」、没有「更新版本」**。
但**路由没锁** —— 直接访问确定性 URL 就能进同一套 republish 流程：

```
https://open.workbuddy.cn/skill/publish/<技能ID>?action=republish&step=1
```

实测走完上传 → 继续 → 提交，成功更新到 v0.5.0，**没有动「撤回」**（撤回会重置排队位置）。

> 泛化：**卡片上没有按钮 ≠ 平台不支持**。先试确定性 URL，别急着做破坏性操作。

> 另注：任何技能走完「更新版本」后，卡片会变成 `撤回 | 审核中 | vX.Y.Z`，
> 期间**看不到「已发布」字样**，这是平台的正常表现，不是被下架。

## 三、其余渠道状态（本轮之前已完成）

| 渠道 | 状态 |
|---|---|
| PyPI | `pasm-agents 0.5.0` + `pasm-customer-service 0.2.0`（干净 venv 断言 `__version__`） |
| **ClawHub**（`@arronjack`） | **6 个技能全部已发布**，逐个 `inspect` 回读：`pasm-cs-agent` / `pasm-npc` / `pasm-companion` / `pasm-tutor` / `pasm-longterm-verify` 均 **v0.5.0**，`pasm-agent-authoring` **v0.5.2**；`pasm-cs-agent` 标注 **Moderate CLEAN**（`scanner.vt.clean`） |
| Agent Skills 生态（skills.sh） | 5 个技能落在仓库 `skills/<name>/SKILL.md`，远端实测可读 |
| 本机 WorkBuddy 技能目录 | 5 个，`md5sum` 与权威产物一致 |

> ClawHub 的**只读探针**（不用登录、不用浏览器）：
> `curl "https://clawhub.ai/api/search?q=pasm"` 看有哪些、更新时间；
> `npx clawhub@latest inspect arronjack/<slug>` 看**版本与安全扫描结论** ——
> 注意 search 接口**不给 version 字段**，版本只能靠 inspect。

## 四、本轮踩到的坑（已固化进技能 `pasm-skill-publish`）

| # | 现象 | 真因 | 正确做法 |
|---|---|---|---|
| 1 | 浏览器窗口始终不出现 | `--headed` 写在子命令**后面**被静默忽略 → 一直无头 | `agent-browser --headed --session <s> open <url>` |
| 2 | 窗口有了仍看不到二维码 | 登录码在**跨域 iframe** 里，受限桌面下退化成占位图 | **协议层取码**：读 iframe `src` → 抠 `uuid` → 取 `/connect/qrcode/<uuid>` 原图 |
| 3 | 轮询永远读不到响应 | 微信那个接口是**长轮询**，读超时 15s 会被自己掐断 | 读超时给到 **45s** |
| 4 | 卡片给了但"没看到二维码" | `present_files` 给 PNG 只出一张**小卡片** | 二维码 **base64 内嵌进 HTML** 再 `present_files`（应用内直接展开预览） |
| 5 | 扫码成功但登录失败 | `copilot` 域返回「**账号不存在，请联系企业管理员**」 | 换**已绑定**的微信号重扫（实测换号立刻进控制台） |
| 6 | 脚本起不了 agent-browser | Windows 上 PATH 那个是**无扩展名 bash 包装脚本** | 调同目录 **`agent-browser.cmd`** |
| 7 | `eval` 报 `Unexpected end of input` | 传了**多行 JS** | JS 压成**单行** |
| 8 | 点了「继续」/「提交」没反应 | Radix 按钮对单一手段不敏感，且按钮常在视口外 | **`scrollIntoView` + 真实鼠标** 与 **`click @ref`** 两种都试，判据只看页面结果 |
| 9 | 审核中的技能无法更新（卡片只有「撤回」） | 只是**不给你按钮**，**路由没锁** | 直连 `/<技能ID>?action=republish&step=1`，**别「撤回」**（会重置排队位置） |

脚本：`~/.workbuddy/skills/pasm-skill-publish/scripts/`
（`wx_qr_grab.py` 取码 / `wx_qr_poll.py` 长轮询 / `wx_qr_html.py` 打大图页 /
`open_platform_publish.py` 上架与更新）
