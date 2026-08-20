from forge.agent import Agent
from forge.conversation import Conversation
from forge.context.instructions import load_project_instructions
from forge.model.lmstudio import LMStudioProvider

from forge.tools.files import ReadFileTool,ListFilesTool,EditFileTool,SearchFilesTool,WriteFileTool,DeleteFileTool
from forge.tools.memory import RememberTool, RecallMemoryTool
from forge.tools.observability import ShowEventsTool
from forge.tools.registry import ToolRegistry
from forge.tools.security import ShowSecurityPolicyTool
from forge.tools.shell import RunCommandTool
from forge.tools.skills import ListSkillsTool, ReadSkillTool
from forge.tools.subagents import DelegateTaskTool, ListDelegationsTool
from forge.tools.tasks import CreateTaskTool, ListTasksTool, UpdateTaskTool
from forge.tools.verification import VerifyProjectTool

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
- list_skills and read_skill to load local project skills.
- remember and recall_memory for durable project memory.
- create_task, update_task, and list_tasks for orchestration.
- delegate_task and list_delegations for subagent work tracking.
- verify_project to run the test suite.
- show_events to inspect recent observability events.
- show_security_policy to inspect the active security rules.

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
tools.register(ListSkillsTool())
tools.register(ReadSkillTool())
tools.register(RememberTool())
tools.register(RecallMemoryTool())
tools.register(CreateTaskTool())
tools.register(UpdateTaskTool())
tools.register(ListTasksTool())
tools.register(DelegateTaskTool())
tools.register(ListDelegationsTool())
tools.register(VerifyProjectTool())
tools.register(ShowEventsTool())
tools.register(ShowSecurityPolicyTool())


agent = Agent(
    model=model,
    conversation=conversation,
    tool_registry=tools
)


print("HarnessAgent v0.5")
print("Tools: files, shell, skills, memory, tasks, subagents, verification, events, security")
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
