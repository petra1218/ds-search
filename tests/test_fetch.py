"""M3: fetch 管道单测（清洗规则/窗口边界/两窗拼接/URL 校验/契约格式）。全部离线。"""
import tempfile
import unittest

from test_pipeline import ds, load, run_cli  # 复用 M2 的模块加载与 CLI 跑法


class TestCleanRules(unittest.TestCase):
    """清洗规则逐条：修改规则须同步本类与 docs/output-schema.md §2。"""

    def test_script_block_removed(self):
        src = "前\n<script type=\"text/javascript\">alert(1)</script>\n后"
        self.assertEqual(ds.clean_markdown(src), "前\n后")

    def test_style_block_removed(self):
        src = "前\n<style>a{color:red}</style>\n后"
        self.assertEqual(ds.clean_markdown(src), "前\n后")

    def test_blank_lines_collapsed(self):
        self.assertEqual(ds.clean_markdown("a\n\n\n\n\nb"), "a\n\nb")

    def test_nav_image_lines_removed(self):
        src = "![site logo](https://x/logo.png)\n正文"
        self.assertEqual(ds.clean_markdown(src), "正文")

    def test_nav_word_lines_removed(self):
        src = "首页\nHome\n| 隐私政策 |\n正文"
        self.assertEqual(ds.clean_markdown(src), "正文")

    def test_ad_lines_removed(self):
        src = "[广告]\n（advertisement）\n正文"
        self.assertEqual(ds.clean_markdown(src), "正文")

    def test_normal_markdown_untouched(self):
        src = "# 标题\n\n正文段落，含 [链接](https://a.com) 与 ![配图](https://a/i.png)。"
        self.assertEqual(ds.clean_markdown(src), src)


class TestWindow(unittest.TestCase):
    CONTENT = "a" * 5000 + "中" * 3000  # 混合长度便于 token 边界

    def test_window_from_zero(self):
        window, truncated, end, remaining = ds.window_text(self.CONTENT, 0, 200)
        self.assertTrue(window)
        self.assertTrue(truncated)
        self.assertLessEqual(ds.count_tokens(window), 200)
        self.assertEqual(end, len(window))

    def test_window_offset_past_end(self):
        window, truncated, end, remaining = ds.window_text("abc", 10, 100)
        self.assertEqual(window, "")
        self.assertFalse(truncated)
        self.assertEqual(remaining, 0)

    def test_window_full_fit(self):
        window, truncated, end, remaining = ds.window_text("短文本", 0, 100)
        self.assertEqual(window, "短文本")
        self.assertFalse(truncated)

    def test_two_windows_seamless(self):
        cleaned = ds.clean_markdown(load("fetch_en.json")["content"])
        w1, t1, end1, _ = ds.window_text(cleaned, 0, 300)
        w2, t2, end2, _ = ds.window_text(cleaned, end1, 300)
        self.assertTrue(t1)
        self.assertEqual(w1 + w2, cleaned[:end2])  # 无缝拼接断言（M3 验收项）


class TestFetchContract(unittest.TestCase):
    def test_format_with_truncation(self):
        data = load("fetch_en.json")
        out = ds.format_fetch("https://example.com", data["title"], data["content"], 0, 300)
        lines = out.split("\n")
        self.assertEqual(lines[0], ds.FETCH_GUARD)
        self.assertRegex(
            lines[1],
            r"^# fetch https://example\.com \| ~\d+ tokens \| truncated: true \| offset: 0 \| contract: v1$")
        self.assertEqual(lines[2], data["title"])
        self.assertRegex(lines[-1], r"^## 已截断，剩余约 \d+ tokens，续读: fetch https://example\.com --offset \d+$")

    def test_format_without_truncation(self):
        out = ds.format_fetch("https://example.com", "T", "短内容", 0, 100)
        self.assertIn("truncated: false", out)
        self.assertNotIn("已截断", out)


class TestFetchUrlValidation(unittest.TestCase):
    """URL 校验先于网络与密钥，可离线测试。"""

    def test_non_http_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli(["fetch", "ftp://example.com"], tmp)
        self.assertEqual(code, 2)
        self.assertIn("http(s)", out)

    def test_userinfo_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli(["fetch", "https://user:pass@example.com"], tmp)
        self.assertEqual(code, 2)
        self.assertIn("用户名或密码", out)

    def test_no_key_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli(["fetch", "https://example.com"], tmp)
        self.assertEqual(code, 2)
        self.assertIn("platform.deepseek.com", out)


if __name__ == "__main__":
    unittest.main()
