import tempfile
import unittest
from pathlib import Path

from forge.observability import EventLogger
from forge.orchestration import TaskBoard
from forge.skills import SkillManager
from forge.state import JsonStateStore
from forge.subagents import SubagentRegistry
from forge.tools.shell import RunCommandTool


class RuntimePrimitiveTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_memory_persists_and_filters(self):
        store = JsonStateStore(project_root=self.project_root)

        store.append_memory("Gemma is the local model")
        store.append_memory("Use uv for tests")

        memories = store.search_memories("gemma")

        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0]["text"], "Gemma is the local model")

    def test_skills_are_listed_and_read(self):
        skills_dir = self.project_root / ".harness" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "demo.md").write_text(
            "# Demo Skill\n\nUse for tests.",
            encoding="utf-8",
        )

        manager = SkillManager(project_root=self.project_root)

        self.assertEqual(manager.list_skills()[0]["name"], "demo")
        self.assertIn(
            "Use for tests.",
            manager.read_skill("demo")["content"],
        )

    def test_task_board_and_subagent_registry_persist_records(self):
        task_board = TaskBoard(project_root=self.project_root)
        task = task_board.create("Implement sandbox")
        updated_task = task_board.update(task["id"], "done")

        registry = SubagentRegistry(project_root=self.project_root)
        delegation = registry.delegate(
            name="reviewer",
            task="Review sandbox",
        )

        self.assertEqual(updated_task["status"], "done")
        self.assertEqual(registry.load()[0]["id"], delegation["id"])

    def test_event_logger_records_recent_events(self):
        logger = EventLogger(project_root=self.project_root)

        logger.record("test_event", {"ok": True})

        events = logger.tail()

        self.assertEqual(events[0]["type"], "test_event")
        self.assertTrue(events[0]["payload"]["ok"])

    def test_shell_runs_in_project_root_and_blocks_destructive_commands(self):
        runner = RunCommandTool(project_root=self.project_root)

        result = runner.execute(command="python -c \"print(__import__('pathlib').Path.cwd())\"")
        blocked = runner.execute(command="git reset --hard")

        self.assertTrue(result["success"])
        self.assertIn(str(self.project_root), result["stdout"])
        self.assertFalse(blocked["success"])
        self.assertIn("blocked", blocked["error"])


if __name__ == "__main__":
    unittest.main()
