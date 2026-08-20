from forge.tool_display import summarize_tool_arguments


class ApprovalGate:

    APPROVAL_REQUIRED_TOOLS = {
        "write_file",
        "delete_file",
        "edit_file",
        "run_command",
        "remember",
        "create_task",
        "update_task",
        "delegate_task",
        "verify_project",
    }

    def requires_approval(self, tool_name: str) -> bool:
        return tool_name in self.APPROVAL_REQUIRED_TOOLS

    def ask(self, tool_name: str, arguments: dict) -> bool:
        print("\nApproval required")
        print(f"Tool: {tool_name}")
        print(
            "Action: "
            + summarize_tool_arguments(
                tool_name,
                arguments,
            )
        )

        answer = input("Approve? [y/N]: ").strip().lower()

        return answer in {"y", "yes"}
