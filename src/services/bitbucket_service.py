import requests
from atlassian.bitbucket import Cloud
from typing import Optional
from .base_repo_service import BaseRepoService
from src.models.pr_data import PRData
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BitbucketService(BaseRepoService):
    def __init__(self):
        if not settings.BITBUCKET_USERNAME or not settings.BITBUCKET_APP_PASSWORD:
            raise ValueError(
                "Bitbucket credentials are required. Set BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD environment variables.")

        self.username = settings.BITBUCKET_USERNAME
        self.app_password = settings.BITBUCKET_APP_PASSWORD
        self.bitbucket = Cloud(
            username=self.username,
            password=self.app_password,
            cloud=True
        )

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> PRData:
        """Get PR data including diff from Bitbucket"""
        try:
            # Get PR details
            pr_data = self.bitbucket.repositories.get_pullrequest(
                owner, repo, pr_number
            )

            # Get PR diff
            diff_response = self.bitbucket.repositories.get_pullrequest_diff(
                owner, repo, pr_number
            )

            # Get PR commits to calculate stats
            commits = self.bitbucket.repositories.get_pullrequest_commits(
                owner, repo, pr_number
            )

            # Calculate additions and deletions from diff
            additions, deletions = self._calculate_diff_stats(diff_response)

            # Count changed files
            files_changed = self._count_changed_files(diff_response)

            return PRData(
                title=pr_data.get('title', ''),
                description=pr_data.get('description', ''),
                diff=diff_response,
                files_changed=files_changed,
                additions=additions,
                deletions=deletions,
                number=pr_number,
                owner=owner,
                repo=repo,
                provider="bitbucket"
            )

        except Exception as e:
            logger.error(f"Error fetching Bitbucket PR data: {str(e)}")
            raise

    def _calculate_diff_stats(self, diff_content: str) -> tuple:
        """Calculate additions and deletions from diff content"""
        additions = 0
        deletions = 0

        for line in diff_content.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                additions += 1
            elif line.startswith('-') and not line.startswith('---'):
                deletions += 1

        return additions, deletions

    def _count_changed_files(self, diff_content: str) -> int:
        """Count number of changed files from diff"""
        files = set()

        for line in diff_content.split('\n'):
            if line.startswith('diff --git'):
                # Extract filename from diff header
                parts = line.split()
                if len(parts) >= 4:
                    files.add(parts[3])  # b/filename

        return len(files)

    async def validate_credentials(self) -> bool:
        """Validate Bitbucket credentials"""
        try:
            # Try to get user info to validate credentials
            user_info = self.bitbucket.user.get()
            return user_info is not None
        except Exception:
            return False

    def get_pr_url(self, owner: str, repo: str, pr_number: int) -> str:
        """Generate Bitbucket PR URL"""
        return f"https://bitbucket.org/{owner}/{repo}/pull-requests/{pr_number}"
