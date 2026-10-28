#!/usr/bin/env python3
"""ds-search 在线评测（G2 门）：--live 真实调用 DeepSeek Search API。

对 queries.json 的每个 query 做两次真实调用（直连 API，不读写缓存，保证全冷）：
  A) count=10 + need_content=true —— "10 条整页正文"基线，模型若直读全量的体量；
  B) 默认管道（count=6, need_content=false, budget=2000）—— 本方案输出体量。
两侧用同一个启发式计数器（ds_cli.count_tokens），对照公平。

断言（G2 验收）：
  - 字段完整：results 为 list；每条含 url/title；rerank_score ∈ [0,3] 或 None；
    authority ∈ [-1,4] 或 None；
  - 契约头：'# ds-search "…"' 开头且含 contract: v1；~T tokens 中 T ≤ budget；
  - truncated 正确：truncated: true ⇔ 输出含 '> 已省略'（默认模式语义）；
  - 空结果（操作符叠加可能）：合法通过，标注 note（不计费）。

产出：逐项 PASS/FAIL 控制台输出；--benchmark-out 写入 Markdown 对照表（docs/BENCHMARK.md）。
退出码：0 全过 / 1 有失败。密钥走环境变量 DEEPSEEK_API_KEY 或 ~/.ds-search/.env。
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "skills" / "ds-search" / "scripts"))
import ds_cli  # noqa: E402

BUDGET = 2000
RAW_COUNT = 10
CURATION_COUNT = 6


def raw_body_tokens(response):
    """模式 A 体量：模型直读全部 title+summary+content 的 token 估计。"""
    total = 0
    for r in response.get("results", []):
        total += ds_cli.count_tokens(str(r.get("title", "")))
        total += ds_cli.count_tokens(str(r.get("summary", "") or r.get("snippet", "")))
        total += ds_cli.count_tokens(str(r.get("content", "")))
    return total


def check_query(entry, key, timeout):
    """返回 (ok, note, tokens_raw, tokens_curated)。"""
    q, question = entry["query"], entry.get("question")
    payload_a = {"query": q, "count": RAW_COUNT, "need_content": True}
    payload_b = {"query": q, "count": CURATION_COUNT, "need_content": False}
    if question:
        payload_a["ori_question"] = question
        payload_b["ori_question"] = question
    resp_a = ds_cli.api_post(key, "/v1/tools/search", payload_a, timeout)
    resp_b = ds_cli.api_post(key, "/v1/tools/search", payload_b, timeout)
    tokens_raw = raw_body_tokens(resp_a)

    results = resp_b.get("results", [])
    if not results:
        curated = ds_cli.curate_and_format(q, [], BUDGET, cached=False)
        assert '"contract: v1' in curated or "contract: v1" in curated
        return True, "空结果（合法，不计费）", tokens_raw, 0

    for r in results:
        assert isinstance(r.get("url"), str) and r["url"], f"url 缺失: {r}"
        assert isinstance(r.get("title"), str), f"title 缺失: {r}"
        score = r.get("rerank_score")
        assert score is None or (isinstance(score, (int, float)) and 0 <= score <= 3), f"rerank_score 越界: {score}"
        auth = r.get("authority")
        assert auth is None or (isinstance(auth, (int, float)) and -1 <= auth <= 4), f"authority 越界: {auth}"

    curated = ds_cli.curate_and_format(q, results, BUDGET, cached=False)
    header = curated.splitlines()[0]
    assert header.startswith('# ds-search "') and "contract: v1" in header, f"契约头不符: {header}"
    tokens_shown = int(header.split("|")[2].strip().split("~")[1].split()[0])
    assert tokens_shown <= BUDGET, f"预算超限: {tokens_shown} > {BUDGET}"
    truncated = "truncated: true" in header
    assert truncated == ("> 已省略" in curated), "truncated 标志与省略行不一致"
    return True, f"{len(results)} 条", tokens_raw, ds_cli.count_tokens(curated)


def render_benchmark(rows, path):
    lines = [
        "# ds-search Token 基准（M7）",
        "",
        f"> 实测日期：2026-10-28 · `evals/eval_live.py --live`（DeepSeek 官方 API 直连，全冷，无缓存）",
        "> 两侧同一启发式计数器（CJK 1 字符≈1 token，ASCII 4 字符≈1 token，宁高勿低），对照公平。",
        "",
        "| query | 模式 A：10 条整页正文 tokens | 模式 B：本方案默认输出 tokens | 压缩比 A/B |",
        "|---|---|---|---|",
    ]
    sum_a = sum_b = 0
    for r in rows:
        ratio = f"{r['raw'] / r['curated']:.1f}x" if r["curated"] else "—"
        lines.append(f"| {r['id']} `{r['query']}` | {r['raw']} | {r['curated']} | {ratio} |")
        sum_a, sum_b = sum_a + r["raw"], sum_b + r["curated"]
    overall = f"{sum_a / sum_b:.1f}x" if sum_b else "—"
    lines += [
        f"| **合计（10 query）** | **{sum_a}** | **{sum_b}** | **{overall}** |",
        "",
        f"结论：同批 query 下，本方案默认管道输出（count=6、summary 层、2000 token 预算）",
        f"约为\"10 条整页正文\"直读体量的 **{overall}**（启发式估计，宁高勿低）。",
        "",
    ]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    parser = argparse.ArgumentParser(description="ds-search 在线评测（G2）")
    parser.add_argument("--live", action="store_true", help="真实调用 API（默认仅打印题集）")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--benchmark-out", default=str(REPO / "docs" / "BENCHMARK.md"))
    args = parser.parse_args()

    queries = json.loads((HERE / "queries.json").read_text(encoding="utf-8"))["queries"]
    if not args.live:
        for q in queries:
            print(f"[题集] {q['id']}: {q['query']}")
        return 0

    key = ds_cli.resolve_key(None, dict(__import__("os").environ), str(Path.home()),
                             str(REPO / "skills" / "ds-search"))
    if not key:
        print(ds_cli.NO_KEY_MESSAGE)
        return 2

    rows, failures = [], 0
    for q in queries:
        try:
            ok, note, tokens_raw, tokens_curated = check_query(q, key, args.timeout)
            if not ok:
                failures += 1
            print(f"PASS {q['id']}: {note} | A={tokens_raw} B={tokens_curated}")
            rows.append({"id": q["id"], "query": q["query"], "raw": tokens_raw, "curated": tokens_curated})
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {q['id']}: {exc}")
            rows.append({"id": q["id"], "query": q["query"], "raw": 0, "curated": 0})
        except ds_cli.ApiError as exc:
            failures += 1
            print(f"FAIL {q['id']}: {ds_cli.error_line(exc)}")
            rows.append({"id": q["id"], "query": q["query"], "raw": 0, "curated": 0})

    render_benchmark(rows, args.benchmark_out)
    print(f"\n{len(queries) - failures}/{len(queries)} PASS · 基准表已写入 {args.benchmark_out}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
