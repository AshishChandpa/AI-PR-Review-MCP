import json
import sys
import os
from pathlib import Path

# Add project root to Python path FIRST
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Dict, Optional
import asyncio
from src.providers.base_provider import BaseProvider
from src.providers.openai_provider import OpenAIProvider
from src.models.review_result import ReviewResult
from src.models.pr_data import PRData
from config.settings import settings
from src.utils.logger import get_logger

# Import other providers after path setup
try:
    from src.providers.claude_provider import ClaudeProvider
except ImportError:
    ClaudeProvider = None

try:
    from src.providers.gemini_provider import GeminiProvider
except ImportError:
    GeminiProvider = None

try:
    from src.providers.groq_provider import GroqProvider
except ImportError:
    GroqProvider = None

try:
    from src.providers.perplexity_provider import PerplexityProvider
except ImportError:
    PerplexityProvider = None

logger = get_logger(__name__)


class LLMService:
    def __init__(self):
        self.providers = self._initialize_providers()

    def _initialize_providers(self) -> Dict[str, BaseProvider]:
        """Initialize available LLM providers"""
        providers = {}

        # Try to initialize each provider if API key is available
        provider_configs = {
            "openai": {
                "class": OpenAIProvider,
                "key": settings.API_KEYS.get("openai"),
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
                "default": "gpt-4o"
            },
            "claude": {
                "class": ClaudeProvider,
                "key": settings.API_KEYS.get("claude"),
                "models": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                "default": "claude-3-sonnet-20240229"
            },
            "gemini": {
                "class": GeminiProvider,
                "key": settings.API_KEYS.get("gemini"),
                "models": ["gemini-pro", "gemini-pro-vision", "gemini-1.5-flash"],
                "default": "gemini-1.5-flash"
            },
            "groq": {
                "class": GroqProvider,
                "key": settings.API_KEYS.get("groq"),
                "models": ["llama3-70b-8192", "llama3-8b-8192"],
                "default": "llama3-70b-8192"
            },
            "perplexity": {
                "class": PerplexityProvider,
                "key": settings.API_KEYS.get("perplexity"),
                "models": ["sonar-small-chat", "sonar-medium-chat"],
                "default": "sonar-small-chat"
            }
        }

        for provider_name, config in provider_configs.items():
            # Check if provider class exists and API key is available
            if config["class"] is not None and config["key"]:
                try:
                    providers[provider_name] = config["class"](config["key"])
                    logger.info(f"Initialized {provider_name} provider")
                except Exception as e:
                    logger.error(f"Failed to initialize {provider_name}: {e}")
            elif config["class"] is None:
                logger.warning(f"Provider class for {provider_name} not implemented")
            else:
                logger.warning(f"No API key for {provider_name}")

        return providers

    async def review_pr(self, pr_data: PRData, provider_name: str, model: str = None,
                        review_type: str = "comprehensive") -> ReviewResult:
        """Review a PR using the specified provider"""

        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not available or not configured")

        provider = self.providers[provider_name]

        # Generate review prompt based on type
        prompt = self._generate_review_prompt(pr_data, review_type)

        # Get review from provider
        review_content = await provider.analyze_pr(prompt, model)

        return ReviewResult(
            content=review_content,
            provider=provider_name,
            model_used=model or provider.get_default_model(),
            review_type=review_type
        )

    def _generate_review_prompt(self, pr_data: PRData, review_type: str) -> str:
        """Generate review prompt based on PR data and review type"""

        base_prompt = f"""
Please review the following Pull Request:

Title: {pr_data.title}
Description: {pr_data.description or "No description provided"}

Files changed: {pr_data.files_changed}
Additions: {pr_data.additions}
Deletions: {pr_data.deletions}

Diff:
{pr_data.diff}
"""

        review_prompts = {
            "comprehensive": "Provide a comprehensive code review covering all aspects including functionality, style, performance, and potential issues.",
            "security": "Focus specifically on security vulnerabilities, potential exploits, and security best practices.",
            "performance": "Analyze performance implications, optimization opportunities, and resource usage.",
            "style": "Review code style, consistency, formatting, and adherence to best practices."
        }

        return base_prompt + "\n\n" + review_prompts.get(review_type, review_prompts["comprehensive"])

    def get_available_providers(self) -> Dict[str, Dict]:
        """Get list of available providers with their models"""
        provider_info = {}

        # Define all possible providers with their configurations
        all_providers = {
            "openai": {
                "name": "OpenAI",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
                "default_model": "gpt-4o",
                "description": "OpenAI GPT models with excellent code analysis capabilities"
            },
            "claude": {
                "name": "Anthropic Claude",
                "models": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                "default_model": "claude-3-sonnet-20240229",
                "description": "Anthropic's Claude with strong reasoning and code review skills"
            },
            "gemini": {
                "name": "Google Gemini",
                "models": ["gemini-pro", "gemini-pro-vision", "gemini-1.5-flash"],
                "default_model": "gemini-1.5-flash",
                "description": "Google's Gemini with multimodal capabilities"
            },
            "groq": {
                "name": "Groq",
                "models": ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"],
                "default_model": "llama3-70b-8192",
                "description": "Fast inference with Llama and Mixtral models"
            },
            "perplexity": {
                "name": "Perplexity",
                "models": ["sonar-small-chat", "sonar-medium-chat", "sonar-large-chat"],
                "default_model": "sonar-small-chat",
                "description": "Perplexity's research-focused models"
            }
        }

        # Check which providers are actually available
        for provider_id, provider_config in all_providers.items():
            enabled = provider_id in self.providers
            api_key_available = bool(settings.API_KEYS.get(provider_id))

            # Check if provider class exists
            provider_configs = {
                "openai": OpenAIProvider,
                "claude": ClaudeProvider,
                "gemini": GeminiProvider,
                "groq": GroqProvider,
                "perplexity": PerplexityProvider
            }

            class_available = provider_configs.get(provider_id) is not None

            provider_info[provider_id] = {
                **provider_config,
                "enabled": enabled,
                "api_key_available": api_key_available,
                "class_available": class_available,
                "status": "Available" if enabled else (
                    "API key required" if class_available and not api_key_available else
                    "Implementation required" if not class_available else
                    "Configuration error"
                )
            }

        return provider_info

    def _generate_inline_review_prompt(self, pr_data: PRData, review_type: str) -> str:
        """
        Prompt for both general and inline feedback.
        """
        return f"""
You are an expert software engineer and code reviewer.

--- OBJECTIVE ---
Given a pull request, provide:
1. A high-level review comment as `"general_comment"`.
2. Inline comments for specific lines of code that require attention, as a list under `"inline_comments"`.

Each inline comment must be a JSON object with:
- "file": filename (string),
- "line": line number (int),
- "comment": review message (string)

--- OUTPUT FORMAT ---
Respond with **only a valid JSON object**, using the following structure:

{{
  "general_comment": "High-level review here.",
  "inline_comments": [
    {{
      "file": "example.py",
      "line": 12,
      "comment": "This could be refactored for clarity."
    }},
    ...
  ]
}}

--- PULL REQUEST DATA ---

Title: {pr_data.title}
Description: {pr_data.description or "No description provided"}
Files Changed: {pr_data.files_changed}
Additions: {pr_data.additions}
Deletions: {pr_data.deletions}

--- DIFF START ---
{pr_data.diff}
--- DIFF END ---

--- REVIEW TYPE ---
Focus on: {review_type}

Be precise, helpful, and return only the JSON object as your entire response.
"""


    async def review_inline_pr(self, pr_data: PRData, provider_name: str, model: str = None,
                        review_type: str = "comprehensive") -> dict:
        """
        Returns {
            "general_comment": "...",
            "inline_comments": [
                {"file": "...", "line": 99, "comment": "..."},
                ...
            ]
        }
        """
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not available or not configured")
        provider = self.providers[provider_name]

        prompt = self._generate_inline_review_prompt(pr_data, review_type)
        review_content = await provider.analyze_pr(prompt, model)

        try:
            feedback = provider.extract_json_from_block(review_content)
            # Defensive: enforce required structure
            general_comment = feedback.get("general_comment", "")
            inline_comments = feedback.get("inline_comments", [])
            if not isinstance(inline_comments, list):
                inline_comments = []
        except Exception as e:
            # Invalid JSON or not in spec. Fallback to general comment only.
            general_comment = review_content
            inline_comments = []

        # Return both sections, ready for posting as Bitbucket comments
        return {
            "general_comment": general_comment,
            "inline_comments": inline_comments,
            "provider": provider_name,
            "model": model or provider.get_default_model(),
            "review_type": review_type
        }

    async def get_suggestions(self, pr_data, prompt: str):
        """Generate code suggestions"""
        full_prompt = f"{prompt}\n\nPR Diff:\n{pr_data.diff_text} \n\n Provide code suggestions based on the changes made in this PR."
        provider = self.providers[settings.DEFAULT_LLM_PROVIDER]
        # Use your existing LLM call logic
        response = await provider.analyze_pr(full_prompt)
        return response

    async def explain_changes(self, pr_data, prompt: str):
        """Explain PR changes"""
        full_prompt = f"{prompt}\n\nPR Diff:\n{pr_data.diff}\n\n Provide a detailed explanation of the changes made in this PR."
        provider = self.providers[settings.DEFAULT_LLM_PROVIDER]
        response = await provider.analyze_pr(full_prompt)
        return response

    async def security_analysis(self, pr_data):
        """Perform security analysis"""
        full_prompt = f"Analyze this code diff for security vulnerabilities, potential security issues, and provide recommendations:\n\n{pr_data.diff_text}"
        provider = self.providers[settings.DEFAULT_LLM_PROVIDER]
        response = await provider.analyze_pr(full_prompt)
        return response


