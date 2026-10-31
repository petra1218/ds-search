"""安装器编码不变量（2026-10-29 缺陷回归守护）。

背景：install.ps1 曾以无 BOM UTF-8 提交，Windows PowerShell 5.1 按 ANSI/GBK
解析含中文的脚本直接报语法错误——.ps1 含非 ASCII 字符必须带 BOM。
反向约束：install.sh 绝不能带 BOM，否则 shebang 行失效，bash 直接报错。
"""
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"


class InstallerEncodingTests(unittest.TestCase):
    def test_install_ps1_has_utf8_bom(self):
        data = (REPO / "install.ps1").read_bytes()
        self.assertTrue(data.startswith(BOM),
                        "install.ps1 必须为带 BOM 的 UTF-8（Windows PowerShell 5.1 兼容）")
        self.assertIn("安装器".encode("utf-8"), data)

    def test_install_sh_has_no_bom(self):
        data = (REPO / "install.sh").read_bytes()
        self.assertFalse(data.startswith(BOM),
                         "install.sh 带 BOM 会破坏 shebang，bash 无法执行")
        self.assertTrue(data.startswith(b"#!"))

    def test_install_ps1_targets_match_sh(self):
        """两安装器的目标 Agent 集合必须一致，防止单边演进。"""
        ps1 = (REPO / "install.ps1").read_text(encoding="utf-8-sig")
        sh = (REPO / "install.sh").read_text(encoding="utf-8")
        for agent in ("zcode", "claude", "codex", "cursor", "codebuddy", "workbuddy", "reasonx"):
            self.assertIn(f'"{agent}"', ps1, f"install.ps1 缺目标 {agent}")
            self.assertIn(agent, sh, f"install.sh 缺目标 {agent}")

    def test_installers_stamp_version(self):
        """两安装器都必须往 runtime.conf 写 Version 行（doctor 依赖它回显版本）。"""
        ps1 = (REPO / "install.ps1").read_text(encoding="utf-8-sig")
        sh = (REPO / "install.sh").read_text(encoding="utf-8")
        self.assertIn("Version:", ps1)
        self.assertIn("Version:", sh)
        repo_conf = (REPO / "skills" / "ds-search" / "runtime.conf").read_text(encoding="utf-8")
        self.assertIn("Version:", repo_conf)

    def test_install_ps1_git_probe_tolerates_failure(self):
        """PS 5.1 + EAP=Stop 时原生命令 stderr 重定向会抛终止性错误——git 探测必须临时放宽 EAP
        （v0.1.2 回归：非 git 环境（zip 安装）下安装器直接崩溃）。此断言防止被"简化"回去。"""
        ps1 = (REPO / "install.ps1").read_text(encoding="utf-8-sig")
        self.assertIn('$ErrorActionPreference = "Continue"', ps1)
        self.assertIn('$ErrorActionPreference = "Stop"', ps1)
        # 探测失败回退 dev 的分支必须在
        self.assertIn('if (-not $Version) { $Version = "dev" }', ps1)


if __name__ == "__main__":
    unittest.main()
