from abc import ABC, abstractmethod
from typing import Optional
from src.models.pr_data import PRData


class BaseRepoService(ABC):
    """Abstract base class for repository services"""

    @abstractmethod
    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> PRData:
        """Get PR data including diff"""
        pass

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate repository service credentials"""
        pass

    @abstractmethod
    def get_pr_url(self, owner: str, repo: str, pr_number: int) -> str:
        """Generate PR URL"""
        pass
