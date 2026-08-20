import subprocess

from forge.paths import ProjectPaths
from forge.tools.base import Tool


class VerifyProjectTool(ProjectPaths, Tool):
    name = "verify_project"
    description = "Run the project test suite with uv and return the result."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def execute(self, **kwargs):
        try:
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "python",
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                ],
                cwd=self.project_root,
                env={
                    **__import__("os").environ,
                    "UV_CACHE_DIR": ".uv-cache",
                },
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Verification timed out after 60 seconds"
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc)
            }

        return {
            "success": result.returncode == 0,
            "command": "uv run python -m unittest discover -s tests",
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
