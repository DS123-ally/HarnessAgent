import json
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

    def run(self, user_input: str):

        self.conversation.add_user(user_input)

        while True:

            response = self.model.generate(
                messages=self.conversation.get_messages(),
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

                result = self.tools.execute(
                    tool_name,
                    arguments
                )

                if self.approval.requires_approval(tool_name):

                  approved = self.approval.ask(
        tool_name,
        arguments
      )

                if not approved:
                    result = {
                    "success": False,
                    "error": "User denied tool execution"
                }

                else:
                     result = self.tools.execute(
            tool_name,
            arguments
        )       

            self.conversation.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })