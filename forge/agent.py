import json

from forge.context import ContextAssembler, ContextConfig
from forge.observability import EventLogger
from forge.tools.approval import ApprovalGate


class Agent:
    def __init__(
        self,
        model,
        conversation,
        tool_registry,
        event_logger=None,
    ):
        self.model = model
        self.conversation = conversation
        self.tools = tool_registry
        self.events = event_logger or EventLogger()
        
        self.approval = ApprovalGate()

        # Context management configuration
        self.context = ContextAssembler(
            ContextConfig(
                max_context_tokens=16_000,
                reserve_response_tokens=4_000,
                recent_turns=8,
                max_tool_output_chars=12_000,
            )
        )
        self.conversation_summary = None
        self.summarized_turns = 0

    def _compact_history(self, history: list[dict]):

        old_history, new_summarized_count = (
            self.context.get_unsummarized_old_history(
                history,
                self.summarized_turns,
            )
        )

        # Nothing new to summarize
        if not old_history:
            return

        old_history_text = json.dumps(
            old_history,
            ensure_ascii=False,
            default=str,
            indent=2,
        )

        existing_summary = (
            self.conversation_summary
            or "No previous summary."
        )

        summary_messages = [
            {
                "role": "system",
                "content": (
                    "You compact conversation history for a coding agent. "
                    "Preserve important user requests, decisions, file names, "
                    "code changes, tool results, errors, project state, and "
                    "unfinished tasks. Remove repetition and unnecessary chatter. "
                    "Return only the compact summary."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Existing conversation summary:\n\n"
                    f"{existing_summary}\n\n"
                    "New old conversation to merge into the summary:\n\n"
                    f"{old_history_text}"
                ),
            },
        ]

        response = self.model.generate(
            messages=summary_messages,
            tools=[],
        )

        summary = response.content or ""

        if summary.strip():
            self.conversation_summary = summary.strip()
            self.summarized_turns = new_summarized_count

    def run(self, user_input: str):

        self.conversation.add_user(user_input)
        self.events.record(
            "user_message",
            {
                "length": len(user_input),
            },
        )

        while True:

            raw_messages = self.conversation.get_messages()

            system_messages = [
                message
                for message in raw_messages
                if message.get("role") == "system"
            ]

            history = [
                message
                for message in raw_messages
                if message.get("role") != "system"
            ]

            try:
                self._compact_history(history)
            except Exception as exc:
                print(f"\n[context] Summary skipped: {exc}")

            recent_history = self.context.get_recent_history(
                history
            )

            summary_messages = []

            if self.conversation_summary:
                summary_messages.append({
                    "role": "system",
                    "content": (
                        "Summary of earlier conversation:\n\n"
                        + self.conversation_summary
                    ),
                })

            messages = (
                system_messages
                + summary_messages
                + recent_history
            )

            messages = self.context.enforce_budget(
                messages
            )

            response = self.model.generate(
                messages=messages,
                tools=self.tools.schemas()
            )
            self.events.record(
                "model_response",
                {
                    "has_tool_calls": bool(response.tool_calls),
                    "content_length": len(response.content or ""),
                },
            )

            # No tool call -> final answer
            if not response.tool_calls:

                content = response.content or ""

                self.conversation.add_assistant(
                    content
                )

                return content

            # Add assistant tool-call message to history
            assistant_message = {
                "role": "assistant",
                "content": response.content,
                "tool_calls": []
            }

            for tool_call in response.tool_calls:
                assistant_message["tool_calls"].append({
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })

            self.conversation.messages.append(
                assistant_message
            )

            # Execute tool calls
            for tool_call in response.tool_calls:

                tool_name = tool_call.function.name

                arguments = json.loads(
                    tool_call.function.arguments
                )

                print(
                    f"\n[tool] {tool_name}({arguments})"
                )
                self.events.record(
                    "tool_call",
                    {
                        "name": tool_name,
                        "arguments": arguments,
                    },
                )

                # Check if tool requires user approval
                if self.approval.requires_approval(
                    tool_name
                ):
                    approved = self.approval.ask(
                        tool_name,
                        arguments
                    )

                    if not approved:
                        result = {
                            "success": False,
                            "error": "User denied the action"
                        }

                    else:
                        result = self.tools.execute(
                            tool_name,
                            arguments
                        )

                else:
                    result = self.tools.execute(
                        tool_name,
                        arguments
                    )

                self.events.record(
                    "tool_result",
                    {
                        "name": tool_name,
                        "success": result.get("success"),
                    },
                )

                # Store complete tool result in conversation history.
                # ContextAssembler will truncate it only when
                # preparing context for the model.
                self.conversation.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        result,
                        ensure_ascii=False,
                        default=str
                    )
                })
