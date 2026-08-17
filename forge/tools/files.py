from pathlib import Path

from forge.tools.base import Tool


class ReadFileTool(Tool):
    name = "read_file"

    description = "Read the contents of a text file from the current project."

    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path of the file to read"
            }
        },
        "required": ["path"]
    }

    def execute(self, **kwargs):
        file_path = kwargs.get("path")

        if not file_path:
            return {
                "success": False,
                "error": "Missing path"
            }

        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }

        if not path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {file_path}"
            }

        try:
            content = path.read_text(
                encoding="utf-8",
                errors="replace"
            )

            return {
                "success": True,
                "path": file_path,
                "content": content
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }