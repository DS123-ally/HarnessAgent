import unittest
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

from rich.console import Console

from forge.cli import HarnessAgentCli, parse_args
from forge.tools.registry import ToolRegistry


class DummyTool:
    name = "dummy"
    description = "Dummy tool for CLI tests."
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def execute(self, **kwargs):
        return {
            "success": True,
            "ok": True,
        }


class DummyAgent:
    def __init__(self):
        tools = ToolRegistry()
        tools.register(DummyTool())

        self.model = SimpleNamespace(model="test-model")
        self.tools = tools
        self.conversation = SimpleNamespace(
            messages=[
                {
                    "role": "system",
                    "content": "test",
                }
            ]
        )
        self.conversation_summary = None
        self.summarized_turns = 0
        self.prompts = []

    def run(self, prompt):
        self.prompts.append(prompt)
        return "agent response"


class CliTests(unittest.TestCase):
    def make_cli(self):
        output = StringIO()
        console = Console(
            file=output,
            force_terminal=False,
            no_color=True,
        )
        return HarnessAgentCli(
            agent=DummyAgent(),
            project_root=Path.cwd(),
            console=console,
        ), output

    def test_parse_args_supports_once_and_model(self):
        config = parse_args(
            [
                "--model",
                "local-model",
                "--project",
                "sample-project",
                "--once",
                "hello",
                "--no-color",
            ]
        )

        self.assertEqual(config.model, "local-model")
        self.assertEqual(config.project, "sample-project")
        self.assertEqual(config.once, "hello")
        self.assertTrue(config.no_color)

    def test_tools_command_prints_registered_tools(self):
        cli, output = self.make_cli()

        cli.handle_input("/tools")

        self.assertIn("dummy", output.getvalue())

    def test_normal_input_runs_agent(self):
        cli, output = self.make_cli()

        cli.handle_input("hello agent")

        self.assertEqual(cli.agent.prompts, ["hello agent"])
        self.assertIn("agent response", output.getvalue())

    def test_clear_command_keeps_system_messages(self):
        cli, output = self.make_cli()
        cli.agent.conversation.messages.append({
            "role": "user",
            "content": "hello",
        })

        cli.handle_input("/clear")

        self.assertEqual(
            cli.agent.conversation.messages,
            [
                {
                    "role": "system",
                    "content": "test",
                }
            ],
        )
        self.assertIn("Conversation cleared", output.getvalue())


if __name__ == "__main__":
    unittest.main()
