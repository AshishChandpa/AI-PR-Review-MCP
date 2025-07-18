import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from typing import Dict, Type
from src.services.base_repo_service import BaseRepoService
from src.services.github_service import GitHubService
from src.services.bitbucket_service import BitbucketService
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RepoServiceFactory:
    """Factory for creating repository service instances"""

    _services: Dict[str, Type[BaseRepoService]] = {
        "github": GitHubService,
        "bitbucket": BitbucketService,  # Re-enable Bitbucket
    }

    @classmethod
    def create_service(cls, provider: str) -> BaseRepoService:
        """Create a repository service instance"""
        if provider not in cls._services:
            raise ValueError(f"Unsupported repository provider: {provider}")

        service_class = cls._services[provider]
        try:
            return service_class()
        except Exception as e:
            logger.error(f"Failed to create {provider} service: {e}")
            raise

    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available repository providers"""
        available = []
        for provider_name in cls._services.keys():
            try:
                # Test if the service can be created (has required credentials)
                cls.create_service(provider_name)
                available.append(provider_name)
            except Exception as e:
                logger.warning(f"Provider {provider_name} not available: {e}")
                # Still add it to the list but it will show as disabled
                available.append(provider_name)

        return available

    @classmethod
    def get_provider_status(cls) -> Dict[str, Dict]:
        """Get detailed status of all providers"""
        status = {}
        for provider_name in cls._services.keys():
            try:
                service = cls.create_service(provider_name)
                status[provider_name] = {
                    "available": True,
                    "name": provider_name.title(),
                    "description": f"{provider_name.title()} repository service"
                }
            except Exception as e:
                status[provider_name] = {
                    "available": False,
                    "name": provider_name.title(),
                    "description": f"{provider_name.title()} repository service",
                    "error": str(e)
                }

        return status
