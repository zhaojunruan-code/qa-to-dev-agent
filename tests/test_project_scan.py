from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from qa_to_dev_agent.project_scan import scan_project


class ProjectScanTests(unittest.TestCase):
    def test_detects_python_project_and_skips_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text(
                "[project]\nname='demo'\n[project.scripts]\ndemo='demo:main'\n",
                encoding="utf-8",
            )
            (root / ".env").write_text("SECRET=value\n", encoding="utf-8")
            (root / "generated").mkdir()
            (root / "generated" / "snapshot.py").write_text("SECRET='generated'\n", encoding="utf-8")
            (root / "dependencies").mkdir()
            (root / "dependencies" / "snapshot.py").write_text("SECRET='dependency'\n", encoding="utf-8")
            context = scan_project(str(root), qa_input="demo")

            markdown = context.to_markdown()
            self.assertIn("Python", markdown)
            self.assertNotIn("SECRET", markdown)
            self.assertNotIn(".env", "\n".join(context.sample_tree))
            self.assertNotIn("generated/snapshot.py", "\n".join(context.sample_tree))
            self.assertNotIn("dependencies/snapshot.py", "\n".join(context.sample_tree))

    def test_related_file_candidates_use_input_terms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "login_button.py").write_text("LABEL = 'Login'\n", encoding="utf-8")
            context = scan_project(str(root), qa_input="login button")

            self.assertIn("login_button.py", context.key_code_locations)

    def test_package_json_with_bom_detects_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text(
                '\ufeff{"scripts":{"build":"vite build","test":"vitest","lint":"eslint ."}}',
                encoding="utf-8",
            )
            context = scan_project(str(root), qa_input="build")

            self.assertTrue(any("npm run build" in script for script in context.build_scripts))
            self.assertTrue(any("npm run test" in script for script in context.test_scripts))
            self.assertTrue(any("npm run lint" in script for script in context.test_scripts))


if __name__ == "__main__":
    unittest.main()
