import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forge.paths import ProjectPaths


class EventLogger(ProjectPaths):
    def __init__(
        self,
        project_root: str | Path | None = None,
        log_path: str = ".harness/events.jsonl",
    ):
        super().__init__(project_root)
        self.log_path = self.resolve_project_path(log_path)
        self.log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def record(self, event_type: str, payload: dict[str, Any]) -> None:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "payload": payload,
        }

        with self.log_path.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(
                json.dumps(
                    event,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )

    def tail(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []

        lines = self.log_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()

        events = []

        for line in lines[-limit:]:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        return events
