import re
from pathlib import Path


def inject_file_references(text: str) -> str:
    matches = re.findall(
        r"@([\w./\\-]+)",
        text
    )

    if not matches:
        return text

    file_context = []

    for file_path in matches:
        path = Path(file_path)

        if not path.exists():
            file_context.append(
                f"\nFile not found: {file_path}"
            )
            continue

        if not path.is_file():
            continue

        content = path.read_text(
            encoding="utf-8",
            errors="replace"
        )

        file_context.append(
            f"""
<file path="{file_path}">
{content}
</file>
"""
        )

    return (
        text
        + "\n\nReferenced project files:\n"
        + "\n".join(file_context)
    )