"""M2: 管道纯函数单测（预算边界/去重/低分/缓存/token 计数/契约格式/无 key 报错）。

全部离线：策展函数只吃 fixtures JSON，不碰网络。CLI 子进程测试通过重定向
USERPROFILE/HOME 隔离密钥，参数校验先于网络调用，因此同样无网络。
"""
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CLI = REPO / "skills" / "ds-search" / "scripts" / "ds_cli.py"
FIXTURES = REPO / "tests" / "fixtures"

_spec = importlib.util.spec_from_file_location("ds_cli", CLI)
ds = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ds)


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def zh_results():
    return load("search_zh.json")["results"]


class TestTokenCounter(unittest.TestCase):
    def test_ascii(self):
        self.assertEqual(ds.count_tokens("hello world"), 3)  # ceil(11/4)

    def test_cjk(self):
        self.assertEqual(ds.count_tokens("中文五个字"), 5)

    def test_mixed(self):
        self.assertEqual(ds.count_tokens("abc中文"), 3)  # 2 CJK + ceil(3/4)=1

    def test_empty(self):
        self.assertEqual(ds.count_tokens(""), 0)


class TestResolveKey(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_cli_flag_wins(self):
        self.assertEqual(ds.resolve_key("K", {"DEEPSEEK_API_KEY": "E"}, self.tmp, self.tmp), "K")

    def test_env_beats_files(self):
        (self.tmp / ".ds-search").mkdir()
        (self.tmp / ".ds-search" / ".env").write_text("DEEPSEEK_API_KEY=F", encoding="utf-8")
        self.assertEqual(ds.resolve_key(None, {"DEEPSEEK_API_KEY": "E"}, self.tmp, self.tmp), "E")

    def test_home_file(self):
        (self.tmp / ".ds-search").mkdir()
        (self.tmp / ".ds-search" / ".env").write_text("DEEPSEEK_API_KEY=H", encoding="utf-8")
        self.assertEqual(ds.resolve_key(None, {}, self.tmp, self.tmp / "skill"), "H")

    def test_skill_dir_fallback(self):
        skill = self.tmp / "skill"
        skill.mkdir()
        (skill / ".env").write_text("DEEPSEEK_API_KEY=S", encoding="utf-8")
        self.assertEqual(ds.resolve_key(None, {}, self.tmp / "other", skill), "S")

    def test_none_when_absent(self):
        self.assertIsNone(ds.resolve_key(None, {}, self.tmp, self.tmp / "skill"))


class TestDedup(unittest.TestCase):
    def test_same_url_keeps_first(self):
        items = zh_results()
        duplicated = items + [dict(items[0])]
        out = ds.dedup(duplicated)
        self.assertEqual(len(out), len(items))
        self.assertEqual(out[0]["url"], items[0]["url"])


class TestCutToTokens(unittest.TestCase):
    def test_no_cut(self):
        text, cut = ds._cut_to_tokens("短文本", 100)
        self.assertEqual(text, "短文本")
        self.assertFalse(cut)

    def test_cut_respects_budget(self):
        text = "a" * 400
        out, cut = ds._cut_to_tokens(text, 10)
        self.assertTrue(cut)
        self.assertIn(ds.CUTOFF_MARK, out)
        self.assertLessEqual(ds.count_tokens(out), 10)

    def test_zero_budget_keeps_mark_only(self):
        out, cut = ds._cut_to_tokens("whatever", 0)
        self.assertEqual(out, ds.CUTOFF_MARK)
        self.assertTrue(cut)


class TestContractFormat(unittest.TestCase):
    HEADER = re.compile(
        r'^# ds-search "测试" \| (\d+)条 \| ~(\d+) tokens \| truncated: (true|false) '
        r'\| cached: (yes|no) \| contract: v1$')
    FOOTER = re.compile(r"^## (\d+)条中(\d+)条低于1\.5分 \| 需要全文: fetch <url> \| 重搜带正文: --full$")

    def test_full_contract_shape(self):
        out = ds.curate_and_format("测试", zh_results(), budget=10 ** 6)
        lines = out.split("\n")
        header = self.HEADER.match(lines[0])
        self.assertIsNotNone(header, lines[0])
        self.assertEqual(header.group(1), "6")
        self.assertEqual(header.group(3), "false")
        self.assertRegex(lines[1], r"^\[1\] \(\d+\.\d分\|权威-?\d+\|\d{4}-\d{2}-\d{2}\) .+")
        self.assertTrue(lines[2].startswith("    http"))
        footer = self.FOOTER.match(lines[-1])
        self.assertIsNotNone(footer, lines[-1])
        self.assertEqual(footer.group(1), "6")
        self.assertNotIn("已省略", out)

    def test_cached_flag(self):
        out = ds.curate_and_format("测试", zh_results(), budget=10 ** 6, cached=True)
        self.assertIn("cached: yes", out.split("\n")[0])

    def test_empty_results(self):
        out = ds.curate_and_format("空", [], budget=2000)
        lines = out.split("\n")
        self.assertIn("| 0条 | ~0 tokens |", lines[0])
        self.assertIn("无结果", lines[-1])


class TestBudgetBoundaries(unittest.TestCase):
    def costs(self):
        items = ds.dedup(zh_results())
        return [ds.count_tokens(ds._item_block(n, r, None)[0]) for n, r in enumerate(items, 1)]

    def test_large_budget_all_fit(self):
        items = ds.dedup(zh_results())
        selected, omitted = ds._select_items(items, 10 ** 6, full=False)
        self.assertEqual(len(selected), 6)
        self.assertEqual(omitted, 0)

    def test_partial_fit_sets_omitted(self):
        costs = self.costs()
        budget = costs[0] + costs[1]
        items = ds.dedup(zh_results())
        selected, omitted = ds._select_items(items, budget, full=False)
        self.assertEqual(len(selected), 2)
        self.assertEqual(omitted, 4)

    def test_exact_fit_boundary(self):
        budget = sum(self.costs())
        items = ds.dedup(zh_results())
        selected, omitted = ds._select_items(items, budget, full=False)
        self.assertEqual(len(selected), 6)
        self.assertEqual(omitted, 0)

    def test_tiny_budget_first_item_survives_with_mark(self):
        out = ds.curate_and_format("测试", zh_results(), budget=1)
        self.assertIn("truncated: true", out.split("\n")[0])
        self.assertIn("> 已省略 5 条", out)
        self.assertIn(ds.CUTOFF_MARK, out)

    def test_output_within_budget_when_tiny(self):
        # 截断后正文（首条 title+url）必须仍可解析且远小于未截断输出
        out = ds.curate_and_format("测试", zh_results(), budget=1)
        body = "\n".join(out.split("\n")[2:-1])  # 跳过信封头与已省略行、尾行
        self.assertLessEqual(ds.count_tokens(body), 60)  # 首条 title+url+标记的地板值


class TestLowScoreAndMinScore(unittest.TestCase):
    def crafted(self):
        items = ds.dedup(zh_results())
        items[1]["rerank_score"] = 1.2
        return items

    def test_low_score_kept_and_counted(self):
        items = self.crafted()
        out = ds.curate_and_format("测试", items, budget=10 ** 6)
        self.assertIn("## 6条中1条低于1.5分", out)
        self.assertIn(items[1]["url"], out)

    def test_min_score_drops(self):
        items = self.crafted()
        out = ds.curate_and_format("测试", items, budget=10 ** 6, min_score=2.0)
        self.assertIn("| 5条 |", out.split("\n")[0])
        self.assertNotIn(items[1]["url"], out)
        self.assertIn("0条低于1.5分", out)


class TestFullMode(unittest.TestCase):
    def test_content_truncated_per_item_nothing_dropped(self):
        results = load("search_full.json")["results"]
        out = ds.curate_and_format("测试", results, budget=900, full=True)
        header = out.split("\n")[0]
        self.assertIn("truncated: false", header)  # --full 模式不整条丢弃
        self.assertNotIn("已省略", out)
        self.assertIn(ds.CUTOFF_MARK, out)  # 预算均分必然触发单条截断（实测正文 24k 字符）
        self.assertEqual(out.count("\n[2]"), 1)  # 条目仍齐全
        self.assertIn("[3] (", out)


class TestJsonMode(unittest.TestCase):
    def test_shape(self):
        out = json.loads(ds.format_json("测试", zh_results(), budget=10 ** 6))
        self.assertEqual(
            set(out.keys()),
            {"contract", "query", "returned", "total_found", "tokens_estimate",
             "truncated", "cached", "results"})
        self.assertEqual(out["returned"], 6)
        self.assertEqual(out["contract"], "v1")
        self.assertFalse(out["truncated"])
        first = out["results"][0]
        self.assertEqual(
            set(first.keys()),
            {"n", "rerank_score", "authority", "date", "title", "url", "summary",
             "content", "below_threshold"})

    def test_budget_trims_returned(self):
        out = json.loads(ds.format_json("测试", zh_results(), budget=50))
        self.assertLess(out["returned"], out["total_found"])
        self.assertTrue(out["truncated"])


class TestCache(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())

    def test_roundtrip_and_hit(self):
        payload = {"query": "q", "count": 6, "need_content": False}
        ds.cache_set(self.home, payload, {"results": [1]}, meta={"latency_ms": 5}, now=1000)
        record = ds.cache_get(self.home, payload, now=1000)
        self.assertIsNotNone(record)
        self.assertEqual(record["response"], {"results": [1]})

    def test_ttl_expiry(self):
        payload = {"query": "q2", "count": 6, "need_content": False}
        ds.cache_set(self.home, payload, {"results": []}, meta={}, now=1000)
        self.assertIsNone(ds.cache_get(self.home, payload, now=1000 + ds.CACHE_TTL_SECONDS + 1))
        self.assertIsNotNone(ds.cache_get(self.home, payload, now=1000 + ds.CACHE_TTL_SECONDS - 1))

    def test_corrupt_file_returns_none(self):
        payload = {"query": "q3", "count": 6, "need_content": False}
        ds.cache_set(self.home, payload, {"results": []}, meta={}, now=1000)
        path = ds.cache_dir(self.home) / (ds.cache_key(payload) + ".json")
        path.write_text("{corrupt", encoding="utf-8")
        self.assertIsNone(ds.cache_get(self.home, payload, now=1000))


def run_cli(args, env_home):
    env = {"SystemRoot": os.environ.get("SystemRoot", ""),
           "PATH": os.environ.get("PATH", ""),
           "USERPROFILE": str(env_home), "HOME": str(env_home)}
    proc = subprocess.run([sys.executable, str(CLI)] + args,
                          capture_output=True, env=env, timeout=30)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


class TestCliNoNetwork(unittest.TestCase):
    """参数校验与无 key 指引都发生在任何网络调用之前，可安全离线测试。"""

    def test_no_key_three_step_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli(["search", "测试"], tmp)
        self.assertEqual(code, 2)
        self.assertIn("platform.deepseek.com", out)
        self.assertIn("1.", out)
        self.assertIn("3. 重新执行", out)

    def test_count_out_of_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli(["search", "测试", "--count", "99"], tmp)
        self.assertEqual(code, 2)
        self.assertIn("--count", out)

    def test_query_too_long(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli(["search", "长" * 129], tmp)
        self.assertEqual(code, 2)
        self.assertIn("1~128", out)


if __name__ == "__main__":
    unittest.main()
