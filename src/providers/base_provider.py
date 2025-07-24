from abc import ABC, abstractmethod

import json
import re
import logging


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

    @staticmethod
    def extract_json_from_block(raw_string: str) -> dict:
        """
        Extracts and parses JSON content from a string wrapped in triple backticks (```json ... ```)

        Args:
            raw_string (str): The raw string containing a JSON block inside markdown-style backticks.

        Returns:
            dict: Parsed JSON data as a Python dictionary.

        Raises:
            ValueError: If JSON cannot be extracted or parsed.
        """
        try:
            # Strip leading/trailing whitespace and extract the JSON block
            cleaned = re.sub(r"^```json|^```|```$", "", raw_string.strip(), flags=re.MULTILINE).strip("` \n")

            # Parse to dict
            return json.loads(cleaned)

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON: {e}")
            raise ValueError("Invalid JSON format in input string.")
