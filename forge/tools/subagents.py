from forge.subagents import SubagentRegistry
from forge.tools.base import Tool


class DelegateTaskTool(Tool):
    name = "delegate_task"
    description = "Record a task delegation for a named subagent."
    parameters = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Subagent name"
            },
            "task": {
                "type": "string",
                "description": "Task to delegate"
            },
            "instructions": {
                "type": "string",
                "description": "Optional subagent instructions"
            }
        },
        "required": ["name", "task"]
    }

    def __init__(self, registry: SubagentRegistry | None = None):
        self.registry = registry or SubagentRegistry()

    def execute(self, **kwargs):
        name = kwargs.get("name")
        task = kwargs.get("task")

        if not name or not task:
            return {
                "success": False,
                "error": "Missing name or task"
            }

        return {
            "success": True,
            "delegation": self.registry.delegate(
                name=name,
                task=task,
                instructions=kwargs.get("instructions", ""),
            )
        }


class ListDelegationsTool(Tool):
    name = "list_delegations"
    description = "List recorded subagent delegations."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def __init__(self, registry: SubagentRegistry | None = None):
        self.registry = registry or SubagentRegistry()

    def execute(self, **kwargs):
        return {
            "success": True,
            "delegations": self.registry.load()
        }
