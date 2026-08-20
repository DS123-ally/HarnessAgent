from pathlib import Path

from forge.paths import ProjectPaths


class SkillManager(ProjectPaths):
    def __init__(
        self,
        project_root: str | Path | None = None,
        skills_dir: str = ".harness/skills",
    ):
        super().__init__(project_root)
        self.skills_dir = self.resolve_project_path(skills_dir)
        self.skills_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def list_skills(self) -> list[dict[str, str]]:
        skills = []

        for path in sorted(self.skills_dir.glob("*.md")):
            content = path.read_text(
                encoding="utf-8",
                errors="replace",
            )
            first_line = content.splitlines()[0] if content else path.stem

            skills.append({
                "name": path.stem,
                "path": self.display_path(path),
                "title": first_line.lstrip("# ").strip(),
            })

        return skills

    def read_skill(self, name: str) -> dict[str, str]:
        if "/" in name or "\\" in name or ".." in name:
            raise ValueError(f"Invalid skill name: {name}")

        path = self.resolve_project_path(
            self.skills_dir / f"{name}.md"
        )

        if not path.exists():
            raise FileNotFoundError(f"Skill not found: {name}")

        if not path.is_file():
            raise ValueError(f"Not a skill file: {name}")

        return {
            "name": name,
            "path": self.display_path(path),
            "content": path.read_text(
                encoding="utf-8",
                errors="replace",
            ),
        }
