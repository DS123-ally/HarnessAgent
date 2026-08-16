from openai import OpenAI


class LMStudioProvider:
    def __init__(self, model: str):
        self.client = OpenAI(
            base_url="http://localhost:1234/v1",
            api_key="lm-studio",
        )
        self.model = model

    def generate(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )

        return response.choices[0].message.content