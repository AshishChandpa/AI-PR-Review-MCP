class PRReviewError(Exception):
    """Base exception for PR review errors"""
    pass

class ProviderError(PRReviewError):
    """Exception for LLM provider errors"""
    pass

class GitHubError(PRReviewError):
    """Exception for GitHub API errors"""
    pass
