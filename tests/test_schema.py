"""M1: 响应字段与官方文档一致性断言（fixtures 回放，离线、无网络、无密钥）。

依据官方文档 api-docs.deepseek.com/zh-cn/guides/search/（2026-10-28 全文核对）：
- results 每项含 10 字段；rerank_score 0~3；authority -1~4（-1=未知）；
  date 为 RFC3339 UTC 或 null；need_content=false 时 content 恒为空字符串；
  空结果返回 {"results": []}。
- Fetch 返回 {title, content}。
"""
import json
import re
import unittest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$")
RESULT_KEYS = {
    "rerank_score", "title", "url", "snippet", "summary", "content",
    "site_name", "site_icon", "date", "authority",
}
# fixture 名 -> 录制时 need_content 的取值
SEARCH_FIXTURES = {
    "search_zh.json": False,
    "search_en.json": False,
    "search_ops2.json": False,
    "search_full.json": True,
}


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class TestSearchSchema(unittest.TestCase):
    def test_result_fields_match_official_docs(self):
        for name in SEARCH_FIXTURES:
            for item in load(name)["results"]:
                self.assertEqual(RESULT_KEYS, set(item.keys()), name)
                self.assertIsInstance(item["title"], str)
                self.assertIsInstance(item["url"], str)
                self.assertRegex(item["url"], r"^https?://")
                for field in ("snippet", "summary", "content"):
                    self.assertIsInstance(item[field], str, (name, field))
                self.assertGreater(len(item["summary"]), 0, name)

    def test_rerank_score_range(self):
        for name in SEARCH_FIXTURES:
            for item in load(name)["results"]:
                score = item["rerank_score"]
                self.assertIsInstance(score, (int, float))
                self.assertGreaterEqual(score, 0, name)
                self.assertLessEqual(score, 3, name)

    def test_authority_range(self):
        for name in SEARCH_FIXTURES:
            for item in load(name)["results"]:
                self.assertIsInstance(item["authority"], int)
                self.assertGreaterEqual(item["authority"], -1, name)
                self.assertLessEqual(item["authority"], 4, name)

    def test_date_rfc3339_or_null(self):
        for name in SEARCH_FIXTURES:
            for item in load(name)["results"]:
                if item["date"] is not None:
                    self.assertRegex(item["date"], RFC3339, name)

    def test_content_empty_when_not_requested(self):
        for name, requested in SEARCH_FIXTURES.items():
            for item in load(name)["results"]:
                if requested:
                    self.assertGreater(len(item["content"]), 0, name)
                else:
                    self.assertEqual(item["content"], "", name)

    def test_empty_results_shape(self):
        """空结果：顶层数组存在且为空（官方：搜索无结果不计费）。"""
        data = load("search_ops.json")
        self.assertEqual(set(data.keys()), {"results"})
        self.assertEqual(data["results"], [])


class TestFetchSchema(unittest.TestCase):
    def test_fetch_fields(self):
        for name in ("fetch_en.json", "fetch_zh.json"):
            data = load(name)
            self.assertEqual(set(data.keys()), {"title", "content"})
            self.assertIsInstance(data["title"], str)
            self.assertIsInstance(data["content"], str)
            self.assertGreater(len(data["content"]), 0, name)


class TestNoSecretsInFixtures(unittest.TestCase):
    """密钥卫生：fixtures 中不得出现密钥模式（NFR-3）。"""

    def test_no_key_pattern(self):
        import glob
        for path in glob.glob(str(FIXTURES / "*.json")):
            text = Path(path).read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"sk-[a-f0-9]{16,}", text), path)


if __name__ == "__main__":
    unittest.main()
