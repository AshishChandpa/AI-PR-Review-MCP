import google.generativeai as genai
from .base_provider import BaseProvider


class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel('gemini-pro')

    async def analyze_pr(self, prompt: str, model: str = None) -> str:
        model = model or self.get_default_model()

        try:
            # Update model if different from default
            if model != 'gemini-pro':
                self.client = genai.GenerativeModel(model)

            response = self.client.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4000
                )
            )
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

    def get_default_model(self) -> str:
        return "gemini-pro"
