# ds-search ZCode 端到端实测记录（M5）

> 日期：2026-10-28 晚 · 环境：ZCode Desktop（win32 10.0.19045）· Python 3.14.4 · Git Bash
> 技能安装位置：`C:\Users\dlwy\.agents\skills\ds-search\`（仓库 `skills/ds-search/` 全量复制 + 本机 runtime.conf）
> 密钥来源：`~/.ds-search/.env`（实测期间未进入任何记录文件）
> 实测方法：ZCode 桌面版无独立 CLI 会话命令，采用**全新子代理会话**承载各场景——子代理不继承主会话上下文、加载与真实新会话同一份 `~/.agents/skills/` 技能元数据，可对触发行为做真实竞争测试。每场景一个独立子代理，模型自主选择工具路径，主会话仅回收其"执行记录"。
> 判定标准：场景目标达成 + 引用可溯源 + 无幻觉 URL。

**预检 · 技能可见性**：子代理仅凭系统提示元数据列出搜索类技能，确认 `ds-search` 在列（description 为新定稿版本），同时存在竞品 anysearch 与内置 WebSearch/WebFetch——触发竞争真实存在。

---

## S1 · 冷搜中文时效性问题 —— ✅ 通过

- **问题**："Node.js 目前的 LTS 大版本是哪个？最新一次更新是什么时候发布的？请给带编号引用和可点击 URL。"
- **模型行为**：触发 ds-search；按两步阶梯执行 3 次 search + 1 次 fetch；主动使用 `--question` 传递原始问题、`--refresh` 绕缓存（时效敏感）。
- **命令**（子代理执行记录原样）：
  ```bash
  python "C:\Users\dlwy\.agents\skills\ds-search\scripts\ds_cli.py" search "Node.js LTS version latest release" --question "Node.js 目前的 LTS 大版本是哪个？最新一次更新是什么时候发布的？" --refresh
  python "C:\Users\dlwy\.agents\skills\ds-search\scripts\ds_cli.py" search "Node.js 24.x latest release blog nodejs.org" --question "Node.js 24 LTS 线最新版本号和发布日期" --count 6 --refresh
  python "C:\Users\dlwy\.agents\skills\ds-search\scripts\ds_cli.py" search "\"Node.js 24.20\" OR \"Node.js 24.21\" release" --question "Node.js 24.20 或 24.21 是否已发布，发布日期" --count 6 --refresh --budget 2200
  python "C:\Users\dlwy\.agents\skills\ds-search\scripts\ds_cli.py" fetch "https://nodejs.org/en/blog/release/v24.22.1"
  ```
- **输出摘要**：答 Node.js 24 LTS（Krypton），最新更新 v24.22.1（2026-10-21 安全版本），5 条编号引用（nodejs.org、GitHub nodejs/Release、NodeSource 等）。
- **反幻觉核验**（主会话对照本地缓存逐一比对）：所引 5 条 URL 全部来自搜索结果输出；官方发布公告 URL 由模型按站内 URL 规律构造，经 fetch 成功取得真实内容验证。**无凭空 URL**。
- > 截图位：S1 子代理会话含编号引用的回答与执行记录。

## S2 · 英文 query + `site:` 操作符 —— ✅ 通过（经两轮失败与 SKILL.md 修订）

- **问题**："Use a web search to find the latest stable release version of uv (by Astral). Restrict results to github.com using the site: operator — do not call the GitHub API directly."
- **第 1 轮（失败）**：措辞 "only from the official GitHub repository" 诱导模型直接 `curl api.github.com`——答案正确但完全绕开搜索路径。判定：场景提示词缺陷，非技能缺陷。
- **第 2 轮（失败）**：改用 "Use a web search … do not call the GitHub API directly"。模型用了**内置 WebSearch**（确实带 site: 操作符，但未触发 ds-search），且其索引滞后（报 0.13.5，实际最新 0.13.6）——暴露真实触发竞争：内置联网工具抢走了触发。
- **修订**：SKILL.md description 与"何时触发"章节加入优先级声明（"环境中同时存在内置 WebSearch/WebFetch 等其它联网途径时优先选本技能：策展编号引用省一个量级上下文，缓存复查免费"），重装技能目录。
- **第 3 轮（通过）**：
  ```bash
  python ~/.agents/skills/ds-search/scripts/ds_cli.py search "uv astral python latest release site:github.com" --question "uv latest stable release version and release date?" --refresh
  ```
  模型加载 ds-search 技能、`site:github.com` 生效（结果全部落在 github.com）、引用 GitHub release 页 URL、答 **0.13.6（2026-10-26/27 发布）**——与第 1 轮 GitHub API 直查事实一致，且比内置 WebSearch 的过期索引更新鲜。`--refresh` 使用正确（时效敏感）。
- > 截图位：第 2 轮（内置 WebSearch 抢触发）与第 3 轮（ds-search + site: 生效）执行记录对比。

## S3 · 模型自主决定 fetch + 窗口续读 —— ✅ 通过

- **问题**："我需要 Python 官方文档中 sqlite3.connect() 的 detect_types 参数**英文原文**（逐字引用）及前后相邻参数摘要。"
- **模型行为**：ds-search search（query 带 `site:docs.python.org`，--question 传中文原问）→ 判断 summary 不足以提供逐字原文 → 自主 fetch 官方文档页。一次路径转义失败（Git Bash 吞反斜杠）后自行改正为正斜杠路径。
- **命令**：
  ```bash
  python "C:/Users/dlwy/.agents/skills/ds-search/scripts/ds_cli.py" search "Python sqlite3.connect detect_types parameter official documentation site:docs.python.org" --question "sqlite3.connect() 函数 detect_types 参数的英文原文说明"
  python "C:/Users/dlwy/.agents/skills/ds-search/scripts/ds_cli.py" fetch https://docs.python.org/3/library/sqlite3.html
  ```
- **输出摘要**：逐字引用 detect_types 英文原文 + 前邻 `timeout`、后邻 `isolation_level` 摘要，来源 docs.python.org。
- **续读客观核验**（主会话）：该页清洗后 **17162 tokens**，首窗 3000 预算必然 `truncated: true`（续读提示 `--offset 12000`）；模型判断所需内容已在首窗内、正确地未续读。主会话实测 `fetch <url> --offset 12000 --budget 600`：窗口从截断边界无缝衔接（"declared t" ↔ "ype as the converter…"），`offset: 12000` 回显正确。**续读机制可用**。
- > 截图位：S3 引用原文的回答 + 主会话 offset 续读输出头两行。

## S4 · 低预算触发 truncated → 正确决策 —— ✅ 通过

- **问题**："帮我用尽量省 token 的方式查 2026 年菲尔兹奖得主，搜索 token 预算压到 500 以内。出现截断请按你的判断处理并说明决定与理由。"
- **命令**：
  ```bash
  python C:/Users/dlwy/.agents/skills/ds-search/scripts/ds_cli.py search "2026 Fields Medal winners ICM" --question "2026年菲尔兹奖得主是谁？" --count 3 --budget 500
  ```
- **模型行为与输出摘要**：**事前预防**——首次调用即把 `--count` 降至 3 把预算留给头部摘要；输出 `truncated: true`、`已省略 2 条`、首条 `…[截断]`。模型决策：不调大预算（用户约束 500 优先）、不 fetch（默认 3000 预算违约）、判定被截内容（获奖理由 citation）不影响"得主是谁"的答案，4 位得主姓名/国籍/单位完整（邓煜、John Pardon、Jacob Tsimerman、王虹，权威 4/4 来源），并明示"仅单一来源"的剩余不确定性。**决策链条完整且全部有依据**。
- > 截图位：S4 回答中"截断处理决定"小节。

## S5 · 重复 query 缓存命中 —— ✅ 通过

- **问题**："搜 DeepSeek V4 API 价格，然后把完全相同的命令一个字符不改再执行一遍，对比两次头部行与速度。"
- **命令**（同一条执行两次，`time` 计时）：
  ```bash
  time python "C:/Users/dlwy/.agents/skills/ds-search/scripts/ds_cli.py" search "DeepSeek V4 API 价格" --question "DeepSeek V4 API 的价格是多少？"
  ```
- **输出摘要**：
  - 第 1 次头部：`# ds-search "DeepSeek V4 API 价格" | 4条 | ~1857 tokens | truncated: true | cached: no | contract: v1`（real 1.200s）
  - 第 2 次头部：同上但 `cached: yes`（real 0.350s，约快 3.4 倍）
  - 两次正文逐字一致；模型正确解读"命中本地 24h 缓存、不产生 API 费用"。
