from pathlib import Path

from forge.tools.base import Tool


## Read File Tool

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

        ## List File Tool

class ListFilesTool(Tool):
    name = "list_files"

    description = "List files and folders inside a project directory."

    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path to list. Use '.' for project root."
            }
        },
        "required": ["path"]
    }

    def execute(self, **kwargs):
        path_str = kwargs.get("path", ".")

        path = Path(path_str)

        if not path.exists():
            return {
                "success": False,
                "error": f"Path not found: {path_str}"
            }

        if not path.is_dir():
            return {
                "success": False,
                "error": f"Not a directory: {path_str}"
            }

        try:
            items = []

            for item in path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file"
                })

            return {
                "success": True,
                "path": path_str,
                "items": items
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }


        ## Search File Tool


class SearchFilesTool(Tool):
    name = "search_files"

    description = "Search for text inside project files."

    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Text to search for"
            },
            "path": {
                "type": "string",
                "description": "Directory to search in. Use '.' for project root."
            }
        },
        "required": ["query", "path"]
    }

    def execute(self, **kwargs):
        query = kwargs.get("query")
        path_str = kwargs.get("path", ".")

        if not query:
            return {
                "success": False,
                "error": "Missing search query"
            }

        root = Path(path_str)

        if not root.exists():
            return {
                "success": False,
                "error": f"Path not found: {path_str}"
            }

        results = []

        try:
            for file_path in root.rglob("*"):
                if not file_path.is_file():
                    continue

                try:
                    content = file_path.read_text(
                        encoding="utf-8",
                        errors="ignore"
                    )
                except Exception:
                    continue

                for line_number, line in enumerate(
                    content.splitlines(),
                    start=1
                ):
                    if query.lower() in line.lower():
                        results.append({
                            "file": str(file_path),
                            "line": line_number,
                            "text": line.strip()
                        })

            return {
                "success": True,
                "query": query,
                "results": results
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }