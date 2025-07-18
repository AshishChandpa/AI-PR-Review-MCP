import requests

from config.settings import settings
from src.models.pr_data import PRData
from src.utils.logger import get_logger
from .base_repo_service import BaseRepoService

logger = get_logger(__name__)


class BitbucketService(BaseRepoService):
    API_BASE = "https://api.bitbucket.org/2.0/repositories"

    def __init__(self):
        if not settings.BITBUCKET_USERNAME or not settings.BITBUCKET_APP_PASSWORD:
            raise ValueError(
                "Bitbucket credentials are required. Set BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD environment variables."
            )
        self.username = settings.BITBUCKET_USERNAME
        self.app_password = settings.BITBUCKET_APP_PASSWORD

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> PRData:
        # Auth tuple for requests
        auth = (self.username, self.app_password)
        repo_slug = repo  # Bitbucket calls this repo_slug

        # Get PR data
        pr_url = f"{self.API_BASE}/{owner}/{repo_slug}/pullrequests/{pr_number}"
        diff_url = f"{pr_url}/diff"
        try:
            pr_resp = requests.get(pr_url, auth=auth)
            pr_resp.raise_for_status()
            pr_data = pr_resp.json()

            diff_resp = requests.get(diff_url, auth=auth)
            diff_resp.raise_for_status()
            diff_content = diff_resp.text

            # Stats extraction
            files_changed, additions, deletions = self._parse_diff_stats(diff_content)

            return PRData(
                title=pr_data.get("title", ""),
                description=pr_data.get("description", ""),
                diff=diff_content,
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

    def _parse_diff_stats(self, diff_content: str):
        additions = deletions = files_changed = 0
        files = set()
        for line in diff_content.splitlines():
            if line.startswith('diff --git'):
                files.add(line)
                files_changed += 1
            elif line.startswith('+') and not line.startswith('+++'):
                additions += 1
            elif line.startswith('-') and not line.startswith('---'):
                deletions += 1
        return files_changed, additions, deletions

    async def validate_credentials(self) -> bool:
        url = f"{self.API_BASE}/{self.username}?pagelen=1"
        try:
            resp = requests.get(url, auth=(self.username, self.app_password))
            return resp.status_code == 200
        except Exception:
            return False

    def get_pr_url(self, owner: str, repo: str, pr_number: int) -> str:
        return f"https://bitbucket.org/{owner}/{repo}/pull-requests/{pr_number}"