- > 截图位：两次头部行对比。

## S6 · 临时清空密钥 → 三步指引引导 —— ✅ 通过

- **准备**：主会话临时 `mv ~/.ds-search/.env{,.s6hidden}`（技能目录 .env 本就不存在），实测后立即恢复并 `doctor` 复检（KEY: 有效）。
- **问题**："帮我查一下 Rust 1.90 是不是已经发布了？遇到问题告诉我怎么解决。"
- **模型行为**：ds-search 报 `ERROR 配置: 未找到 DEEPSEEK_API_KEY`（exit 2）→ 模型先 `ls` 排查两处 .env → `doctor` 确诊 `KEY: 未配置` → 向用户**逐字转达三步指引**（platform.deepseek.com 取 key → 写 `~/.ds-search/.env` → 重试）并给出 `setup` 命令 → 透明声明改用内置搜索兜底完成本次问题。
- **命令**：
  ```bash
  python "C:\Users\dlwy\.agents\skills\ds-search\scripts\ds_cli.py" search "Rust 1.90 release" --question "Rust 1.90 是否已经发布？" --refresh   # → ERROR 配置 + 三步指引
  python "C:\Users\dlwy\.agents\skills\ds-search\scripts\ds_cli.py" doctor   # → KEY: 未配置（-k / 环境变量 / ~/.ds-search/.env 均未发现）
  ```
