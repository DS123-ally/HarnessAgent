from pathlib import Path


def load_project_instructions(project_root: str | Path | None = None) -> str:
    root = Path(project_root or Path.cwd())
    path = root / "AGENTS.md"

    if not path.exists():
        return ""

    return path.read_text(
        encoding="utf-8"
    )
