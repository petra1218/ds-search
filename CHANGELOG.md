# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-11-14

### Changed

- SKILL.md 触发措辞扩展（措辞级变更，无代码改动，输出契约 v1 不变）：
  - **二次换引擎**：用户在一轮搜索结果后要求"再搜 / 仔细搜 / 还有没有没想到的方案 / 换个角度查 / 别的思路"时触发本技能——不同搜索引擎索引不同，换用即提升召回；
  - **密钥去回避**：新增"未配置密钥时首次调用输出本身就是三步引导、不会失败"声明——实测中模型曾以"需要密钥"为由回避本技能转用其它搜索工具；
  - 优先级条款从"内置 WebSearch/WebFetch"扩为"内置 WebSearch/WebFetch、批量/垂直搜索类工具等其它联网途径"。
- 正文「何时触发」镜像以上条款，并新增穷尽式调研分工说明（批量搜索铺广度 → 本技能收束核证并抓官方原文）。

### Verified

- 触发竞争实测（本机 ZCode，anysearch MCP 与技能共存、无内置 WebSearch/WebFetch）：发散式/二次搜索话术 5 问 3/5 → 4/5，基线两个 miss（纯发散话术、"需密钥"回避）全部翻正且保持；事实查证话术 6 问与原版 4/6 持平（含净翻正 1 题）。完整三版本对照数据见 `docs/E2E_ZCODE.md` S9。
- **平台约束发现**：SKILL.md description 超过 ~1024 字符会被 ZCode 静默拒载（YAML 本身合法，pyyaml 校验通过）——实测 1074 字符拒载、738 字符正常。今后措辞迭代必须在此预算内。

## [0.2.0] - 2026-10-31

### Notes

- Maintenance release with **no code changes** since 0.1.3: the 0.1.x line is complete (installer hardening and the version-stamping update loop landed in 0.1.1–0.1.3), and this bump opens the 0.2.x development cycle. Tree is identical to `v0.1.3`.
- Output contract v1 unchanged. Updating is optional: `git pull` + re-run either installer (idempotent; keys and cache are never touched), or `npx skills update ds-search` for npx-installed copies.

## [0.1.3] - 2026-10-31

### Fixed

- `install.ps1` crashed under Windows PowerShell 5.1 when run from a non-git copy (e.g. a Release zip download): with `$ErrorActionPreference = "Stop"`, redirecting a native command's stderr (`git describe --tags 2>$null`) raises a terminating error. The git probe now temporarily relaxes the preference and always falls back to `dev`. Regression-guarded in `tests/test_install.py`. Happy path (install from a git clone) was always fine; this fixes the zip-download path introduced with version stamping in 0.1.2.

### Verified

- `npx skills add petra1218/ds-search` and `npx skills update ds-search` tested end-to-end in an isolated project (agent name for the skills CLI is `claude-code`; the command in the README installs interactively without `-a`). Update confirms "up to date" via `skills-lock.json` source tracking.
- Non-git fallback (`Version: dev`) now tested for **both** installers under PS 5.1 and Git Bash.

## [0.1.2] - 2026-10-31

### Added

- Installed-version visibility, closing the update loop: both installers now stamp the version (from `git describe --tags`, `dev` fallback) into `runtime.conf`, and `doctor` shows it as its first line (`版本: v0.1.2`) — so any installed copy can tell which release it is. Repo checkouts report `dev`.
- "Update" section in both READMEs: the installer is idempotent, so updating = `git pull` + re-run it (keys and cache are never touched); `npx skills update ds-search` for `npx`-installed copies.
- Guarded by new tests: version line in both installer templates and repo `runtime.conf`, `doctor` version rendering, `read_runtime_version` parsing.

## [0.1.1] - 2026-10-29

### Fixed

- `install.ps1` is now saved as UTF-8 **with BOM**: Windows PowerShell 5.1 parses BOM-less files with the legacy ANSI code page (GBK on Chinese Windows) and failed with syntax errors on the script's Chinese text. `runtime.conf` written by the PowerShell installer is now BOM-less on both PowerShell 5.1 and 7 (via `WriteAllText`). Guarded by `tests/test_install.py` (BOM present in `.ps1`, absent in `.sh`, target sets in sync).

## [0.1.0] - 2026-10-28

### Added

- Single-file CLI (`skills/ds-search/scripts/ds_cli.py`, Python 3.7+ stdlib only):
  - `search` — deterministic curation pipeline (dedup → score annotation → token-budget packing → explicit truncation), output contract v1, DeepSeek search operators pass-through (`site:` `-site:` `"..."` `lang:` `after:` `before:`), `--count/--budget/--question/--min-score/--json/--full/--refresh/--timeout`.
  - `fetch` — page cleaning (script/style residue, nav/footer noise, blank-line compression), token-budget windowing with `--offset` continuation, prompt-injection guard line.
  - `setup` / `doctor` / `stats` / `cache clean` — interactive key configuration, three-state self-check, call statistics, cache management.
- Local cache: one JSON file per query under `~/.ds-search/cache/`, SHA-256 key, 24h TTL, `cached:` marker and `--refresh` bypass; cache hits are free.
- Key resolution chain: `-k` > `DEEPSEEK_API_KEY` env > `~/.ds-search/.env` > `<skill_dir>/.env`; missing-key error is a three-step agent-readable guide (exit code 2).
- Official error-code handling: retry once with backoff on 408/429/5xx (unbilled failures), 402 top-up hint, 401 key hint; explicit 30s default timeout.
- Agent Skill package (`skills/ds-search/`): bilingual SKILL.md (trigger-first description, two-step search→fetch ladder, operator cheatsheet, output example) + frozen output contract v1 (`references/output-schema.md`) + `runtime.conf`.
- ZCode E2E verification record: `docs/E2E_ZCODE.md` — S1–S7 passed, S8 trigger reliability 10/10.
- Multi-agent installers: `install.sh` / `install.ps1` with `--agent=zcode|claude|codex|cursor|codebuddy|workbuddy|reasonx|all`, idempotent overwrite.
- Live evaluation & token benchmark: `evals/eval_live.py --live`, results in `docs/BENCHMARK.md`.
- Bilingual docs: `README.md` / `README.zh-CN.md` with honest compatibility-matrix levels; `SECURITY.md` key-hygiene policy; `AGENTS.md` contributor guide.

### Notes

- No MCP layer by design (decision D9): every target agent reads skills or runs the CLI.
- Released on GitCode first; tag `v0.1.0`.

[Unreleased]: https://gitcode.com/petra1218/ds-search/compare/v0.2.0...main
[0.2.0]: https://gitcode.com/petra1218/ds-search/compare/v0.1.3...v0.2.0
[0.1.3]: https://gitcode.com/petra1218/ds-search/compare/v0.1.2...v0.1.3
[0.1.2]: https://gitcode.com/petra1218/ds-search/compare/v0.1.1...v0.1.2
[0.1.1]: https://gitcode.com/petra1218/ds-search/compare/v0.1.0...v0.1.1
[0.1.0]: https://gitcode.com/petra1218/ds-search/releases/tag/v0.1.0