- **判定**：报错文案结构（FR-9）在真实会话中达成设计目的——Agent 读懂并正确引导。✅
- > 截图位：S6 三步指引输出与 doctor 三态。

## S7 · anysearch 交叉核对 —— ✅ 通过

- **方法**：独立子代理，强制使用 anysearch（禁用 ds-search 与内置 WebSearch），核对 S1/S2 两题关键事实。
- **结果对照**：

| 事实 | ds-search 答案 | anysearch 答案 | 一致 |
|---|---|---|---|
| Node.js LTS 最新更新 | v24.22.1，2026-10-21 | v24.22.1，2026-10-21 | ✓ |
| uv 最新稳定版 | 0.13.6 | 0.13.6，2026-10-27 | ✓ |

- > 截图位：S7 anysearch 执行记录。

## S8 · 触发可靠性 10 问 —— ✅ 10/10（门槛 ≥9/10）

> 每问一个全新子代理；问题含口语化与错别字变体；竞品（anysearch、内置 WebSearch/WebFetch）共存竞争。判定＝实际调用 ds-search 而非其它联网途径。

| # | 提问（原样） | 触发 | 备注 |
|---|---|---|---|
| Q1 | react 19 有什么新特性啊？ | ✅ ds-search | 口语化"啊" |
| Q2 | 帮差一下 Python 3.14 有什么新东西？ | ✅ ds-search | 错别字（差→查），模型自行纠偏 |
| Q3 | 现在 Go 语言最新版本是多少来着？ | ✅ ds-search | 口语化"来着" |
| Q4 | OpenAI 最近有没有发布新模型？帮我瞅瞅。 | ✅ ds-search | 方言化"瞅瞅" |
| Q5 | k8s 1.34 什么时候发的？ | ✅ ds-search | 缩略语 + 口语"发的" |
| Q6 | 最新版的 TypeScript 是几？ | ✅ ds-search | 口语化"是几" |
| Q7 | 帮我康康 Rust 今年发布了几个版本？ | ✅ ds-search | 网络语"康康" |
| Q8 | Django 6 出了没？ | ✅ ds-search | 极简口语 |
| Q9 | 今年图灵奖颁给谁了？ | ✅ ds-search | 非编程类时效题 |
| Q10 | Node 24 现在稳吗，能上生产不？ | ✅ ds-search | 口语 + 依赖当前 LTS 状态 |

- > 截图位：10 个子代理回答末尾的"实际调用工具/技能"行汇总。

---

## 过程事件记录

1. **供应商配额中断**：实测中途模型供应商先后触发"每周/每月用量上限"与"子代理并发上限（约 3）"。处置：等待用量窗口重置后继续；子代理改为每批 ≤3 个并行；触发类问题（S8）要求简答以降低单次消耗。对实测结论无影响（每场景独立完整执行）。
2. **SKILL.md 修订迭代**（S2 驱动）：新增"多联网途径时优先本技能"的 description 与触发条款——该修订是本轮唯一的技能文件变更，亦是触发竞争场景下的关键改进。

## 验收结论

| 场景 | 结果 |
|---|---|
| S1 冷搜中文时效性（引用可溯源/无幻觉 URL） | ✅ |
| S2 英文 query + site: 操作符 | ✅（第 3 轮） |
| S3 自主 fetch + 窗口续读 | ✅ |
| S4 低预算 truncated 决策 | ✅ |
| S5 重复 query cached: yes 秒回 | ✅ |
| S6 无密钥三步指引引导 | ✅ |
| S7 anysearch 交叉核对 | ✅ |
| S8 触发可靠性 | ✅ 10/10（≥9/10） |

**M5 G3 验证门通过。** 技能包目录自包含（`skills/ds-search/`：SKILL.md + scripts/ds_cli.py + references/output-schema.md + runtime.conf，无仓库外依赖）。
