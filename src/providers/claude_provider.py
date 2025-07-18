import anthropic
from .base_provider import BaseProvider


class ClaudeProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = anthropic.Anthropic(api_key=api_key)

    async def analyze_pr(self, prompt: str, model: str = None) -> str:
        model = model or self.get_default_model()

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")

    def get_default_model(self) -> str:
        return "claude-3-sonnet-20240229"
