class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, tool):
        self.tools[tool.name] = tool

    def get(self, name: str):
        return self.tools.get(name)

    def execute(self, name: str, arguments: dict):
        tool = self.get(name)

        if tool is None:
            return {
                "success": False,
                "error": f"Unknown tool: {name}"
            }

        return tool.execute(**arguments)

    def schemas(self):
        schemas = []

        for tool in self.tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })

        return schemas