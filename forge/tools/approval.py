class ApprovalGate:

    SAFE_TOOLS = {
        "read_file",
        "list_files",
        "search_files",
    }

    WRITE_TOOLS = {
        "write_file",
    }

    def requires_approval(self, tool_name: str) -> bool:
        return tool_name in self.WRITE_TOOLS

    def ask(self, tool_name: str, arguments: dict) -> bool:

        print("\nApproval required")
        print(f"Tool: {tool_name}")
        print(f"Arguments: {arguments}")

        answer = input(
            "Allow this action? [y/N]: "
        ).strip().lower()

        return answer in {"y", "yes"}