"""M4: 管理子命令单测（doctor 三态文案 / stats 统计 / setup 写入与拒绝 / cache clean）。离线。"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_pipeline import CLI, ds, run_cli  # 复用模块加载与 CLI 跑法


class TestWriteKeyFile(unittest.TestCase):
    def test_writes_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = ds.write_key_file(tmp, "sk-testvalue123")
            self.assertEqual(path, Path(tmp) / ".ds-search" / ".env")
            self.assertEqual(path.read_text(encoding="utf-8"),
                             "DEEPSEEK_API_KEY=sk-testvalue123\n")


class TestRenderDoctor(unittest.TestCase):
    """M4 验收：三态输出与预期逐字一致（首行为版本戳，M6 增补）。"""

    def test_state_none(self):
        text, code = ds.render_doctor("3.12.0", "none", None, [], version="v9.9.9")
        lines = text.split("\n")
        self.assertEqual(lines[0], "版本: v9.9.9")
        self.assertEqual(lines[1], "Python: 3.12.0（要求 3.7+）")
        self.assertEqual(lines[2], "KEY: 未配置（-k / 环境变量 / ~/.ds-search/.env 均未发现）")
        self.assertEqual(lines[3], "诊断: 未配置。按 ds_cli.py setup 引导完成配置")
        self.assertEqual(code, 2)

    def test_state_invalid(self):
        text, code = ds.render_doctor("3.12.0", "invalid", None, [], version="v9.9.9")
        self.assertEqual(text.split("\n")[0], "版本: v9.9.9")
        self.assertIn("KEY: 已配置但无效", text)
        self.assertIn("诊断: Key 无效", text)
        self.assertEqual(code, 3)

    def test_state_ok(self):
        text, code = ds.render_doctor("3.12.0", "ok", "校验调用 40 ms", [], version="v9.9.9")
        self.assertEqual(text.split("\n")[0], "版本: v9.9.9")
        self.assertEqual(text.split("\n")[2], "KEY: 有效（校验调用 40 ms）")
        self.assertEqual(code, 0)
        self.assertIn("诊断: 正常", text)

    def test_version_defaults_to_unknown(self):
        text, _ = ds.render_doctor("3.12.0", "none", None, [])
        self.assertEqual(text.split("\n")[0], "版本: unknown")

    def test_read_runtime_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(ds.read_runtime_version(tmp), "unknown")
            skill = Path(tmp) / "runtime.conf"
            skill.write_text("Runtime: Python\nVersion: v0.1.2\nCommand: x\n", encoding="utf-8")
            self.assertEqual(ds.read_runtime_version(tmp), "v0.1.2")


class TestRenderStats(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        ds.cache_set(self.home, {"query": "a", "count": 6, "need_content": False},
                     {"results": []}, meta={"latency_ms": 100, "tokens_est": 500}, now=1)
        ds.cache_set(self.home, {"url": "https://x"},
                     {"title": "t", "content": "c"}, meta={"latency_ms": 300, "tokens_est": 700}, now=2)
        record = ds.cache_get(self.home, {"query": "a", "count": 6, "need_content": False}, now=3)
        ds.cache_record_hit(self.home, {"query": "a", "count": 6, "need_content": False}, record)
        self.files = ds._cache_files(self.home)

    def test_counts_and_averages(self):
        text = ds.render_stats(self.files)
        self.assertIn("缓存记录: 2 条", text)
        self.assertIn("search 1 次 / fetch 1 次", text)
        self.assertIn("平均耗时: 200 ms", text)
        self.assertIn("缓存命中: 1 次", text)
        self.assertIn("~1200 tokens", text)


class TestCacheCleanCli(unittest.TestCase):
    def test_clean_empties_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            ds.cache_set(tmp, {"query": "x", "count": 6, "need_content": False},
                         {"results": []}, meta={}, now=1)
            self.assertTrue(ds.cache_dir(tmp).exists())
            code, out = run_cli(["cache", "clean"], tmp)
            self.assertEqual(code, 0)
            self.assertIn("已清空缓存：1 条", out)
            self.assertEqual(list(ds.cache_dir(tmp).glob("*.json")), [])


class TestSetupCli(unittest.TestCase):
    def test_bad_prefix_rejected_no_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli(["setup", "--key", "not-a-key"], tmp)
        self.assertEqual(code, 2)
        self.assertIn("sk- 开头", out)
        self.assertNotIn("已写入", out)

    def test_interactive_eof_hint(self):
        env_home = tempfile.mkdtemp()
        import os
        env = {"SystemRoot": os.environ.get("SystemRoot", ""),
               "PATH": os.environ.get("PATH", ""),
               "USERPROFILE": env_home, "HOME": env_home}
        proc = subprocess.run([sys.executable, str(CLI), "setup"],
                              capture_output=True, env=env, timeout=30,
                              stdin=subprocess.DEVNULL)
        out = proc.stdout.decode("utf-8", "replace")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("未读到输入", out)


class TestDoctorCliNoKey(unittest.TestCase):
    def test_exit_2_and_exact_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli(["doctor"], tmp)
        self.assertEqual(code, 2)
        self.assertIn("KEY: 未配置（-k / 环境变量 / ~/.ds-search/.env 均未发现）", out)
        self.assertIn("诊断: 未配置", out)


if __name__ == "__main__":
    unittest.main()
