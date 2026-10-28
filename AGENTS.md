# AGENTS.md —— 贡献者与 Agent 协作指南

面向在本仓库工作的 AI Agent 与人类贡献者。唯一权威计划：[docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)（含决策记录 §2.5，改动须更新该表）。

## 仓库结构

```
skills/ds-search/     可安装技能包（自包含）：SKILL.md + scripts/ds_cli.py + references/output-schema.md + runtime.conf
tests/                离线单测：fixtures 回放 + 契约/管道/管理命令测试（无网络无密钥）
evals/                在线评测与 token 基准（--live 需密钥）
docs/                 开发计划、E2E 实测记录（E2E_ZCODE.md）、token 基准（BENCHMARK.md）
install.sh/.ps1       多 Agent 安装器（只分发 skills/ds-search/ 目录）
```

## 硬性纪律

- **输出契约 v1 冻结**于 `skills/ds-search/references/output-schema.md`：任何输出格式变更先改契约文档，破坏性变更必须升 v2 并在 CHANGELOG 顶部声明。
- **密钥卫生六不清单**（SECURITY.md）：提交前 `git grep -E "sk-[a-f0-9]{16,}"` 必须为 0 命中（`sk-` 字样仅允许出现在前缀校验模式与文档自述中）。
- **提交前三件事**：`python -m unittest discover tests` 全绿；`git grep` 密钥检查；约定式提交信息（`feat(M<n>): ...`，WIP 注明 `[WIP]`）。
- **Windows 编码纪律**：所有文件 IO 显式 `encoding="utf-8"`；CLI 入口即 `sys.stdout.reconfigure(encoding="utf-8")`（NFR-8）。
- **零第三方依赖**：CLI 只用 Python 标准库；引入依赖属破坏性决策，须先改计划文档决策表。
- **验证等级不虚标**：README 兼容矩阵等级与计划 §2.3 一致；只有真实会话验证过才能标 ★。

## 变更流程

1. 读 `docs/DEVELOPMENT_PLAN.md` 对应里程碑与 §8 通用约束；
2. 发现计划与现实冲突（如 API 字段与文档不符）：先停，把差异写进计划文档对应小节，再继续；
3. 改动 search/fetch 管道后必须跑 `python evals/eval_live.py --live`（G2 门）；
4. 触碰 SKILL.md 触发相关措辞后，建议复跑 E2E 触发场景（S2/S8，见 docs/E2E_ZCODE.md）。

## 本地验证命令

```bash
python -m unittest discover tests          # 离线基线
python skills/ds-search/scripts/ds_cli.py doctor   # 三态自检
python evals/eval_live.py --live           # 在线评测 + 基准（需密钥，产生少量计费调用）
```
