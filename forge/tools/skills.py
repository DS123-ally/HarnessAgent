from forge.skills import SkillManager
from forge.tools.base import Tool


class ListSkillsTool(Tool):
    name = "list_skills"
    description = "List local HarnessAgent skills available in the project."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def __init__(self, manager: SkillManager | None = None):
        self.manager = manager or SkillManager()

    def execute(self, **kwargs):
        return {
            "success": True,
            "skills": self.manager.list_skills()
        }


class ReadSkillTool(Tool):
    name = "read_skill"
    description = "Read a local HarnessAgent skill by name."
    parameters = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Skill name without .md"
            }
        },
        "required": ["name"]
    }

    def __init__(self, manager: SkillManager | None = None):
        self.manager = manager or SkillManager()

    def execute(self, **kwargs):
        name = kwargs.get("name")

        if not name:
            return {
                "success": False,
                "error": "Missing name"
            }

        try:
            return {
                "success": True,
                "skill": self.manager.read_skill(name)
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }
