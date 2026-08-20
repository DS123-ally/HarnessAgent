from forge.security import SecurityPolicy
from forge.tools.base import Tool


class ShowSecurityPolicyTool(Tool):
    name = "show_security_policy"
    description = "Show the active HarnessAgent security policy."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def __init__(self, security_policy: SecurityPolicy | None = None):
        self.security = security_policy or SecurityPolicy()

    def execute(self, **kwargs):
        return {
            "success": True,
            "policy": self.security.redact_value(
                self.security.policy
            )
        }
