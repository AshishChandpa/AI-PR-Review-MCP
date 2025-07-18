import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import json
from typing import Dict, Optional
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigService:
    def __init__(self):
        self.config_path = Path("config/llm_providers.json")
        self.providers_config = self._load_providers_config()

    def _load_providers_config(self) -> Dict:
        """Load providers configuration from JSON file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading providers config: {str(e)}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Get default providers configuration"""
        return {
            "providers": {
                "openai": {
                    "name": "OpenAI",
                    "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
                    "default_model": "gpt-4o",
                    "enabled": bool(settings.API_KEYS.get("openai")),
                    "description": "OpenAI GPT models"
                },
                "claude": {
                    "name": "Anthropic Claude",
                    "models": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                    "default_model": "claude-3-sonnet-20240229",
                    "enabled": bool(settings.API_KEYS.get("claude")),
                    "description": "Anthropic Claude models"
                },
                "gemini": {
                    "name": "Google Gemini",
                    "models": ["gemini-pro", "gemini-pro-vision"],
                    "default_model": "gemini-pro",
                    "enabled": bool(settings.API_KEYS.get("gemini")),
                    "description": "Google Gemini models"
                },
                "groq": {
                    "name": "Groq",
                    "models": ["llama3-70b-8192", "llama3-8b-8192"],
                    "default_model": "llama3-70b-8192",
                    "enabled": bool(settings.API_KEYS.get("groq")),
                    "description": "Groq models"
                },
                "perplexity": {
                    "name": "Perplexity",
                    "models": ["sonar-small-chat", "sonar-medium-chat"],
                    "default_model": "sonar-small-chat",
                    "enabled": bool(settings.API_KEYS.get("perplexity")),
                    "description": "Perplexity models"
                }
            }
        }

    def get_available_providers(self) -> Dict:
        """Get available providers with their configuration"""
        return self.providers_config.get("providers", {})

    def get_default_provider(self) -> str:
        """Get the default provider name"""
        # Return first enabled provider
        for provider_id, provider_info in self.providers_config.get("providers", {}).items():
            if provider_info.get("enabled", False):
                return provider_id

        return settings.DEFAULT_LLM_PROVIDER

    async def configure_provider(self, provider: str, api_key: str = None,
                                 model: str = None, enabled: bool = None) -> Dict:
        """Configure a provider"""
        if provider not in self.providers_config.get("providers", {}):
            raise ValueError(f"Unknown provider: {provider}")

        # Update configuration
        config = self.providers_config["providers"][provider]

        if enabled is not None:
            config["enabled"] = enabled

        if model and model in config.get("models", []):
            config["default_model"] = model

        # Save configuration
        self._save_config()

        return {"status": "success", "provider": provider, "config": config}

    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.providers_config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
