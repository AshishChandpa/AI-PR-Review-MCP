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
        self.api_url = "https://api.bitbucket.org/2.0"
        self.auth = (self.username, self.app_password)

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> PRData:
        """Get PR data and diff from Bitbucket Cloud via direct REST"""
        base_url = f"https://api.bitbucket.org/2.0/repositories/{owner}/{repo}"
        auth = (self.username, self.app_password)

        # Pull request main data
        pr_url = f"{base_url}/pullrequests/{pr_number}"
        pr_resp = requests.get(pr_url, auth=auth)
        pr_resp.raise_for_status()
        pr_data_json = pr_resp.json()

        # Pull request diff (text)
        diff_url = f"{base_url}/pullrequests/{pr_number}/diff"
        diff_resp = requests.get(diff_url, auth=auth)
        diff_resp.raise_for_status()
        diff = diff_resp.text

        title = pr_data_json.get('title', '')
        description = pr_data_json.get('description', '')
        # Optional: fetch more stats, e.g., files_changed, additions, deletions
        # Minimal example:
        files_changed = pr_data_json.get('changed_files', 0)
        additions = pr_data_json.get('additions', 0)
        deletions = pr_data_json.get('deletions', 0)

        return PRData(
            title=title,
            description=description,
            diff=diff,
            files_changed=files_changed,
            additions=additions,
            deletions=deletions,
            number=pr_number,
            owner=owner,
            repo=repo,
            provider="bitbucket"
        )

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

    async def add_inline_comment(self, owner, repo, pr_number, file_path, line, comment_text):
        """
        Post an inline comment to a specific file and line in a PR.
        """
        url = f"{self.api_url}/repositories/{owner}/{repo}/pullrequests/{pr_number}/comments"
        body = {
            "content": {"raw": comment_text},
            "inline": {
                "path": file_path,
                "to": line  # Or use "from": line for old, "to": for new line context
            }
        }
        response = requests.post(url, auth=self.auth, json=body)
        response.raise_for_status()
        return response.json()
