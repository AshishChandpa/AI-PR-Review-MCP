"""
Bitbucket AI Assistant Webhook Handler
Similar to GitHub Copilot - provides intelligent PR reviews and interactive assistance
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import asyncio

import requests
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from src.services.llm_service import LLMService
from src.services.repo_service_factory import RepoServiceFactory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Bitbucket AI Assistant",
    description="AI-powered code review assistant for Bitbucket repositories",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
llm_service = LLMService()


class EventType(Enum):
    """Bitbucket webhook event types we handle"""
    PR_CREATED = "pullrequest:created"
    PR_UPDATED = "pullrequest:updated"
    PR_APPROVED = "pullrequest:approved"
    PR_COMMENT_CREATED = "pullrequest:comment_created"
    PR_COMMENT_UPDATED = "pullrequest:comment_updated"


class AssistantCommand(Enum):
    """Available assistant commands"""
    REVIEW = "review"
    SUGGESTION = "suggestion"
    EXPLAIN = "explain"
    SECURITY = "security"
    HELP = "help"
    SUMMARIZE = "summarize"
    TEST = "test"


@dataclass
class PullRequestInfo:
    """Pull request information extracted from webhook"""
    workspace: str
    repo_slug: str
    pr_id: int

    def __str__(self) -> str:
        return f"{self.workspace}/{self.repo_slug}/pull-requests/{self.pr_id}"


@dataclass
class CommentInfo:
    """Comment information extracted from webhook"""
    workspace: str
    repo_slug: str
    pr_id: int
    comment_text: str
    comment_id: int
    author: str = ""

    def __str__(self) -> str:
        return f"Comment {self.comment_id} on PR {self.pr_id}"


class WebhookProcessor:
    """Handles webhook processing logic"""

    @staticmethod
    def extract_pr_info(payload: Dict[str, Any]) -> Optional[PullRequestInfo]:
        """
        Extract PR information from Bitbucket webhook payload

        Args:
            payload: Webhook payload from Bitbucket

        Returns:
            PullRequestInfo if valid PR data found, None otherwise
        """
        try:
            pr = payload.get("pullrequest", {})
            repo = payload.get("repository", {})

            workspace = (
                    repo.get("workspace", {}).get("slug") or
                    repo.get("project", {}).get("key") or
                    repo.get("owner", {}).get("username")
            )

            repo_slug = repo.get("slug") or repo.get("name")
            pr_id = pr.get("id")

            if all([workspace, repo_slug, pr_id]):
                return PullRequestInfo(
                    workspace=workspace,
                    repo_slug=repo_slug,
                    pr_id=pr_id
                )

        except Exception as e:
            logger.error(f"Error extracting PR info: {e}")

        return None

    @staticmethod
    def extract_comment_info(payload: Dict[str, Any]) -> Optional[CommentInfo]:
        """
        Extract comment information from Bitbucket webhook payload

        Args:
            payload: Webhook payload from Bitbucket

        Returns:
            CommentInfo if valid comment data found, None otherwise
        """
        try:
            comment = payload.get("comment", {})
            pr = payload.get("pullrequest", {})
            repo = payload.get("repository", {})

            workspace = (
                    repo.get("workspace", {}).get("slug") or
                    repo.get("project", {}).get("key") or
                    repo.get("owner", {}).get("username")
            )

            repo_slug = repo.get("slug") or repo.get("name")
            pr_id = pr.get("id")
            comment_text = comment.get("content", {}).get("raw", "")
            comment_id = comment.get("id")
            author = comment.get("user", {}).get("display_name", "")

            if all([workspace, repo_slug, pr_id, comment_text, comment_id]):
                return CommentInfo(
                    workspace=workspace,
                    repo_slug=repo_slug,
                    pr_id=pr_id,
                    comment_text=comment_text,
                    comment_id=comment_id,
                    author=author
                )

        except Exception as e:
            logger.error(f"Error extracting comment info: {e}")

        return None


class AssistantCommandParser:
    """Parses and handles assistant commands"""

    COMMAND_PREFIX = "/assistant"

    @classmethod
    def is_assistant_command(cls, comment_text: str) -> bool:
        """Check if comment contains assistant command"""
        return comment_text.strip().lower().startswith(cls.COMMAND_PREFIX.lower())

    @classmethod
    def parse_command(cls, comment_text: str) -> Dict[str, Any]:
        """
        Parse assistant command and extract action and context

        Args:
            comment_text: Raw comment text

        Returns:
            Dictionary with action and context
        """
        text = comment_text.strip().lower()

        # Remove command prefix
        if text.startswith(cls.COMMAND_PREFIX.lower()):
            text = text[len(cls.COMMAND_PREFIX):].strip()

        # Parse different commands
        if not text:
            return {"action": AssistantCommand.REVIEW.value}
        elif "suggestion" in text or "improve" in text:
            return {"action": AssistantCommand.SUGGESTION.value, "context": text}
        elif "explain" in text:
            return {"action": AssistantCommand.EXPLAIN.value, "context": text}
        elif "security" in text or "secure" in text:
            return {"action": AssistantCommand.SECURITY.value}
        elif "summarize" in text or "summary" in text:
            return {"action": AssistantCommand.SUMMARIZE.value}
        elif "test" in text:
            return {"action": AssistantCommand.TEST.value}
        elif "help" in text:
            return {"action": AssistantCommand.HELP.value}
        else:
            return {"action": AssistantCommand.HELP.value}


class BitbucketAPIClient:
    """Handles Bitbucket API interactions"""

    def __init__(self):
        self.base_url = "https://api.bitbucket.org/2.0"
        self.auth = (settings.BITBUCKET_USERNAME, settings.BITBUCKET_APP_PASSWORD)

    async def post_comment(self, workspace: str, repo: str, pr_id: int,
                           content: str, parent_id: Optional[int] = None,
                           inline_data: Optional[Dict] = None) -> bool:
        """
        Post a comment to a pull request

        Args:
            workspace: Bitbucket workspace
            repo: Repository name
            pr_id: Pull request ID
            content: Comment content
            parent_id: Parent comment ID for replies
            inline_data: Inline comment data (file, line)

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/repositories/{workspace}/{repo}/pullrequests/{pr_id}/comments"

            data = {"content": {"raw": content}}

            if parent_id:
                data["parent"] = {"id": parent_id}

            if inline_data:
                data["inline"] = inline_data

            response = requests.post(url, auth=self.auth, json=data, timeout=30)
            response.raise_for_status()

            logger.info(f"Posted comment to {workspace}/{repo}/PR-{pr_id}")
            return True

        except Exception as e:
            logger.error(f"Error posting comment: {e}")
            return False

    async def post_inline_comments(self, workspace: str, repo: str, pr_id: int,
                                   inline_comments: List[Dict]) -> int:
        """
        Post multiple inline comments

        Returns:
            Number of successfully posted comments
        """
        success_count = 0

        for comment in inline_comments:
            if all(key in comment for key in ("file", "line", "comment")):
                inline_data = {"path": comment["file"], "to": comment["line"]}
                content = f"🤖 **AI Review**: {comment['comment']}"

                if await self.post_comment(workspace, repo, pr_id, content,
                                           inline_data=inline_data):
                    success_count += 1

        return success_count


