import subprocess

from forge.paths import ProjectPaths
from forge.tools.base import Tool


class RunCommandTool(ProjectPaths, Tool):
    name = "run_command"

    description = "Run a shell command inside the current project directory."

    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute"
            }
        },
        "required": ["command"]
    }

    BLOCKED_COMMAND_PARTS = {
        "git reset --hard",
        "git clean",
        "rm ",
        "rmdir",
        "del ",
        "format ",
        "shutdown",
    }

    def is_blocked(self, command: str) -> bool:
        normalized = command.lower().strip()

        return any(
            blocked in normalized
            for blocked in self.BLOCKED_COMMAND_PARTS
        )

    def execute(self, **kwargs):
        command = kwargs.get("command")

        if not command:
            return {
                "success": False,
                "error": "Missing command"
            }

        if self.is_blocked(command):
            return {
                "success": False,
                "error": "Command blocked by execution sandbox"
            }

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                "success": result.returncode == 0,
                "command": command,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out after 30 seconds"
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }
