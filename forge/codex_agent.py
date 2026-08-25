import json
from pathlib import Path

from forge.conversation import Conversation
from forge.model.codex_app_server import CodexAppServerClient
from forge.observability import EventLogger
from forge.tool_display import summarize_tool_arguments
from forge.tools.approval import ApprovalGate


class CodexAgent:
    def __init__(
        self,
        model: str | None,
        project_root: str | Path,
        tool_registry,
        developer_instructions: str,
        event_logger=None,
        client=None,
    ):
        self.client = client or CodexAppServerClient()
        self.project_root = Path(project_root).resolve()
        self.tools = tool_registry
        self.developer_instructions = developer_instructions
        self.events = event_logger or EventLogger(project_root=self.project_root)
        self.approval = ApprovalGate()
        self.model = type(
            "CodexModelInfo",
            (),
            {"provider": "codex", "model": model or "account default"},
        )()
        self.requested_model = model
        self.conversation = Conversation()
        self.conversation.add_system(developer_instructions)
        self.conversation_summary = None
        self.summarized_turns = 0

    def _dynamic_tools(self) -> list[dict]:
        tools = []
        for schema in self.tools.schemas():
            function = schema["function"]
            tools.append(
                {
                    "name": function["name"],
                    "description": function["description"],
                    "inputSchema": function["parameters"],
                }
            )
        return tools

    def _ensure_thread(self) -> None:
        if self.client.thread_id:
            return

        self.client.start_thread(
            project_root=self.project_root,
            dynamic_tools=self._dynamic_tools(),
            developer_instructions=(
                self.developer_instructions
                + "\n\nUse the HarnessAgent dynamic tools for all project file, "
                "shell, memory, task, skill, delegation, verification, and "
                "security operations. Do not use built-in file or shell tools."
            ),
            model=self.requested_model,
        )

    def _handle_server_request(self, request: dict) -> dict:
        method = request.get("method")
        if method != "item/tool/call":
            return {"success": False, "contentItems": []}

        params = request.get("params", {})
        tool_name = params.get("tool", "")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            arguments = {}

        print("\n[tool] " + summarize_tool_arguments(tool_name, arguments))
        self.events.record(
            "tool_call",
            {"name": tool_name, "arguments": arguments},
        )

        if self.approval.requires_approval(tool_name) and not self.approval.ask(
            tool_name,
            arguments,
        ):
            result = {"success": False, "error": "User denied the action"}
        else:
            result = self.tools.execute(tool_name, arguments)

        self.events.record(
            "tool_result",
            {"name": tool_name, "success": result.get("success")},
        )
        return {
            "success": bool(result.get("success")),
            "contentItems": [
                {
                    "type": "inputText",
                    "text": json.dumps(result, ensure_ascii=False, default=str),
                }
            ],
        }

    def run(self, user_input: str) -> str:
        self._ensure_thread()
        self.conversation.add_user(user_input)
        self.events.record("user_message", {"length": len(user_input)})

        response = self.client.run_turn(
            user_input,
            server_request_handler=self._handle_server_request,
        )
        self.conversation.add_assistant(response)
        self.events.record(
            "model_response",
            {"has_tool_calls": False, "content_length": len(response)},
        )
        return response

    def reset_conversation(self) -> None:
        self.client.reset_thread()
        self.conversation = Conversation()
        self.conversation.add_system(self.developer_instructions)
        self.conversation_summary = None
        self.summarized_turns = 0

    def available_models(self) -> list[dict]:
        return self.client.list_models()

    def set_model(self, model: str) -> None:
        self.requested_model = model
        self.model.model = model
        self.reset_conversation()

    def close(self) -> None:
        self.client.close()
