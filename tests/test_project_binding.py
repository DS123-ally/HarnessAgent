import tempfile
import unittest
from pathlib import Path

from forge.bootstrap import build_tool_registry
from forge.context.instructions import load_project_instructions


class ProjectBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_registry_tools_use_selected_project_root(self):
        skills_dir = self.project_root / ".harness" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "demo.md").write_text(
            "# Demo\n",
            encoding="utf-8",
        )

        tools = build_tool_registry(project_root=self.project_root)

        memory_result = tools.execute(
            "remember",
            {
                "text": "Project-specific memory"
            },
        )
        skills_result = tools.execute(
            "list_skills",
            {},
        )

        self.assertTrue(memory_result["success"])
        self.assertTrue((self.project_root / ".harness" / "state.json").exists())
        self.assertEqual(skills_result["skills"][0]["name"], "demo")

    def test_instructions_load_from_selected_project_root(self):
        (self.project_root / "AGENTS.md").write_text(
            "Use this project.",
            encoding="utf-8",
        )

        self.assertEqual(
            load_project_instructions(self.project_root),
            "Use this project.",
        )


if __name__ == "__main__":
    unittest.main()
