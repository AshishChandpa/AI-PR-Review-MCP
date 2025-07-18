from abc import ABC, abstractmethod
from typing import Optional


class BaseProvider(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def analyze_pr(self, prompt: str, model: str = None) -> str:
        """Analyze PR and return review"""
        pass

    @abstractmethod
    def get_default_model(self) -> str:
        """Get default model for this provider"""
        pass
