import unittest
from types import SimpleNamespace

from forge.agent import Agent
from forge.conversation import Conversation
from forge.tools.registry import ToolRegistry


class FakeModel:
    def __init__(self):
        self.calls = []

    def generate(self, messages, tools=None):
        self.calls.append({
            "messages": messages,
            "tools": tools,
        })

        first_message = messages[0]["content"]

        if "You compact conversation history" in first_message:
            return SimpleNamespace(
                content="The user discussed earlier agent work.",
                tool_calls=None,
            )

        return SimpleNamespace(
            content="Done",
            tool_calls=None,
        )


class AgentContextTests(unittest.TestCase):
    def test_agent_compacts_old_history_and_includes_summary(self):
        model = FakeModel()
        conversation = Conversation()
        conversation.add_system("You are a test agent.")

        for index in range(9):
            conversation.add_user(f"old request {index}")
            conversation.add_assistant(f"old answer {index}")

        agent = Agent(
            model=model,
            conversation=conversation,
            tool_registry=ToolRegistry(),
        )

        response = agent.run("new request")

        self.assertEqual(response, "Done")
        self.assertEqual(
            agent.conversation_summary,
            "The user discussed earlier agent work.",
        )

        final_call = model.calls[-1]
        final_messages = final_call["messages"]

        self.assertTrue(
            any(
                message["role"] == "system"
                and message["content"].startswith(
                    "Summary of earlier conversation:"
                )
                for message in final_messages
            )
        )


if __name__ == "__main__":
    unittest.main()
