# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://gitcode.com/petra1218/ds-search/compare/v0.1.0...main
[0.1.0]: https://gitcode.com/petra1218/ds-search/releases/tag/v0.1.0
