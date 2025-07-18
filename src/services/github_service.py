import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from github import Github
from src.services.base_repo_service import BaseRepoService
from src.models.pr_data import PRData
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GitHubService(BaseRepoService):
    def __init__(self):
        if not settings.GITHUB_TOKEN:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")

        self.github = Github(settings.GITHUB_TOKEN)

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> PRData:
        """Get PR data including diff"""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)

            # Get PR files and generate diff
            files = pr.get_files()
            diff_content = ""

            for file in files:
                diff_content += f"\n--- {file.filename} ---\n"
                if file.patch:
                    diff_content += file.patch
                else:
                    diff_content += "Binary file or no changes to show"

            return PRData(
                title=pr.title,
                description=pr.body,
                diff=diff_content,
                files_changed=pr.changed_files,
                additions=pr.additions,
                deletions=pr.deletions,
                number=pr_number,
                owner=owner,
                repo=repo,
                provider="github"
            )

        except Exception as e:
            logger.error(f"Error fetching GitHub PR data: {str(e)}")
            raise

    async def validate_credentials(self) -> bool:
        """Validate GitHub credentials"""
        try:
            user = self.github.get_user()
            return user is not None
        except Exception:
            return False

    def get_pr_url(self, owner: str, repo: str, pr_number: int) -> str:
        """Generate GitHub PR URL"""
        return f"https://github.com/{owner}/{repo}/pull/{pr_number}"
