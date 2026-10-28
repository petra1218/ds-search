# ds-search Token 基准（M7）

> 实测日期：2026-10-28 · `evals/eval_live.py --live`（DeepSeek 官方 API 直连，全冷，无缓存）
> 两侧同一启发式计数器（CJK 1 字符≈1 token，ASCII 4 字符≈1 token，宁高勿低），对照公平。

| query | 模式 A：10 条整页正文 tokens | 模式 B：本方案默认输出 tokens | 压缩比 A/B |
|---|---|---|---|
| zh-1 `Node.js LTS 最新版本` | 26816 | 1924 | 13.9x |
| zh-2 `DeepSeek V4 API 价格` | 15034 | 1927 | 7.8x |
| zh-3 `2026 年菲尔兹奖得主` | 27186 | 1824 | 14.9x |
| zh-4 `Kubernetes 1.34 发布日期` | 21941 | 786 | 27.9x |
| en-1 `latest stable release of uv astral python` | 22699 | 855 | 26.5x |
| en-2 `Go 1.27 release notes highlights` | 54143 | 1868 | 29.0x |
| en-3 `Rust 2026 releases changelog` | 70226 | 1926 | 36.5x |
| en-4 `TypeScript 7.0 native compiler announcement` | 20739 | 1131 | 18.3x |
| ops-1 `Python sqlite3 connect site:docs.python.org` | 125965 | 2042 | 61.7x |
| ops-2 `uv releases site:github.com astral-sh` | 33370 | 1515 | 22.0x |
| **合计（10 query）** | **418119** | **15798** | **26.5x** |

结论：同批 query 下，本方案默认管道输出（count=6、summary 层、2000 token 预算）
约为"10 条整页正文"直读体量的 **26.5x**（启发式估计，宁高勿低）。
