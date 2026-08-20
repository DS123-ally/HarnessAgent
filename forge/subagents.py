import json
from pathlib import Path
from typing import Any

from forge.paths import ProjectPaths


class SubagentRegistry(ProjectPaths):
    def __init__(
        self,
        project_root: str | Path | None = None,
        subagents_path: str = ".harness/subagents.json",
    ):
        super().__init__(project_root)
        self.subagents_path = self.resolve_project_path(subagents_path)
        self.subagents_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def load(self) -> list[dict[str, Any]]:
        if not self.subagents_path.exists():
            return []

        try:
            return json.loads(
                self.subagents_path.read_text(
                    encoding="utf-8",
                )
            )
        except json.JSONDecodeError:
            return []

    def save(self, subagents: list[dict[str, Any]]) -> None:
        self.subagents_path.write_text(
            json.dumps(
                subagents,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def delegate(
        self,
        name: str,
        task: str,
        instructions: str = "",
    ) -> dict[str, Any]:
        subagents = self.load()

        delegation = {
            "id": len(subagents) + 1,
            "name": name,
            "task": task,
            "instructions": instructions,
            "status": "delegated",
        }

        subagents.append(delegation)
        self.save(subagents)

        return delegation
