import json
from pathlib import Path
from typing import Any

from forge.paths import ProjectPaths


class TaskBoard(ProjectPaths):
    def __init__(
        self,
        project_root: str | Path | None = None,
        tasks_path: str = ".harness/tasks.json",
    ):
        super().__init__(project_root)
        self.tasks_path = self.resolve_project_path(tasks_path)
        self.tasks_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def load(self) -> list[dict[str, Any]]:
        if not self.tasks_path.exists():
            return []

        try:
            return json.loads(
                self.tasks_path.read_text(
                    encoding="utf-8",
                )
            )
        except json.JSONDecodeError:
            return []

    def save(self, tasks: list[dict[str, Any]]) -> None:
        self.tasks_path.write_text(
            json.dumps(
                tasks,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def create(self, title: str, details: str = "") -> dict[str, Any]:
        tasks = self.load()
        task = {
            "id": len(tasks) + 1,
            "title": title,
            "details": details,
            "status": "pending",
        }

        tasks.append(task)
        self.save(tasks)

        return task

    def update(self, task_id: int, status: str) -> dict[str, Any]:
        tasks = self.load()

        for task in tasks:
            if task.get("id") == task_id:
                task["status"] = status
                self.save(tasks)
                return task

        raise ValueError(f"Task not found: {task_id}")
