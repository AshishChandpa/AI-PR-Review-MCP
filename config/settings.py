import os
from dotenv import load_dotenv
from typing import Dict, Optional

load_dotenv()


class Settings:
    # Server Configuration
    MCP_SERVER_NAME = "pr-review-server"
    UI_HOST = "localhost"
    UI_PORT = 8080
    MCP_PORT = 8000

    # Repository Provider Configuration
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    BITBUCKET_USERNAME = os.getenv("BITBUCKET_USERNAME")
    BITBUCKET_APP_PASSWORD = os.getenv("BITBUCKET_APP_PASSWORD")

    # Default Repository Provider
    DEFAULT_REPO_PROVIDER = "github"

    # Supported Repository Providers
    SUPPORTED_REPO_PROVIDERS = ["github", "bitbucket"]

    # Default LLM Provider
    DEFAULT_LLM_PROVIDER = "gemini"

    # API Keys
    API_KEYS = {
        "openai": os.getenv("OPENAI_API_KEY"),
        "claude": os.getenv("ANTHROPIC_API_KEY"),
        "gemini": os.getenv("GOOGLE_API_KEY"),
        "groq": os.getenv("GROQ_API_KEY"),
        "perplexity": os.getenv("PERPLEXITY_API_KEY")
    }

    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "pr_review.log"


settings = Settings()
