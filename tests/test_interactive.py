from __future__ import annotations

import argparse
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from qa_to_dev_agent.cli import main
from qa_to_dev_agent.confirm import confirm_typed
from qa_to_dev_agent.interactive import handle_interactive_line, run_interactive
from qa_to_dev_agent.runner import run_batch
from qa_to_dev_agent.session import InteractiveSession


def make_args(**overrides: object) -> argparse.Namespace:
    data = {
        "project": None,
        "input": None,
        "input_file": None,
        "docs_file": [],
        "docs_url": [],
        "docs_timeout": 15,
        "max_files": 80,
        "print_prompt": False,
        "local_only": True,
        "output": None,
        "output_dir": None,
        "create_issue": False,
        "issue_mode": "local",
        "issue_dir": "docs/issues",
        "issue_title": None,
        "issue_repository": None,
        "base_url": None,
        "api_key": None,
        "model": None,
        "http_referer": None,
        "app_title": None,
    }
    data.update(overrides)
    return argparse.Namespace(**data)


class InteractiveTests(unittest.TestCase):
    def test_plain_text_appends_to_qa_input(self) -> None:
        outputs: list[str] = []
        session = InteractiveSession()

        done = handle_interactive_line(session, make_args(), "button text is wrong", output_func=outputs.append)

        self.assertFalse(done)
        self.assertEqual(session.qa_input, "button text is wrong")
        self.assertIn("appended QA input", outputs[-1])

    def test_project_and_scan_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
            outputs: list[str] = []
            session = InteractiveSession()

            handle_interactive_line(session, make_args(), f"/project {tmp}", output_func=outputs.append)
            handle_interactive_line(session, make_args(), "login copy needs updating", output_func=outputs.append)
            handle_interactive_line(session, make_args(), "/scan", output_func=outputs.append)

            self.assertEqual(session.project, tmp)
            self.assertIsNotNone(session.context)
            self.assertIn("scanned", outputs[-1])

    def test_generate_local_then_save_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            output = Path(tmp) / "task.md"
            outputs: list[str] = []
            session = InteractiveSession(project=str(project))
            args = make_args(output=str(output))

            handle_interactive_line(session, args, "need local task", output_func=outputs.append)
            handle_interactive_line(session, args, "/generate --local", output_func=outputs.append)
            handle_interactive_line(session, args, f"/save {output}", input_func=lambda _: "n", output_func=outputs.append)

            self.assertFalse(output.exists())
            handle_interactive_line(session, args, f"/save {output}", input_func=lambda _: "y", output_func=outputs.append)
            self.assertTrue(output.exists())

    def test_llm_generation_requires_confirmation_before_client_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outputs: list[str] = []
            session = InteractiveSession(project=tmp)
            args = make_args(api_key="key", model="model")
            handle_interactive_line(session, args, "need llm task", output_func=outputs.append)

            with patch("qa_to_dev_agent.interactive.OpenAICompatibleClient") as client:
                handle_interactive_line(session, args, "/generate --llm", input_func=lambda _: "n", output_func=outputs.append)

            client.assert_not_called()
            self.assertIn("cancelled", outputs[-1])

    def test_remote_issue_uses_typed_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outputs: list[str] = []
            session = InteractiveSession(project=tmp, last_result="# task")
            args = make_args(issue_dir=str(Path(tmp) / "issues"))

            with patch("qa_to_dev_agent.interactive.create_issue") as create_issue:
                handle_interactive_line(
                    session,
                    args,
                    "/issue remote --repo owner/name",
                    input_func=lambda _: "wrong",
                    output_func=outputs.append,
                )

            create_issue.assert_not_called()
            self.assertIn("cancelled", outputs[-1])

    def test_typed_confirmation_accepts_exact_phrase(self) -> None:
        self.assertTrue(confirm_typed("Remote?", "owner/name", input_func=lambda _: "owner/name", output_func=lambda _: None))
        self.assertFalse(confirm_typed("Remote?", "owner/name", input_func=lambda _: "OWNER/name", output_func=lambda _: None))

    def test_batch_project_is_validated_outside_argparse_required(self) -> None:
        with self.assertRaisesRegex(ValueError, "Batch mode requires --project"):
            run_batch(make_args(project=None, input="needs work"))

    def test_main_interactive_starts_without_project(self) -> None:
        stdout = io.StringIO()
        with patch("builtins.input", side_effect=["/status", "/exit"]), patch("sys.stdout", stdout):
            code = main(["--interactive"])

        self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("QA-to-Dev Prompt Agent Interactive", output)
        self.assertIn("Project: not selected", output)

    def test_real_interactive_local_issue_uses_issue_dir_and_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            issue_dir = Path(tmp) / "issues"
            commands = iter([
                "need local issue",
                f"/project {project}",
                "/scan",
                "/generate --local",
                "/issue local",
                "y",
                "/exit",
            ])

            code = run_interactive(
                make_args(issue_dir=str(issue_dir)),
                input_func=lambda _: next(commands),
                output=io.StringIO(),
                error=io.StringIO(),
            )

            self.assertEqual(code, 0)
            self.assertEqual(len(list(issue_dir.glob("*.md"))), 1)

    def test_real_interactive_save_inside_project_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            output = project / "task.md"
            stderr = io.StringIO()
            commands = iter([
                "need saved task",
                f"/project {project}",
                "/scan",
                "/generate --local",
                f"/save {output}",
                "y",
                "/exit",
            ])

            code = run_interactive(
                make_args(),
                input_func=lambda _: next(commands),
                output=io.StringIO(),
                error=stderr,
            )

            self.assertEqual(code, 0)
            self.assertFalse(output.exists())
            self.assertIn("Refusing to write Markdown output inside target project", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
