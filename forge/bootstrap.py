from pathlib import Path

from forge.agent import Agent
from forge.codex_agent import CodexAgent
from forge.conversation import Conversation
from forge.context.instructions import load_project_instructions
from forge.model.lmstudio import LMStudioProvider, OpenAICompatibleProvider
from forge.observability import EventLogger
from forge.orchestration import TaskBoard
from forge.security import SecurityPolicy
from forge.skills import SkillManager
from forge.state import JsonStateStore
from forge.subagents import SubagentRegistry
from forge.tools.files import (
    CreateDirectoryTool,
    DeleteDirectoryTool,
    DeleteFileTool,
    EditFileTool,
    ListFilesTool,
    ReadFileTool,
    SearchFilesTool,
    WriteFileTool,
)
from forge.tools.memory import RecallMemoryTool, RememberTool
from forge.tools.observability import ShowEventsTool
from forge.tools.registry import ToolRegistry
from forge.tools.security import ShowSecurityPolicyTool
from forge.tools.shell import RunCommandTool
from forge.tools.skills import ListSkillsTool, ReadSkillTool
from forge.tools.subagents import DelegateTaskTool, ListDelegationsTool
from forge.tools.tasks import CreateTaskTool, ListTasksTool, UpdateTaskTool
from forge.tools.verification import VerifyProjectTool


DEFAULT_MODEL_ID = "google/gemma-4-e4b"
DEFAULT_PROVIDER = "lmstudio"
DEFAULT_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def build_system_prompt(instructions: str) -> str:
    return f"""
You are HarnessAgent, a coding agent.

Use:
- list_files to discover project structure.
- search_files to locate code.
- read_file before making claims about file contents.
- create_directory to create folders inside the project.
- write_file to create new files.
- edit_file for small modifications to existing files.
- delete_directory only when the user explicitly asks to remove a folder.
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


def build_tool_registry(project_root: str | Path | None = None) -> ToolRegistry:
    tools = ToolRegistry()
    security_policy = SecurityPolicy(project_root=project_root)
    event_logger = EventLogger(
        project_root=project_root,
        security_policy=security_policy,
    )
    memory_store = JsonStateStore(project_root=project_root)
    skill_manager = SkillManager(project_root=project_root)
    task_board = TaskBoard(project_root=project_root)
    subagent_registry = SubagentRegistry(project_root=project_root)

    for tool in (
        ReadFileTool(
            project_root=project_root,
            security_policy=security_policy,
        ),
        ListFilesTool(
            project_root=project_root,
            security_policy=security_policy,
        ),
        SearchFilesTool(
            project_root=project_root,
            security_policy=security_policy,
        ),
        CreateDirectoryTool(
            project_root=project_root,
            security_policy=security_policy,
        ),
        DeleteDirectoryTool(
            project_root=project_root,
            security_policy=security_policy,
        ),
        WriteFileTool(
            project_root=project_root,
            security_policy=security_policy,
        ),
        DeleteFileTool(
            project_root=project_root,
            security_policy=security_policy,
        ),
        EditFileTool(
            project_root=project_root,
            security_policy=security_policy,
        ),
        RunCommandTool(
            project_root=project_root,
            security_policy=security_policy,
        ),
        ListSkillsTool(manager=skill_manager),
        ReadSkillTool(manager=skill_manager),
        RememberTool(store=memory_store),
        RecallMemoryTool(store=memory_store),
        CreateTaskTool(task_board=task_board),
        UpdateTaskTool(task_board=task_board),
        ListTasksTool(task_board=task_board),
        DelegateTaskTool(registry=subagent_registry),
        ListDelegationsTool(registry=subagent_registry),
        VerifyProjectTool(project_root=project_root),
        ShowEventsTool(logger=event_logger),
        ShowSecurityPolicyTool(security_policy=security_policy),
    ):
        tools.register(tool)

    return tools


def build_agent(
    model_id: str = DEFAULT_MODEL_ID,
    project_root: str | Path | None = None,
    provider: str = DEFAULT_PROVIDER,
    base_url: str | None = None,
    api_key_env: str | None = None,
) -> Agent:
    project_root = Path(project_root or Path.cwd()).resolve()
    provider = provider.lower()

    if provider == "codex":
        tools = build_tool_registry(project_root=project_root)
        instructions = build_system_prompt(
            load_project_instructions(project_root)
        )
        requested_model = None if model_id == DEFAULT_MODEL_ID else model_id
        return CodexAgent(
            model=requested_model,
            project_root=project_root,
            tool_registry=tools,
            developer_instructions=instructions,
            event_logger=EventLogger(project_root=project_root),
        )
    elif provider == "lmstudio":
        model = LMStudioProvider(model=model_id)
    elif provider == "openai":
        model = OpenAICompatibleProvider(
            model=model_id,
            provider=provider,
            api_key_env=api_key_env or "OPENAI_API_KEY",
        )
    elif provider == "gemini":
        model = OpenAICompatibleProvider(
            model=model_id,
            provider=provider,
            base_url=base_url or DEFAULT_GEMINI_BASE_URL,
            api_key_env=api_key_env or "GEMINI_API_KEY",
        )
    elif provider == "openai-compatible":
        if not base_url:
            raise ValueError("--base-url is required for openai-compatible provider")

        model = OpenAICompatibleProvider(
            model=model_id,
            provider=provider,
            base_url=base_url,
            api_key_env=api_key_env or "OPENAI_API_KEY",
        )
    else:
        raise ValueError(f"Unknown model provider: {provider}")

    conversation = Conversation()
    conversation.add_system(
        build_system_prompt(load_project_instructions(project_root))
    )
    event_logger = EventLogger(project_root=project_root)

    return Agent(
        model=model,
        conversation=conversation,
        tool_registry=build_tool_registry(project_root=project_root),
        event_logger=event_logger,
    )
