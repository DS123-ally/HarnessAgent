from openai import OpenAI


class LMStudioProvider:
    def __init__(self, model: str):
        self.client = OpenAI(
            base_url="http://localhost:1234/v1",
            api_key="lm-studio"
        )

        self.model = model

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

        return response.choices[0].message