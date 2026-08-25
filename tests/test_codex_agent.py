import unittest
from collections import deque
from pathlib import Path

from forge.codex_agent import CodexAgent
from forge.model.codex_app_server import CodexAppServerClient
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

    def run_turn(
        self,
        prompt,
        server_request_handler,
        on_text_delta=None,
    ):
        result = server_request_handler(
            {
                "method": "item/tool/call",
                "params": {"tool": "echo", "arguments": {"text": prompt}},
            }
        )
        self.tool_result = result
        if on_text_delta:
            on_text_delta("fin")
            on_text_delta("ished")
        return "finished"

    def reset_thread(self):
        self.thread_id = None

    def list_models(self):
        return [
            {
                "id": "codex-model",
                "model": "codex-model",
                "displayName": "Codex Model",
                "isDefault": True,
            }
        ]

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

    def test_streams_deltas_and_stores_completed_response(self):
        tools = ToolRegistry()
        tools.register(EchoTool())
        agent = CodexAgent(
            model=None,
            project_root=Path.cwd(),
            tool_registry=tools,
            developer_instructions="Test instructions",
            client=FakeCodexClient(),
        )
        deltas = []

        response = agent.run_stream("hello", deltas.append)

        self.assertEqual(deltas, ["fin", "ished"])
        self.assertEqual(response, "finished")
        self.assertEqual(
            agent.conversation.messages[-1],
            {"role": "assistant", "content": "finished"},
        )

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

    def test_lists_and_switches_codex_models(self):
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

        models = agent.available_models()
        agent.set_model(models[0]["model"])

        self.assertEqual(agent.model.model, "codex-model")
        self.assertEqual(agent.requested_model, "codex-model")
        self.assertIsNone(client.thread_id)


class CodexAppServerStreamingTests(unittest.TestCase):
    def test_run_turn_emits_deltas_and_returns_completed_message(self):
        client = CodexAppServerClient.__new__(CodexAppServerClient)
        client.thread_id = "thread-1"
        client._notifications = deque(
            [
                {
                    "method": "item/agentMessage/delta",
                    "params": {"delta": "Hel"},
                },
                {
                    "method": "item/agentMessage/delta",
                    "params": {"delta": "lo"},
                },
                {
                    "method": "item/completed",
                    "params": {
                        "item": {"type": "agentMessage", "text": "Hello"}
                    },
                },
                {
                    "method": "turn/completed",
                    "params": {
                        "turn": {"id": "turn-1", "status": "completed"}
                    },
                },
            ]
        )
        client.request = lambda *args, **kwargs: {"turn": {"id": "turn-1"}}
        deltas = []

        response = client.run_turn("hello", lambda request: {}, deltas.append)

        self.assertEqual(deltas, ["Hel", "lo"])
        self.assertEqual(response, "Hello")


if __name__ == "__main__":
    unittest.main()
