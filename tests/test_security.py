import tempfile
import unittest
from pathlib import Path

from forge.observability import EventLogger
from forge.security import SecurityPolicy
from forge.tools.files import ReadFileTool, WriteFileTool
from forge.tools.shell import RunCommandTool


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_policy_blocks_denied_paths(self):
        tool = WriteFileTool(project_root=self.project_root)

        result = tool.execute(
            path=".env",
            content="API_KEY=secret",
        )

        self.assertFalse(result["success"])
        self.assertIn("security policy", result["error"])

    def test_read_file_redacts_secret_values(self):
        path = self.project_root / "config.txt"
        path.write_text(
            "api_key = abc123\nnormal = visible",
            encoding="utf-8",
        )

        result = ReadFileTool(
            project_root=self.project_root
        ).execute(path="config.txt")

        self.assertTrue(result["success"])
        self.assertIn("[REDACTED]", result["content"])
        self.assertIn("normal = visible", result["content"])

    def test_shell_blocks_unlisted_and_network_commands(self):
        runner = RunCommandTool(project_root=self.project_root)

        unlisted = runner.execute(command="whoami")
        network = runner.execute(command="curl https://example.com")

        self.assertFalse(unlisted["success"])
        self.assertIn("allowlist", unlisted["error"])
        self.assertFalse(network["success"])
        self.assertIn("blocked", network["error"])

    def test_observability_redacts_sensitive_payloads(self):
        policy = SecurityPolicy(project_root=self.project_root)
        logger = EventLogger(
            project_root=self.project_root,
            security_policy=policy,
        )

        logger.record(
            "tool_call",
            {
                "api_key": "abc123",
                "message": "token = xyz789",
            },
        )

        event = logger.tail()[0]

        self.assertEqual(event["payload"]["api_key"], "[REDACTED]")
        self.assertEqual(event["payload"]["message"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
