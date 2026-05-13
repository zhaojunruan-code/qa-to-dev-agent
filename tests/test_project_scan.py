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

    def test_filters_package_cache_and_uniapp_build_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".pnpm-store" / "v3").mkdir(parents=True)
            (root / ".pnpm-store" / "v3" / "noise.js").write_text("hidden", encoding="utf-8")
            (root / "unpackage" / "dist").mkdir(parents=True)
            (root / "unpackage" / "dist" / "built.js").write_text("built", encoding="utf-8")
            (root / "src" / "pages" / "mine").mkdir(parents=True)
            (root / "src" / "pages" / "misc").mkdir(parents=True)
            for index in range(120):
                (root / "src" / "pages" / "misc" / f"noise-{index}.vue").write_text(
                    "<template>noise</template>",
                    encoding="utf-8",
                )
            (root / "src" / "pages" / "mine" / "orders.vue").write_text("<template>orders</template>", encoding="utf-8")
            (root / "src" / "components" / "order").mkdir(parents=True)
            (root / "src" / "components" / "order" / "StatusTabs.vue").write_text("<template>tabs</template>", encoding="utf-8")
            (root / "pages.json").write_text('{"pages":["src/pages/mine/orders"]}', encoding="utf-8")

            context = scan_project(str(root), qa_input="我的订单状态切换消失了")
            markdown = context.to_markdown()

            self.assertIn("pages.json", context.sample_tree[:3])
            self.assertIn("src/pages/mine/orders.vue", context.key_code_locations)
            self.assertIn("src/components/order/StatusTabs.vue", context.key_code_locations)
            self.assertNotIn(".pnpm-store", markdown)
            self.assertNotIn("unpackage", markdown)

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
