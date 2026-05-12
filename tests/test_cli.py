from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from qa_to_dev_agent.cli import main


class CliTests(unittest.TestCase):
    def test_local_only_generates_required_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            (project / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
            output = Path(tmp) / "task.md"

            code = main([
                "--project",
                str(project),
                "--input",
                "登录页按钮文案需要调整",
                "--local-only",
                "--output",
                str(output),
            ])

            self.assertEqual(code, 0)
            content = output.read_text(encoding="utf-8")
            self.assertIn("# 开发任务标题", content)
            self.assertIn("## 当前项目上下文", content)
            self.assertIn("## Codex CLI Prompt", content)

    def test_empty_input_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code = main(["--project", tmp, "--input", "   ", "--local-only"])
            self.assertEqual(code, 1)

    def test_missing_project_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            code = main(["--project", str(missing), "--input", "需要调整", "--local-only"])
            self.assertEqual(code, 1)

    def test_print_prompt_does_not_require_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code = main(["--project", tmp, "--input", "需要调整", "--print-prompt"])
            self.assertEqual(code, 0)

    def test_create_local_issue_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            issue_dir = Path(tmp) / "issues"
            code = main([
                "--project",
                tmp,
                "--input",
                "需要生成本地 Issue",
                "--local-only",
                "--create-issue",
                "--issue-title",
                "本地 Issue 测试",
                "--issue-dir",
                str(issue_dir),
            ])

            self.assertEqual(code, 0)
            issues = list(issue_dir.glob("*.md"))
            self.assertEqual(len(issues), 1)
            self.assertIn("## 验收标准", issues[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
