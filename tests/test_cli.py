import unittest
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from rich.console import Console

from forge.cli import (
    CliConfig,
    HarnessAgentCli,
    main,
    parse_args,
    run_auth_command,
    select_model,
)
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
                "--provider",
                "gemini",
                "--api-key-env",
                "TEST_GEMINI_KEY",
                "--project",
                "sample-project",
                "--once",
                "hello",
                "--no-color",
            ]
        )

        self.assertEqual(config.model, "local-model")
        self.assertEqual(config.provider, "gemini")
        self.assertEqual(config.api_key_env, "TEST_GEMINI_KEY")
        self.assertEqual(config.project, "sample-project")
        self.assertEqual(config.once, "hello")
        self.assertTrue(config.no_color)

    def test_openai_provider_requires_credentials(self):
        with patch.dict("os.environ", {}, clear=True):
            exit_code = main([
                "--provider",
                "openai",
                "--model",
                "gpt-5-codex",
                "--once",
                "hello",
                "--no-color",
            ])

        self.assertEqual(exit_code, 1)

    def test_parse_args_supports_codex_login_status(self):
        config = parse_args(["login", "status", "--no-color"])

        self.assertEqual(config.command, "login")
        self.assertEqual(config.login_action, "status")
        self.assertTrue(config.no_color)

    def test_auth_status_uses_codex_app_server_account(self):
        class FakeClient:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def account(self):
                return {
                    "type": "chatgpt",
                    "email": "person@example.com",
                    "planType": "plus",
                }

        output = StringIO()
        console = Console(file=output, no_color=True)
        config = CliConfig(command="login", login_action="status")

        with patch("forge.cli.CodexAppServerClient", return_value=FakeClient()):
            exit_code = run_auth_command(config, console)

        self.assertEqual(exit_code, 0)
        self.assertIn("person@example.com", output.getvalue())
        self.assertIn("plus", output.getvalue())

    def test_startup_selector_uses_codex_account_default(self):
        output = StringIO()
        console = Console(file=output, no_color=True)
        config = CliConfig()

        with patch.object(console, "input", side_effect=["1", ""]):
            selected = select_model(config, console)

        self.assertEqual(selected.provider, "codex")
        self.assertEqual(selected.model, "google/gemma-4-e4b")
        self.assertIn("Select Model", output.getvalue())

    def test_startup_selector_supports_custom_local_model(self):
        output = StringIO()
        console = Console(file=output, no_color=True)
        config = CliConfig()

        with patch.object(
            console,
            "input",
            side_effect=["3", "my-local-model"],
        ):
            selected = select_model(config, console)

        self.assertEqual(selected.provider, "lmstudio")
        self.assertEqual(selected.model, "my-local-model")

    def test_tools_command_prints_registered_tools(self):
        cli, output = self.make_cli()

        cli.handle_input("/tools")

        self.assertIn("dummy", output.getvalue())

    def test_banner_shows_branded_startup(self):
        cli, output = self.make_cli()

        cli.banner()

        banner = output.getvalue()

        self.assertIn("Welcome to HarnessAgent", banner)
        self.assertIn(r"|_| |_/_/   \_\_| \_\_| \_|", banner)
        self.assertIn(r"/_/   \_\____|_____|_| \_|", banner)
        self.assertIn("Press Enter to continue", banner)

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
