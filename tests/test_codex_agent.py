import unittest
from pathlib import Path

from forge.codex_agent import CodexAgent
from forge.tools.registry import ToolRegistry


class EchoTool:
    name = "echo"
    description = "Return the supplied text."
    parameters = {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    }

    def execute(self, text):
        return {"success": True, "text": text}


class FakeCodexClient:
    def __init__(self):
        self.thread_id = None
        self.thread_options = None
        self.closed = False

    def start_thread(self, **options):
        self.thread_options = options
        self.thread_id = "thread-1"

    def run_turn(self, prompt, server_request_handler):
        result = server_request_handler(
            {
                "method": "item/tool/call",
                "params": {"tool": "echo", "arguments": {"text": prompt}},
            }
        )
        self.tool_result = result
        return "finished"

    def reset_thread(self):
        self.thread_id = None

    def close(self):
        self.closed = True


class CodexAgentTests(unittest.TestCase):
    def test_routes_dynamic_tool_calls_through_harness_registry(self):
        tools = ToolRegistry()
        tools.register(EchoTool())
        client = FakeCodexClient()
        agent = CodexAgent(
            model=None,
            project_root=Path.cwd(),
            tool_registry=tools,
            developer_instructions="Test instructions",
            client=client,
        )

        response = agent.run("hello")

        self.assertEqual(response, "finished")
        self.assertEqual(client.tool_result["success"], True)
        self.assertIn('"text": "hello"', client.tool_result["contentItems"][0]["text"])
        self.assertEqual(
            client.thread_options["dynamic_tools"][0]["name"],
            "echo",
        )
        self.assertEqual(agent.model.provider, "codex")

    def test_reset_starts_a_fresh_codex_thread(self):
        tools = ToolRegistry()
        tools.register(EchoTool())
        client = FakeCodexClient()
        agent = CodexAgent(
            model=None,
            project_root=Path.cwd(),
            tool_registry=tools,
            developer_instructions="Test instructions",
            client=client,
        )
        agent.run("hello")

        agent.reset_conversation()

        self.assertIsNone(client.thread_id)
        self.assertEqual(len(agent.conversation.messages), 1)


if __name__ == "__main__":
    unittest.main()
