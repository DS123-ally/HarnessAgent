import json
from pathlib import Path
from typing import Any

from forge.paths import ProjectPaths


class JsonStateStore(ProjectPaths):
    def __init__(
        self,
        project_root: str | Path | None = None,
        state_path: str = ".harness/state.json",
    ):
        super().__init__(project_root)
        self.state_path = self.resolve_project_path(state_path)
        self.state_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def load(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {
                "memories": [],
            }

        try:
            return json.loads(
                self.state_path.read_text(
                    encoding="utf-8",
                )
            )
        except json.JSONDecodeError:
            return {
                "memories": [],
            }

    def save(self, state: dict[str, Any]) -> None:
        self.state_path.write_text(
            json.dumps(
                state,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def append_memory(self, text: str) -> dict[str, Any]:
        state = self.load()
        memories = state.setdefault(
            "memories",
            [],
        )

        memory = {
            "id": len(memories) + 1,
            "text": text,
        }

        memories.append(memory)
        self.save(state)

        return memory

    def search_memories(self, query: str | None = None) -> list[dict[str, Any]]:
        memories = self.load().get(
            "memories",
            [],
        )

        if not query:
            return memories

        normalized_query = query.lower()

        return [
            memory
            for memory in memories
            if normalized_query in memory.get("text", "").lower()
        ]
