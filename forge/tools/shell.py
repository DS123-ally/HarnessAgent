import subprocess

from forge.tools.base import Tool


class RunCommandTool(Tool):
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

    def execute(self, **kwargs):
        command = kwargs.get("command")

        if not command:
            return {
                "success": False,
                "error": "Missing command"
            }

        try:
            result = subprocess.run(
                command,
                shell=True,
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