class AssistantService:
    """Main service for handling assistant operations"""

    def __init__(self):
        self.api_client = BitbucketAPIClient()

    async def handle_command(self, comment_info: CommentInfo, command: Dict[str, Any]):
        """
        Handle assistant command

        Args:
            comment_info: Comment information
            command: Parsed command dictionary
        """
        action = command.get("action")
        context = command.get("context", "")

        try:
            if action == AssistantCommand.REVIEW.value:
                await self._perform_full_review(comment_info)
            elif action == AssistantCommand.SUGGESTION.value:
                await self._provide_suggestions(comment_info, context)
            elif action == AssistantCommand.EXPLAIN.value:
                await self._explain_changes(comment_info, context)
            elif action == AssistantCommand.SECURITY.value:
                await self._security_analysis(comment_info)
            elif action == AssistantCommand.SUMMARIZE.value:
                await self._summarize_pr(comment_info)
            elif action == AssistantCommand.TEST.value:
                await self._suggest_tests(comment_info)
            else:
                await self._show_help(comment_info)

        except Exception as e:
            logger.exception(f"Error handling command {action}: {e}")
            await self._reply_with_error(comment_info)

    async def _perform_full_review(self, comment_info: CommentInfo):
        """Perform comprehensive PR review"""
        repo_service = RepoServiceFactory.create_service("bitbucket")
        pr_data = await repo_service.get_pr_diff(
            comment_info.workspace, comment_info.repo_slug, comment_info.pr_id
        )

        review_result = await llm_service.review_inline_pr(
            pr_data, settings.DEFAULT_LLM_PROVIDER
        )

        # Post general review comment
        general_comment = f"""🤖 **AI Code Review Complete**

{review_result.get('general_comment', 'Review completed successfully.')}

---
*Review generated by Bitbucket AI Assistant*"""

        await self.api_client.post_comment(
            comment_info.workspace, comment_info.repo_slug, comment_info.pr_id,
            general_comment, comment_info.comment_id
        )

        # Post inline comments
        inline_count = await self.api_client.post_inline_comments(
            comment_info.workspace, comment_info.repo_slug, comment_info.pr_id,
            review_result.get("inline_comments", [])
        )

        logger.info(f"Posted {inline_count} inline comments for PR review")

    async def _provide_suggestions(self, comment_info: CommentInfo, context: str):
        """Provide code improvement suggestions"""
        repo_service = RepoServiceFactory.create_service("bitbucket")
        pr_data = await repo_service.get_pr_diff(
            comment_info.workspace, comment_info.repo_slug, comment_info.pr_id
        )

        prompt = f"Provide specific code improvement suggestions. Context: {context}" if context else "Provide code improvement suggestions"
        suggestions = await llm_service.get_suggestions(pr_data, prompt)

        response = f"""💡 **Code Suggestions**

{suggestions}

---
*Suggestions by AI Assistant*"""

        await self.api_client.post_comment(
            comment_info.workspace, comment_info.repo_slug, comment_info.pr_id,
            response, comment_info.comment_id
        )

    async def _explain_changes(self, comment_info: CommentInfo, context: str):
        """Explain changes in the PR"""
        repo_service = RepoServiceFactory.create_service("bitbucket")
        pr_data = await repo_service.get_pr_diff(
            comment_info.workspace, comment_info.repo_slug, comment_info.pr_id
        )

        prompt = f"Explain changes focusing on: {context}" if context else "Explain the changes and their impact"
        explanation = await llm_service.explain_changes(pr_data, prompt)

        response = f"""📖 **Change Explanation**

{explanation}

---
*Explanation by AI Assistant*"""

        await self.api_client.post_comment(
            comment_info.workspace, comment_info.repo_slug, comment_info.pr_id,
            response, comment_info.comment_id
        )

    async def _security_analysis(self, comment_info: CommentInfo):
        """Perform security analysis"""
        repo_service = RepoServiceFactory.create_service("bitbucket")
        pr_data = await repo_service.get_pr_diff(
            comment_info.workspace, comment_info.repo_slug, comment_info.pr_id
        )

        security_analysis = await llm_service.security_analysis(pr_data)

        response = f"""🔒 **Security Analysis**

{security_analysis}

---
*Security analysis by AI Assistant*"""

        await self.api_client.post_comment(
            comment_info.workspace, comment_info.repo_slug, comment_info.pr_id,
            response, comment_info.comment_id
        )

    async def _summarize_pr(self, comment_info: CommentInfo):
        """Summarize PR changes"""
        repo_service = RepoServiceFactory.create_service("bitbucket")
        pr_data = await repo_service.get_pr_diff(
            comment_info.workspace, comment_info.repo_slug, comment_info.pr_id
        )

        summary = await llm_service.summarize_pr(pr_data)

        response = f"""📋 **PR Summary**

{summary}

---
*Summary by AI Assistant*"""

        await self.api_client.post_comment(
            comment_info.workspace, comment_info.repo_slug, comment_info.pr_id,
            response, comment_info.comment_id
        )

    async def _suggest_tests(self, comment_info: CommentInfo):
        """Suggest test cases"""
        repo_service = RepoServiceFactory.create_service("bitbucket")
        pr_data = await repo_service.get_pr_diff(
            comment_info.workspace, comment_info.repo_slug, comment_info.pr_id
        )

        test_suggestions = await llm_service.suggest_tests(pr_data)

        response = f"""🧪 **Test Suggestions**

{test_suggestions}

---
*Test suggestions by AI Assistant*"""

        await self.api_client.post_comment(
            comment_info.workspace, comment_info.repo_slug, comment_info.pr_id,
            response, comment_info.comment_id
        )

    async def _show_help(self, comment_info: CommentInfo):
        """Show available commands"""
        help_text = """🤖 **AI Assistant Commands**

Available commands:
- `/assistant` or `/assistant review` - Full PR review
- `/assistant suggestion` - Get code improvement suggestions  
- `/assistant explain [topic]` - Explain changes
- `/assistant security` - Security analysis
- `/assistant summarize` - Summarize PR changes
- `/assistant test` - Suggest test cases
- `/assistant help` - Show this help

---
*Your AI-powered code review assistant*"""

        await self.api_client.post_comment(
            comment_info.workspace, comment_info.repo_slug, comment_info.pr_id,
            help_text, comment_info.comment_id
        )

    async def _reply_with_error(self, comment_info: CommentInfo):
        """Reply with error message"""
        error_text = """❌ **Error**

Sorry, I encountered an error processing your request. Please try again or contact support.

---
*AI Assistant*"""

        await self.api_client.post_comment(
            comment_info.workspace, comment_info.repo_slug, comment_info.pr_id,
            error_text, comment_info.comment_id
        )


