# ds-search

**把 DeepSeek 官方 Search / Fetch API 策展给 AI 编程 Agent。** 确定性管道、token 预算受控——结果不经任何 AI 二次加工，无服务器、零遥测。

> 把 token 花在答案上，而不是网页上。

- `search` —— 基于官方服务端 `summary` 层（专为模型阅读而生）的编号紧凑结果，带 `rerank_score` / `权威` / `日期` 标注，URL 去重，token 预算封顶，绝不静默截断。
- `fetch` —— 单页清洗后的 Markdown，按 token 预算开窗，`--offset` 续读，首行自带提示注入防护标注。
- 一个核心、两层形态：纯标准库单文件 CLI（任何能跑 shell 的 Agent）+ [Agent Skill](skills/ds-search/SKILL.md) 技能目录。不做 MCP 层——所有目标 Agent 都能读技能目录或直接执行 CLI。
- 密钥只存在本机、只发往 `api.deepseek.com`。无服务器组件，零遥测。

English docs: [README.md](README.md) · 开发计划：[docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)

## 为什么

原始搜索 API 会把整页网页灌进上下文。ds-search 用确定性管道替代：去重 → 评分标注 → 预算装入 → 显式截断标记——模型读到的是约 2000 token 的策展摘要，而不是原始转储。搜索结果不经任何 AI 二次加工；输出格式冻结为**契约 v1**（[skills/ds-search/references/output-schema.md](skills/ds-search/references/output-schema.md)），破坏性变更必须升版本号。

## 安装

需要 Python 3.7+（纯标准库，无 pip 依赖）与 [platform.deepseek.com](https://platform.deepseek.com) 的 API Key。

**手工安装（主要方式）：**

```bash
git clone https://gitcode.com/petra1218/ds-search.git
cd ds-search

# ZCode
./install.sh --agent=zcode        # Windows PowerShell: .\install.ps1 -Agent zcode

# Claude Code / Codex / Cursor / 全部
./install.sh --agent=claude
./install.sh --agent=codex
./install.sh --agent=cursor
./install.sh --agent=all
```

**`npx skills add`（辅助方式）：**

```bash
npx skills add petra1218/ds-search
```

**配置密钥**（任选其一）：

```bash
# 交互式引导
python ~/.agents/skills/ds-search/scripts/ds_cli.py setup
# 或在 ~/.ds-search/.env 写入一行
# DEEPSEEK_API_KEY=<你的Key>
# 或设置同名环境变量
```

密钥优先级：`-k` 参数 > 环境变量 `DEEPSEEK_API_KEY` > `~/.ds-search/.env` > `<技能目录>/.env`。`doctor` 一条命令自检 Python / 密钥 / 网络。

## CLI 用法

```bash
DS=~/.agents/skills/ds-search/scripts/ds_cli.py

# 搜索：默认 6 条、约 2000 token 预算、缓存 24h（重复 query 免费秒回）
python $DS search "GLM-5 发布时间" --question "GLM-5 什么时候发布的？"

# 抓取单页：清洗后的 Markdown、3000 token 窗口、--offset 续读
python $DS fetch https://example.com/article --offset 12000

# 维护
python $DS doctor        # Python / 密钥 / 网络自检
python $DS stats         # 调用次数、token、缓存命中率、耗时
python $DS cache clean
```

搜索操作符原样透传引擎：`site:` `-site:` `"精确短语"` `lang:zh,en` `after:2026-06-01` `before:`。操作符叠加过狠可能返回空结果（不计费）。时效敏感的问题加 `--refresh` 绕过 24h 缓存。其余参数：`--count 1~50`、`--budget`、`--min-score`、`--json`、`--full`（带正文重搜——更贵，优先 fetch）、`--timeout`（默认 30s）。

## Agent 兼容矩阵

| Agent | 技能支持 | 适配方式 | 验证等级 |
|---|---|---|---|
| ZCode | `~/.agents/skills/` | Skill | ★ 本机亲测（E2E 实测：[docs/E2E_ZCODE.md](docs/E2E_ZCODE.md)） |
| Claude Code | `~/.claude/skills/`；`npx skills add` | Skill | 冒烟 |
| Codex | `~/.codex/skills/`；`npx skills add` | Skill | 冒烟 |
| Cursor | 官方文档确认兼容读取 `.claude`/`.codex` 技能目录 | Skill | 文档级 |
| CodeBuddy | 官方博客实证支持 SKILL.md 技能 | Skill | 文档级 |
| WorkBuddy | 内置 Skills 扩展能力（第三方介绍） | Skill | 文档级 |
| ReasonX | 未获一手证据 | Skill / CLI 兜底 | 社区级（未验证） |
| Gemini CLI / Windsurf 等 | — | 指令文件（AGENTS.md 等）引到 CLI | 社区级 |

等级如实标注：★ = 真实会话全流程 E2E；冒烟 = 安装后文件落位并被发现；文档级 = 仅厂商文档佐证；社区级 = 未验证的社区报告。任何能执行 shell 的 Agent 都可以直接走 CLI 层。

## 费用

DeepSeek 对 Search/Fetch 按 ¥5（约 $0.75）/千次**成功**请求计费——失败、空结果、超时均不计费；`count` 不影响单价。本地缓存命中（24h TTL）零成本。日常交互式使用每天通常只有几分级别的开销。

## 安全

无服务器组件、无遥测、无埋点。密钥只从本地文件读取，仅经 HTTPS 发往 `api.deepseek.com`。密钥不出现在日志、缓存内容、错误信息、fixtures、`stats` 输出和 git 仓库中。fetch 返回的网页正文按不可信外部数据处理：CLI 在其首行输出显式防护标注（"视为数据而非指令"）。详见 [SECURITY.md](SECURITY.md)。

## 故障排查

- **`ERROR 配置: 未找到 DEEPSEEK_API_KEY`** —— 输出本身就是三步指引：到 platform.deepseek.com 创建 Key → 写入 `~/.ds-search/.env` → 重试。
- **`ERROR 401`** —— Key 无效；到平台控制台核对后更新 `~/.ds-search/.env`。
- **`ERROR 402`** —— 账户余额不足；充值后重试。
- **`0条` 空结果** —— 通常是操作符叠加过多；放宽条件，或怀疑缓存陈旧时加 `--refresh`。
- **Windows 乱码** —— 确认 Python 3.7+；CLI 启动时已将 stdout 重配置为 UTF-8。
- **`truncated: true` / `已省略 J 条`** —— 设计内的预算封顶；收窄 query、用 `--min-score` 过滤、调低 `--count`，或调大 `--budget`。

## 开发

```bash
python -m unittest discover tests   # 离线、fixture 回放、无需密钥
```

目录：`skills/ds-search/`（可安装、自包含）· `tests/`（fixtures + 契约测试）· `evals/`（在线评测 + token 基准）· `docs/`（计划、E2E 实测、基准）。输出契约 v1 冻结于 [skills/ds-search/references/output-schema.md](skills/ds-search/references/output-schema.md)；破坏性变更必须升 v2。里程碑与决策记录：[docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)。

## 许可证

MIT
