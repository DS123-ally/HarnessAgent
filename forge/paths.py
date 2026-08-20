from pathlib import Path


class ProjectPaths:
    def __init__(self, project_root: str | Path | None = None):
        self.project_root = Path(
            project_root or Path.cwd()
        ).resolve()

    def resolve_project_path(self, path_str: str | Path) -> Path:
        candidate = Path(path_str)

        if not candidate.is_absolute():
            candidate = self.project_root / candidate

        resolved = candidate.resolve(strict=False)

        try:
            resolved.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError(
                f"Path is outside the project root: {path_str}"
            ) from exc

        return resolved

    def display_path(self, path: str | Path) -> str:
        return str(
            Path(path).resolve(strict=False).relative_to(
                self.project_root
            )
        )

    def harness_dir(self) -> Path:
        path = self.project_root / ".harness"
        path.mkdir(
            parents=True,
            exist_ok=True,
        )
        return path