# Initialize services
assistant_service = AssistantService()
webhook_processor = WebhookProcessor()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Bitbucket AI Assistant",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": "2025-08-05T18:30:00Z",
        "services": {
            "llm_service": "active",
            "bitbucket_api": "active"
        }
    }


@app.post("/bitbucket-webhook")
async def bitbucket_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Main webhook endpoint for Bitbucket events
    Handles PR events and comment-based assistant commands
    """
    logger.info("🔔 Bitbucket webhook received")

    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Invalid JSON payload: {e}")
        return JSONResponse(
            content={"status": "error", "detail": "Invalid JSON payload"},
            status_code=400
        )

    if not payload:
        return JSONResponse(
            content={"status": "ignored", "detail": "Empty payload"},
            status_code=200
        )

    event_key = request.headers.get("X-Event-Key", "")
    logger.info(f"📨 Processing event: {event_key}")

    # Handle PR lifecycle events (auto-review)
    if event_key in [EventType.PR_CREATED.value, EventType.PR_UPDATED.value]:
        pr_info = webhook_processor.extract_pr_info(payload)

        if not pr_info:
            return JSONResponse(
                content={"status": "error", "detail": "Invalid PR data"},
                status_code=400
            )

        # Add automatic review task
        background_tasks.add_task(
            perform_automatic_review, pr_info
        )

        logger.info(f"🚀 Scheduled automatic review for {pr_info}")
        return JSONResponse(
            content={
                "status": "review_scheduled",
                "pr": str(pr_info),
                "event": event_key
            },
            status_code=202
        )

    # Handle comment-based assistant commands
    elif event_key in [EventType.PR_COMMENT_CREATED.value, EventType.PR_COMMENT_UPDATED.value]:
        comment_info = webhook_processor.extract_comment_info(payload)

        if not comment_info:
            return JSONResponse(
                content={"status": "ignored", "detail": "Invalid comment data"},
                status_code=200
            )

        # Check if it's an assistant command
        if AssistantCommandParser.is_assistant_command(comment_info.comment_text):
            command = AssistantCommandParser.parse_command(comment_info.comment_text)

            # Add command handling task
            background_tasks.add_task(
                assistant_service.handle_command, comment_info, command
            )

            logger.info(f"🤖 Processing assistant command: {command['action']} for {comment_info}")
            return JSONResponse(
                content={
                    "status": "command_processing",
                    "command": command['action'],
                    "comment": str(comment_info)
                },
                status_code=202
            )

    # Event not handled
    logger.info(f"⏭️ Ignoring event: {event_key}")
    return JSONResponse(
        content={"status": "ignored", "detail": f"Event {event_key} not processed"},
        status_code=200
    )


async def perform_automatic_review(pr_info: PullRequestInfo):
    """
    Perform automatic PR review (similar to GitHub Copilot auto-review)
    """
    try:
        logger.info(f"🔍 Starting automatic review for {pr_info}")

        repo_service = RepoServiceFactory.create_service("bitbucket")
        pr_data = await repo_service.get_pr_diff(
            pr_info.workspace, pr_info.repo_slug, pr_info.pr_id
        )

        # Get AI review
        review_result = await llm_service.review_inline_pr(
            pr_data, settings.DEFAULT_LLM_PROVIDER
        )

        api_client = BitbucketAPIClient()

        # Post general review comment
        if review_result.get("general_comment"):
            general_comment = f"""🤖 **Automatic AI Review**

{review_result["general_comment"]}

---
*Automatic review by AI Assistant • Use `/assistant help` for more commands*"""

            await api_client.post_comment(
                pr_info.workspace, pr_info.repo_slug, pr_info.pr_id,
                general_comment
            )

        # Post inline comments
        inline_count = await api_client.post_inline_comments(
            pr_info.workspace, pr_info.repo_slug, pr_info.pr_id,
            review_result.get("inline_comments", [])
        )

        logger.info(f"✅ Completed automatic review for {pr_info} - {inline_count} inline comments")

    except Exception as e:
        logger.exception(f"❌ Error in automatic review for {pr_info}: {e}")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting Bitbucket AI Assistant")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8050,
        log_level="info"
    )

# To run:
# uvicorn bitbucket_webhook_server:app --host 0.0.0.0 --port 8050 --reload
# cloudflared tunnel --url http://localhost:8050
