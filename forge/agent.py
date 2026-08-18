import json

from forge.context import ContextAssembler, ContextConfig
from forge.tools.approval import ApprovalGate


class Agent:
    def __init__(
        self,
        model,
        conversation,
        tool_registry
    ):
        self.model = model
        self.conversation = conversation
        self.tools = tool_registry
        
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

    def run(self, user_input: str):

        self.conversation.add_user(user_input)

        while True:

            # Get complete conversation history
            raw_messages = self.conversation.get_messages()

            # Keep system messages separately
            system_messages = [
                message
                for message in raw_messages
                if message.get("role") == "system"
            ]

            # Everything except system messages is conversation history
            history = [
                message
                for message in raw_messages
                if message.get("role") != "system"
            ]

            # ContextAssembler keeps only recent turns
            # and truncates huge tool outputs
            recent_history = self.context.get_recent_history(
                history
            )

            # Final controlled context sent to the model
            messages = system_messages + recent_history

            messages = self.context.enforce_budget(messages)

            response = self.model.generate(
                messages=messages,
                tools=self.tools.schemas()
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