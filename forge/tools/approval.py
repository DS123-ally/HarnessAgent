class ApprovalGate:

    APPROVAL_REQUIRED_TOOLS = {
        "write_file",
        "delete_file",
        "edit_file",
        "run_command",
    }

    def requires_approval(self, tool_name: str) -> bool:
        return tool_name in self.APPROVAL_REQUIRED_TOOLS

    def ask(self, tool_name: str, arguments: dict) -> bool:
        print("\n⚠ Approval required")
        print(f"Tool: {tool_name}")
        print(f"Arguments: {arguments}")

        answer = input("Approve? [y/N]: ").strip().lower()

        return answer in {"y", "yes"}