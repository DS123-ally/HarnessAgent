from forge.observability import EventLogger
from forge.tools.base import Tool


class ShowEventsTool(Tool):
    name = "show_events"
    description = "Show recent HarnessAgent observability events."
    parameters = {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of recent events to show"
            }
        },
        "required": []
    }

    def __init__(self, logger: EventLogger | None = None):
        self.logger = logger or EventLogger()

    def execute(self, **kwargs):
        limit = kwargs.get("limit", 20)

        return {
            "success": True,
            "events": self.logger.tail(
                limit=int(limit)
            )
        }
