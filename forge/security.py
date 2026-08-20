import fnmatch
import json
import re
from pathlib import Path
from typing import Any

from forge.paths import ProjectPaths


DEFAULT_SECURITY_POLICY = {
    "network": "deny",
    "allowed_commands": [
        "python",
        "uv",
        "git status",
        "git diff",
        "git log",
    ],
    "blocked_command_parts": [
        "git reset --hard",
        "git clean",
        "rm ",
        "rmdir",
        "del ",
        "format ",
        "shutdown",
        "curl",
        "wget",
        "ssh",
        "scp",
        "pip install",
    ],
    "blocked_shell_operators": [
        "&&",
        "||",
        ";",
        "|",
        ">",
        ">>",
    ],
    "deny_paths": [
        ".git/**",
        ".venv/**",
        ".uv-cache/**",
        "__pycache__/**",
        ".env",
        "*.pem",
        "*.key",
        "*.p12",
        "*.pfx",
    ],
    "secret_patterns": [
        "api[_-]?key\\s*[:=]\\s*['\\\"]?[^'\\\"\\s]+",
        "token\\s*[:=]\\s*['\\\"]?[^'\\\"\\s]+",
        "secret\\s*[:=]\\s*['\\\"]?[^'\\\"\\s]+",
        "-----BEGIN [A-Z ]*PRIVATE KEY-----",
    ],
}


class SecurityPolicy(ProjectPaths):
    def __init__(
        self,
        project_root: str | Path | None = None,
        policy_path: str = ".harness/security.json",
    ):
        super().__init__(project_root)
        self.policy_path = self.resolve_project_path(policy_path)
        self.policy_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.policy = self.load()

    def load(self) -> dict[str, Any]:
        if not self.policy_path.exists():
            self.policy_path.write_text(
                json.dumps(
                    DEFAULT_SECURITY_POLICY,
                    indent=2,
                ),
                encoding="utf-8",
            )
            return DEFAULT_SECURITY_POLICY.copy()

        user_policy = json.loads(
            self.policy_path.read_text(
                encoding="utf-8",
            )
        )

        policy = DEFAULT_SECURITY_POLICY.copy()
        policy.update(user_policy)

        return policy

    def is_path_denied(self, path: Path) -> bool:
        relative_path = self.display_path(path).replace("\\", "/")

        return any(
            fnmatch.fnmatch(relative_path, pattern)
            for pattern in self.policy["deny_paths"]
        )

    def check_path_allowed(self, path: Path) -> None:
        if self.is_path_denied(path):
            raise PermissionError(
                f"Path blocked by security policy: {self.display_path(path)}"
            )

    def command_risk(self, command: str) -> tuple[bool, str]:
        normalized = command.lower().strip()

        for blocked in self.policy["blocked_command_parts"]:
            if blocked in normalized:
                return False, f"Command contains blocked part: {blocked}"

        for operator in self.policy["blocked_shell_operators"]:
            if operator in command:
                return False, f"Command contains blocked shell operator: {operator}"

        if self.policy.get("network") == "deny":
            network_commands = {
                "curl",
                "wget",
                "ssh",
                "scp",
                "ftp",
            }

            if normalized.split(" ", 1)[0] in network_commands:
                return False, "Network command blocked by security policy"

        if not any(
            normalized == allowed
            or normalized.startswith(allowed + " ")
            for allowed in self.policy["allowed_commands"]
        ):
            return False, "Command is not in the security allowlist"

        return True, "Command allowed"

    def redact_text(self, text: str) -> str:
        redacted = text

        for pattern in self.policy["secret_patterns"]:
            redacted = re.sub(
                pattern,
                "[REDACTED]",
                redacted,
                flags=re.IGNORECASE,
            )

        return redacted

    def redact_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.redact_text(value)

        if isinstance(value, list):
            return [
                self.redact_value(item)
                for item in value
            ]

        if isinstance(value, dict):
            redacted = {}

            for key, item in value.items():
                if any(
                    sensitive in key.lower()
                    for sensitive in ("key", "token", "secret", "password")
                ):
                    redacted[key] = "[REDACTED]"
                else:
                    redacted[key] = self.redact_value(item)

            return redacted

        return value
