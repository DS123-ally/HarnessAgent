from forge.agent import Agent
from forge.conversation import Conversation
from forge.context.instructions import load_project_instructions
from forge.model.lmstudio import LMStudioProvider

from forge.tools.files import ReadFileTool,ListFilesTool,EditFileTool,SearchFilesTool,WriteFileTool,DeleteFileTool
from forge.tools.registry import ToolRegistry
from forge.tools.shell import RunCommandTool


MODEL_ID = "google/gemma-4-e4b"


model = LMStudioProvider(
    model=MODEL_ID
)

conversation = Conversation()

instructions = load_project_instructions()

conversation.add_system(
    f"""
You are HarnessAgent, a coding agent.

Use:
- list_files to discover project structure.
- search_files to locate code.
- read_file before making claims about file contents.
- write_file to create new files.
- edit_file for small modifications to existing files.
- delete_file only when the user explicitly asks to remove a file.

Use run_command when you need to execute code, run tests,
inspect Git state, or verify a change.

After modifying code, prefer verifying the change with an appropriate command.
Never claim that code works unless verification succeeded.

Prefer edit_file over rewriting an entire existing file.

Never invent file contents.

Project instructions:

{instructions}
"""
)


tools = ToolRegistry()

tools.register(
    ReadFileTool()

)
tools.register(ListFilesTool())
tools.register(SearchFilesTool())
tools.register(WriteFileTool())
tools.register(DeleteFileTool())
tools.register(EditFileTool())
tools.register(RunCommandTool())


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