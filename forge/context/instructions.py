from pathlib import Path


def load_project_instructions() -> str:
    path = Path("AGENTS.md")

    if not path.exists():
        return ""

    return path.read_text(
        encoding="utf-8"
    )