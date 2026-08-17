from forge.agent import Agent
from forge.conversation import Conversation
from forge.context.instructions import load_project_instructions
from forge.model.lmstudio import LMStudioProvider

from forge.tools.files import ReadFileTool
from forge.tools.registry import ToolRegistry


MODEL_ID = "google/gemma-4-e4b"


model = LMStudioProvider(
    model=MODEL_ID
)

conversation = Conversation()

instructions = load_project_instructions()

conversation.add_system(
    f"""
You are HarnessAgent, a coding agent.

You can inspect project files using tools.

If the user asks about a file and you do not know its contents,
use the read_file tool.

Do not invent file contents.

Project instructions:

{instructions}
"""
)


tools = ToolRegistry()

tools.register(
    ReadFileTool()
)


agent = Agent(
    model=model,
    conversation=conversation,
    tool_registry=tools
)


print("HarnessAgent v0.4")
print("Tools: read_file")
print("Type 'exit' to stop.\n")


while True:

    user_input = input("You > ")

    if user_input.lower() in {
        "exit",
        "quit"
    }:
        break

    response = agent.run(
        user_input
    )

    print(
        f"\nHarnessAgent > {response}\n"
    )