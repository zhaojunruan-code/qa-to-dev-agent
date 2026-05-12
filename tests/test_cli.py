from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
                "login button copy needs updating",
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
            code = main(["--project", str(missing), "--input", "needs work", "--local-only"])
            self.assertEqual(code, 1)

    def test_print_prompt_does_not_require_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code = main(["--project", tmp, "--input", "needs work", "--print-prompt"])
            self.assertEqual(code, 0)

    def test_create_local_issue_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            issue_dir = Path(tmp) / "issues"
            code = main([
                "--project",
                str(project),
                "--input",
                "need a local issue",
                "--local-only",
                "--create-issue",
                "--issue-title",
                "Local Issue Test",
                "--issue-dir",
                str(issue_dir),
            ])

            self.assertEqual(code, 0)
            issues = list(issue_dir.glob("*.md"))
            self.assertEqual(len(issues), 1)
            self.assertIn("## 验收标准", issues[0].read_text(encoding="utf-8"))

    def test_file_scheme_docs_url_is_not_fetched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            secret = Path(tmp) / "secret.txt"
            secret.write_text("DO_NOT_READ", encoding="utf-8")
            output = Path(tmp) / "task.md"

            with patch("qa_to_dev_agent.documents.urlopen") as mocked_urlopen:
                code = main([
                    "--project",
                    str(project),
                    "--input",
                    "summarize supplemental docs",
                    "--docs-url",
                    secret.as_uri(),
                    "--local-only",
                    "--output",
                    str(output),
                ])

            self.assertEqual(code, 0)
            mocked_urlopen.assert_not_called()
            content = output.read_text(encoding="utf-8")
            self.assertIn("Unsupported document URL scheme", content)
            self.assertNotIn("DO_NOT_READ", content)

    def test_sensitive_input_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            secret = Path(tmp) / ".env.local"
            secret.write_text("SECRET=value", encoding="utf-8")

            code = main(["--project", str(project), "--input-file", str(secret), "--local-only"])

            self.assertEqual(code, 1)

    def test_sensitive_docs_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            secret = Path(tmp) / ".env"
            secret.write_text("SECRET=value", encoding="utf-8")
            output = Path(tmp) / "task.md"

            code = main([
                "--project",
                str(project),
                "--input",
                "docs safety check",
                "--docs-file",
                str(secret),
                "--local-only",
                "--output",
                str(output),
            ])

            self.assertEqual(code, 1)
            self.assertFalse(output.exists())

    def test_lib_docs_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            lib_dir = Path(tmp) / "lib"
            lib_dir.mkdir()
            generated_doc = lib_dir / "generated.md"
            generated_doc.write_text("generated content", encoding="utf-8")

            code = main([
                "--project",
                str(project),
                "--input",
                "docs safety check",
                "--docs-file",
                str(generated_doc),
                "--local-only",
            ])

            self.assertEqual(code, 1)

    def test_dependency_docs_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            dependency_dir = Path(tmp) / "dependencies"
            dependency_dir.mkdir()
            generated_doc = dependency_dir / "generated.md"
            generated_doc.write_text("generated content", encoding="utf-8")

            code = main([
                "--project",
                str(project),
                "--input",
                "docs safety check",
                "--docs-file",
                str(generated_doc),
                "--local-only",
            ])

            self.assertEqual(code, 1)

    def test_dependency_singular_docs_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            dependency_dir = Path(tmp) / "dependency"
            dependency_dir.mkdir()
            generated_doc = dependency_dir / "generated.md"
            generated_doc.write_text("generated content", encoding="utf-8")

            code = main([
                "--project",
                str(project),
                "--input",
                "docs safety check",
                "--docs-file",
                str(generated_doc),
                "--local-only",
            ])

            self.assertEqual(code, 1)

    def test_generated_docs_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            generated_dir = Path(tmp) / "generated"
            generated_dir.mkdir()
            generated_doc = generated_dir / "task.md"
            generated_doc.write_text("generated content", encoding="utf-8")

            code = main([
                "--project",
                str(project),
                "--input",
                "docs safety check",
                "--docs-file",
                str(generated_doc),
                "--local-only",
            ])

            self.assertEqual(code, 1)

    def test_output_inside_target_project_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            output = project / "task.md"

            code = main([
                "--project",
                str(project),
                "--input",
                "output safety check",
                "--local-only",
                "--output",
                str(output),
            ])

            self.assertEqual(code, 1)
            self.assertFalse(output.exists())

    def test_output_dir_inside_target_project_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            output_dir = project / "generated"

            code = main([
                "--project",
                str(project),
                "--input",
                "output safety check",
                "--local-only",
                "--output-dir",
                str(output_dir),
            ])

            self.assertEqual(code, 1)
            self.assertFalse(output_dir.exists())

    def test_issue_backup_inside_target_project_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            issue_dir = project / "docs" / "issues"

            code = main([
                "--project",
                str(project),
                "--input",
                "issue safety check",
                "--local-only",
                "--create-issue",
                "--issue-dir",
                str(issue_dir),
            ])

            self.assertEqual(code, 1)
            self.assertFalse(issue_dir.exists())


if __name__ == "__main__":
    unittest.main()
