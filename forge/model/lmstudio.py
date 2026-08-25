import os

from openai import OpenAI


class OpenAICompatibleProvider:
    def __init__(
        self,
        model: str,
        *,
        provider: str,
        base_url: str | None = None,
        api_key: str | None = None,
        api_key_env: str | None = None,
    ):
        resolved_api_key = api_key
        if api_key_env:
            resolved_api_key = os.environ.get(api_key_env)

        if not resolved_api_key:
            raise ValueError(
                f"{provider} requires credentials. "
                f"Set {api_key_env or 'the provider API key environment variable'}."
            )

        client_kwargs = {
            "api_key": resolved_api_key,
        }
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = OpenAI(**client_kwargs)
        self.model = model
        self.provider = provider
        self.base_url = base_url
        self.last_usage = None

    def generate(self, messages, tools=None):
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(
            **kwargs
        )
        usage = getattr(response, "usage", None)
        if usage is not None:
            if hasattr(usage, "model_dump"):
                self.last_usage = usage.model_dump()
            elif isinstance(usage, dict):
                self.last_usage = usage
            else:
                self.last_usage = {
                    key: getattr(usage, key)
                    for key in (
                        "prompt_tokens",
                        "completion_tokens",
                        "total_tokens",
                    )
                    if hasattr(usage, key)
                }
        else:
            self.last_usage = None

        return response.choices[0].message


class LMStudioProvider(OpenAICompatibleProvider):
    def __init__(self, model: str):
        super().__init__(
            model,
            provider="lmstudio",
            base_url="http://localhost:1234/v1",
            api_key="lm-studio",
        )
