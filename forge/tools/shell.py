import subprocess

from forge.paths import ProjectPaths
from forge.security import SecurityPolicy
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

    def __init__(
        self,
        project_root=None,
        security_policy: SecurityPolicy | None = None,
    ):
        super().__init__(project_root)
        self.security = security_policy or SecurityPolicy(
            project_root=self.project_root
        )

    def execute(self, **kwargs):
        command = kwargs.get("command")

        if not command:
            return {
                "success": False,
                "error": "Missing command"
            }

        allowed, reason = self.security.command_risk(command)

        if not allowed:
            return {
                "success": False,
                "error": f"Command blocked by execution sandbox: {reason}"
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
                "stdout": self.security.redact_text(result.stdout),
                "stderr": self.security.redact_text(result.stderr)
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
