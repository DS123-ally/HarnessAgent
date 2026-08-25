from forge.paths import ProjectPaths
from forge.security import SecurityPolicy
from forge.tools.base import Tool


class ProjectPathMixin(ProjectPaths):
    def __init__(
        self,
        project_root=None,
        security_policy: SecurityPolicy | None = None,
    ):
        super().__init__(project_root)
        self.security = security_policy or SecurityPolicy(
            project_root=self.project_root
        )

    def resolve_allowed_path(self, path_str: str):
        path = self.resolve_project_path(path_str)
        self.security.check_path_allowed(path)
        return path


## Read File Tool

class ReadFileTool(ProjectPathMixin, Tool):
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

        try:
            path = self.resolve_allowed_path(file_path)
        except (PermissionError, ValueError) as exc:
            return {
                "success": False,
                "error": str(exc)
            }

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
                "path": self.display_path(path),
                "content": self.security.redact_text(content)
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }

## List File Tool

class ListFilesTool(ProjectPathMixin, Tool):
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

        try:
            path = self.resolve_allowed_path(path_str)
        except (PermissionError, ValueError) as exc:
            return {
                "success": False,
                "error": str(exc)
            }

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
                "path": self.display_path(path),
                "items": items
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }


## Search File Tool


class SearchFilesTool(ProjectPathMixin, Tool):
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

        try:
            root = self.resolve_allowed_path(path_str)
        except (PermissionError, ValueError) as exc:
            return {
                "success": False,
                "error": str(exc)
            }

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

                if any(
                    part in {".git", ".venv", ".uv-cache", "__pycache__"}
                    for part in file_path.parts
                ):
                    continue

                if self.security.is_path_denied(file_path):
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
                            "file": self.display_path(file_path),
                            "line": line_number,
                            "text": self.security.redact_text(line.strip())
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


## Wrte Tool File


class CreateDirectoryTool(ProjectPathMixin, Tool):
    name = "create_directory"

    description = "Create a directory inside the current project."

    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path of the directory to create"
            }
        },
        "required": ["path"]
    }

    def execute(self, **kwargs):
        path_str = kwargs.get("path")

        if not path_str:
            return {
                "success": False,
                "error": "Missing path"
            }

        try:
            path = self.resolve_allowed_path(path_str)
        except (PermissionError, ValueError) as exc:
            return {
                "success": False,
                "error": str(exc)
            }

        if path.exists() and not path.is_dir():
            return {
                "success": False,
                "error": f"Path exists and is not a directory: {path_str}"
            }

        try:
            path.mkdir(
                parents=True,
                exist_ok=True
            )

            return {
                "success": True,
                "path": self.display_path(path),
                "message": f"Created directory: {self.display_path(path)}"
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }


class DeleteDirectoryTool(ProjectPathMixin, Tool):
    name = "delete_directory"

    description = (
        "Delete a directory inside the current project. Empty directories "
        "can be deleted directly; non-empty directories require recursive=true."
    )

    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path of the directory to delete"
            },
            "recursive": {
                "type": "boolean",
                "description": "Delete the directory and all of its contents"
            }
        },
        "required": ["path"]
    }

    def execute(self, **kwargs):
        path_str = kwargs.get("path")
        recursive = bool(kwargs.get("recursive", False))

        if not path_str:
            return {
                "success": False,
                "error": "Missing path"
            }

        try:
            path = self.resolve_allowed_path(path_str)
        except (PermissionError, ValueError) as exc:
            return {
                "success": False,
                "error": str(exc)
            }

        if not path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {path_str}"
            }

        if not path.is_dir():
            return {
                "success": False,
                "error": f"Not a directory: {path_str}"
            }

        try:
            if recursive:
                self._delete_tree(path)
            else:
                path.rmdir()

            return {
                "success": True,
                "path": self.display_path(path),
                "message": f"Deleted directory: {self.display_path(path)}"
            }

        except OSError:
            return {
                "success": False,
                "error": (
                    "Directory is not empty. Use recursive=true to delete "
                    "the directory and its contents."
                )
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }

    def _delete_tree(self, path):
        for child in path.iterdir():
            self.security.check_path_allowed(child)
            if child.is_dir():
                self._delete_tree(child)
            else:
                child.unlink()
        path.rmdir()


class WriteFileTool(ProjectPathMixin, Tool):
    name = "write_file"

    description = "Create a new file or overwrite an existing text file."

    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path of the file to write"
            },
            "content": {
                "type": "string",
                "description": "Full content to write into the file"
            }
        },
        "required": ["path", "content"]
    }

    def execute(self, **kwargs):
        path_str = kwargs.get("path")
        content = kwargs.get("content")

        if not path_str:
            return {
                "success": False,
                "error": "Missing path"
            }

        if content is None:
            return {
                "success": False,
                "error": "Missing content"
            }

        try:
            path = self.resolve_allowed_path(path_str)
        except (PermissionError, ValueError) as exc:
            return {
                "success": False,
                "error": str(exc)
            }

        try:
            path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            path.write_text(
                content,
                encoding="utf-8"
            )

            return {
                "success": True,
                "path": self.display_path(path),
                "message": f"Wrote file: {self.display_path(path)}"
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }


## Delete File Tool 

class DeleteFileTool(ProjectPathMixin, Tool):
    name = "delete_file"

    description = "Delete a file from the current project."

    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path of the file to delete"
            }
        },
        "required": ["path"]
    }

    def execute(self, **kwargs):
        path_str = kwargs.get("path")

        if not path_str:
            return {
                "success": False,
                "error": "Missing path"
            }

        try:
            path = self.resolve_allowed_path(path_str)
        except (PermissionError, ValueError) as exc:
            return {
                "success": False,
                "error": str(exc)
            }

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {path_str}"
            }

        if not path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {path_str}"
            }

        try:
            path.unlink()

            return {
                "success": True,
                "path": self.display_path(path),
                "message": f"Deleted file: {self.display_path(path)}"
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }



## Edit File Tool 
class EditFileTool(ProjectPathMixin, Tool):
    name = "edit_file"

    description = (
        "Edit an existing text file by replacing exact text "
        "with new text."
    )

    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path of the file to edit"
            },
            "old_text": {
                "type": "string",
                "description": "Exact existing text to replace"
            },
            "new_text": {
                "type": "string",
                "description": "Replacement text"
            }
        },
        "required": [
            "path",
            "old_text",
            "new_text"
        ]
    }

    def execute(self, **kwargs):
        path_str = kwargs.get("path")
        old_text = kwargs.get("old_text")
        new_text = kwargs.get("new_text")

        if not path_str:
            return {
                "success": False,
                "error": "Missing path"
            }

        if old_text is None:
            return {
                "success": False,
                "error": "Missing old_text"
            }

        if new_text is None:
            return {
                "success": False,
                "error": "Missing new_text"
            }

        try:
            path = self.resolve_allowed_path(path_str)
        except (PermissionError, ValueError) as exc:
            return {
                "success": False,
                "error": str(exc)
            }

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {path_str}"
            }

        if not path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {path_str}"
            }

        try:
            content = path.read_text(
                encoding="utf-8",
                errors="replace"
            )

            if old_text not in content:
                return {
                    "success": False,
                    "error": "old_text was not found in the file"
                }

            # Important:
            # only replace the first matching occurrence
            updated_content = content.replace(
                old_text,
                new_text,
                1
            )

            path.write_text(
                updated_content,
                encoding="utf-8"
            )

            return {
                "success": True,
                "path": self.display_path(path),
                "message": f"Edited file: {self.display_path(path)}"
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }
