# ds-search

**DeepSeek official Search / Fetch API, curated for AI coding agents.** Deterministic, token-budgeted search results — no AI post-processing, no server, zero telemetry.

> Spend tokens on answers, not webpages.

**Status: in development (pre-release).** Plan: [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) · First target platform: [GitCode](https://gitcode.com/petra1218/ds-search)

## What it is (planned v0.1.0)

- `search` — numbered, compact results using DeepSeek's server-side `summary` tier (600–800 chars, designed for LLM reading), annotated with `rerank_score` / `authority` / `date`, deduped, capped by a token budget (`--budget`), never silently truncated.
- `fetch` — cleaned Markdown of a single page, windowed by token budget with `--offset` continuation.
- Three integration layers, one core: plain CLI (any agent with a shell) · Agent Skill (`SKILL.md`, works with ZCode / Claude Code / Codex / Cursor / CodeBuddy / WorkBuddy / ReasonX …) · stdio MCP (MCP-only agents).
- Keys stay on your machine and are sent only to `api.deepseek.com`. No server component. Zero telemetry.

## License

MIT
