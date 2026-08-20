from forge.state import JsonStateStore
from forge.tools.base import Tool


class RememberTool(Tool):
    name = "remember"
    description = "Persist an important memory about the project or user request."
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Memory text to store"
            }
        },
        "required": ["text"]
    }

    def __init__(self, store: JsonStateStore | None = None):
        self.store = store or JsonStateStore()

    def execute(self, **kwargs):
        text = kwargs.get("text")

        if not text:
            return {
                "success": False,
                "error": "Missing text"
            }

        return {
            "success": True,
            "memory": self.store.append_memory(text)
        }


class RecallMemoryTool(Tool):
    name = "recall_memory"
    description = "Recall persisted project memories, optionally filtered by text."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Optional text to search for in memories"
            }
        },
        "required": []
    }

    def __init__(self, store: JsonStateStore | None = None):
        self.store = store or JsonStateStore()

    def execute(self, **kwargs):
        return {
            "success": True,
            "memories": self.store.search_memories(
                kwargs.get("query")
            )
        }
