import openai
from .base_provider import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = openai.OpenAI(api_key=api_key)

    async def analyze_pr(self, prompt: str, model: str = None) -> str:
        model = model or self.get_default_model()

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system",
                 "content": "You are a senior software engineer conducting a code review. Provide detailed, constructive feedback."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.1
        )

        return response.choices[0].message.content

    def get_default_model(self) -> str:
        return "gpt-4o"
