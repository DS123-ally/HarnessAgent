from typing import Any


MAX_PREVIEW_CHARS = 90


def compact_text(value: str) -> str:
    single_line = " ".join(value.split())

    if len(single_line) <= MAX_PREVIEW_CHARS:
        return single_line

    return single_line[:MAX_PREVIEW_CHARS] + "..."


def describe_value(name: str, value: Any) -> str:
    if isinstance(value, str):
        if "\n" in value or len(value) > MAX_PREVIEW_CHARS:
            line_count = len(value.splitlines())
            return (
                f"{name}=<text {len(value)} chars, "
                f"{line_count} lines, preview=\"{compact_text(value)}\">"
            )

        return f'{name}="{value}"'

    return f"{name}={value!r}"


def summarize_tool_arguments(tool_name: str, arguments: dict) -> str:
    if not arguments:
        return tool_name

    important_keys = {
        "write_file": ["path", "content"],
        "edit_file": ["path", "old_text", "new_text"],
        "delete_file": ["path"],
        "read_file": ["path"],
        "list_files": ["path"],
        "search_files": ["query", "path"],
        "run_command": ["command"],
        "remember": ["text"],
        "create_task": ["title", "details"],
        "update_task": ["task_id", "status"],
        "delegate_task": ["name", "task", "instructions"],
        "verify_project": [],
    }

    keys = important_keys.get(
        tool_name,
        list(arguments.keys()),
    )

    parts = [
        describe_value(key, arguments[key])
        for key in keys
        if key in arguments
    ]

    return f"{tool_name} " + ", ".join(parts)
