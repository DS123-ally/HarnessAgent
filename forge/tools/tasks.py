from forge.orchestration import TaskBoard
from forge.tools.base import Tool


class CreateTaskTool(Tool):
    name = "create_task"
    description = "Create a persistent project task for orchestration."
    parameters = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Short task title"
            },
            "details": {
                "type": "string",
                "description": "Optional task details"
            }
        },
        "required": ["title"]
    }

    def __init__(self, task_board: TaskBoard | None = None):
        self.task_board = task_board or TaskBoard()

    def execute(self, **kwargs):
        title = kwargs.get("title")

        if not title:
            return {
                "success": False,
                "error": "Missing title"
            }

        return {
            "success": True,
            "task": self.task_board.create(
                title=title,
                details=kwargs.get("details", ""),
            )
        }


class UpdateTaskTool(Tool):
    name = "update_task"
    description = "Update a persistent project task status."
    parameters = {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "integer",
                "description": "Task id to update"
            },
            "status": {
                "type": "string",
                "description": "New task status"
            }
        },
        "required": ["task_id", "status"]
    }

    def __init__(self, task_board: TaskBoard | None = None):
        self.task_board = task_board or TaskBoard()

    def execute(self, **kwargs):
        try:
            task = self.task_board.update(
                task_id=int(kwargs["task_id"]),
                status=kwargs["status"],
            )
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }

        return {
            "success": True,
            "task": task
        }


class ListTasksTool(Tool):
    name = "list_tasks"
    description = "List persistent project tasks."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def __init__(self, task_board: TaskBoard | None = None):
        self.task_board = task_board or TaskBoard()

    def execute(self, **kwargs):
        return {
            "success": True,
            "tasks": self.task_board.load()
        }
