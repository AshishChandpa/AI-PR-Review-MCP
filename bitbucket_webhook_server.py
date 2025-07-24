from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional


from src.services.llm_service import LLMService

import requests
from config.settings import settings
from src.services.repo_service_factory import RepoServiceFactory

import logging

app = FastAPI()

llm_service = LLMService()

def extract_info(payload: dict) -> Optional[dict]:
    """Extracts workspace, repo_slug, pr_id if possible. Returns None if not a valid PR webhook."""
    pr = payload.get("pullrequest", {})
    repo = payload.get("repository", {})
    workspace = (
        repo.get("workspace", {}).get("slug")
        or repo.get("project", {}).get("key")
        or repo.get("owner", {}).get("username")
    )
    repo_slug = repo.get("slug") or repo.get("name")
    pr_id = pr.get("id")
    if workspace and repo_slug and pr_id:
        return {
            "workspace": workspace,
            "repo_slug": repo_slug,
            "pr_id": pr_id
        }
    return None

@app.post("/bitbucket-webhook")
async def bitbucket_webhook(request: Request, background_tasks: BackgroundTasks):
    print("bitbucket webhook received")
    try:
        payload = await request.json()
    except Exception:
        payload = None

    # Require a JSON body
    if not payload:
        return JSONResponse(content={"status": "ignored", "detail": "No payload"}, status_code=200)

    event_key = request.headers.get("X-Event-Key", "")
    print(f"printing event key:{event_key}")
    # Handle PR events (existing logic)
    if event_key.startswith("pullrequest:") and event_key not in ["pullrequest:comment_created", "pullrequest:comment_updated"]:
        info = extract_info(payload)
        if not info:
            return JSONResponse(content={
                "status": "error",
                "detail": "Missing PR data"
            }, status_code=400)

        background_tasks.add_task(
            review_and_comment, info["workspace"], info["repo_slug"], info["pr_id"]
        )
        return JSONResponse(content={"status": "review started", "pr": info}, status_code=202)

    # NEW: Handle comment events
    elif event_key in ["pullrequest:comment_created", "pullrequest:comment_updated"]:
        comment_info = extract_comment_info(payload)
        if comment_info and is_assistant_command(comment_info["comment_text"]):
            background_tasks.add_task(
                handle_assistant_command,
                comment_info["workspace"],
                comment_info["repo_slug"],
                comment_info["pr_id"],
                comment_info["comment_text"],
                comment_info["comment_id"]
            )
            return JSONResponse(content={"status": "assistant command processed"}, status_code=202)
    return JSONResponse(content={"status": "ignored", "detail": f"Event {event_key} not processed"}, status_code=200)


def extract_comment_info(payload: dict) -> Optional[dict]:
    """Extract comment info from Bitbucket webhook payload"""
    comment = payload.get("comment", {})
    pr = payload.get("pullrequest", {})
    repo = payload.get("repository", {})

    workspace = (
            repo.get("workspace", {}).get("slug")
            or repo.get("project", {}).get("key")
            or repo.get("owner", {}).get("username")
    )
    repo_slug = repo.get("slug") or repo.get("name")
    pr_id = pr.get("id")
    comment_text = comment.get("content", {}).get("raw", "")
    comment_id = comment.get("id")

    if workspace and repo_slug and pr_id and comment_text:
        return {
            "workspace": workspace,
            "repo_slug": repo_slug,
            "pr_id": pr_id,
            "comment_text": comment_text,
            "comment_id": comment_id
        }
    return None


def is_assistant_command(comment_text: str) -> bool:
    """Check if comment contains assistant command"""
    return comment_text.strip().startswith("/assistant")


async def handle_assistant_command(workspace: str, repo: str, pr_id: int, comment_text: str, comment_id: int):
    """Process assistant commands"""
    try:
        command = parse_assistant_command(comment_text)

        if command["action"] == "review":
            await perform_full_review(workspace, repo, pr_id, comment_id)
        elif command["action"] == "suggestion":
            await provide_suggestions(workspace, repo, pr_id, comment_id, command.get("context"))
        elif command["action"] == "explain":
            await explain_changes(workspace, repo, pr_id, comment_id, command.get("context"))
        elif command["action"] == "security":
            await security_analysis(workspace, repo, pr_id, comment_id)
        else:
            await reply_to_comment(workspace, repo, pr_id, comment_id,
                                   "Available commands:\n- `/assistant` - Full review\n- `/assistant suggestion` - Get suggestions\n- `/assistant explain [topic]` - Explain changes\n- `/assistant security` - Security analysis")

    except Exception as e:
        logging.exception(f"Error handling assistant command: {e}")
        await reply_to_comment(workspace, repo, pr_id, comment_id,
                               "Sorry, I encountered an error processing your request.")


def parse_assistant_command(comment_text: str) -> dict:
    """Parse assistant command and extract action and context"""
    text = comment_text.strip()

    # Remove /assistant prefix
    if text.startswith("/assistant"):
        text = text[10:].strip()

    if not text or text == "":
        return {"action": "review"}
    elif "suggestion" in text.lower():
        return {"action": "suggestion", "context": text[10:].strip()}
    elif "explain" in text.lower():
        return {"action": "explain", "context": text[7:].strip()}
    elif "security" in text.lower():
        return {"action": "security"}
    else:
        return {"action": "help"}

async def review_and_comment(owner, repo, pr_number):
    try:
        print("Inside review_and_comment()")
        repo_service = RepoServiceFactory.create_service("bitbucket")
        pr_data = await repo_service.get_pr_diff(owner, repo, pr_number)

        # Use your LLM's updated inline-aware review method!
        review_result = await llm_service.review_inline_pr(
            pr_data, settings.DEFAULT_LLM_PROVIDER
        )

        # Post general comment
        if review_result.get("general_comment"):
            url = f"https://api.bitbucket.org/2.0/repositories/{owner}/{repo}/pullrequests/{pr_number}/comments"
            data = {"content": {"raw": review_result["general_comment"]}}
            auth = (settings.BITBUCKET_USERNAME, settings.BITBUCKET_APP_PASSWORD)
            resp = requests.post(url, auth=auth, json=data)
            resp.raise_for_status()
            print("Posted general comment.")

        # Post each inline comment
        for c in review_result.get("inline_comments", []):
            if all(k in c for k in ("file", "line", "comment")):
                url = f"https://api.bitbucket.org/2.0/repositories/{owner}/{repo}/pullrequests/{pr_number}/comments"
                data = {
                    "content": {"raw": c["comment"]},
                    "inline": {"path": c["file"], "to": c["line"]}
                }
                resp = requests.post(url, auth=auth, json=data)
                resp.raise_for_status()
                print(f"Posted inline comment to {c['file']}:{c['line']}.")

        print(f"Posted all comments for PR {pr_number} of {owner}/{repo}.")

    except Exception as e:
        logging.exception(f"Webhook review_and_comment error: {e}")


async def perform_full_review(workspace: str, repo: str, pr_id: int, comment_id: int):
    """Perform full PR review"""
    try:
        repo_service = RepoServiceFactory.create_service("bitbucket")
        pr_data = await repo_service.get_pr_diff(workspace, repo, pr_id)

        review_result = await llm_service.review_inline_pr(
            pr_data, settings.DEFAULT_LLM_PROVIDER
        )

        response_text = f"🤖 **Full PR Review Completed**\n\n{review_result.get('general_comment', 'Review completed successfully.')}"
        await reply_to_comment(workspace, repo, pr_id, comment_id, response_text, settings.DEFAULT_LLM_PROVIDER)

        # Post inline comments
        for c in review_result.get("inline_comments", []):
            if all(k in c for k in ("file", "line", "comment")):
                url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/pullrequests/{pr_id}/comments"
                data = {
                    "content": {"raw": f"🤖 **Assistant Review**: {c['comment']}"},
                    "inline": {"path": c["file"], "to": c["line"]}
                }
                auth = (settings.BITBUCKET_USERNAME, settings.BITBUCKET_APP_PASSWORD)
                resp = requests.post(url, auth=auth, json=data)
                resp.raise_for_status()

    except Exception as e:
        logging.exception(f"Error in full review: {e}")
        await reply_to_comment(workspace, repo, pr_id, comment_id, "Error performing review.")


async def provide_suggestions(workspace: str, repo: str, pr_id: int, comment_id: int, context: str = ""):
    """Provide code suggestions"""
    try:
        repo_service = RepoServiceFactory.create_service("bitbucket")
        pr_data = await repo_service.get_pr_diff(workspace, repo, pr_id)

        # Create a suggestion-focused prompt
        suggestion_prompt = f"Provide specific code improvement suggestions for this PR. Focus on: {context}" if context else "Provide specific code improvement suggestions for this PR."

        suggestions = await llm_service.get_suggestions(pr_data, suggestion_prompt)

        response_text = f"💡 **Code Suggestions**\n\n{suggestions}"
        await reply_to_comment(workspace, repo, pr_id, comment_id, response_text)

    except Exception as e:
        logging.exception(f"Error providing suggestions: {e}")
        await reply_to_comment(workspace, repo, pr_id, comment_id, "Error generating suggestions.")


async def explain_changes(workspace: str, repo: str, pr_id: int, comment_id: int, context: str = ""):
    """Explain changes in the PR"""
    try:
        repo_service = RepoServiceFactory.create_service("bitbucket")
        pr_data = await repo_service.get_pr_diff(workspace, repo, pr_id)

        explanation_prompt = f"Explain the changes in this PR, focusing on: {context}" if context else "Explain what changes were made in this PR and their impact."

        explanation = await llm_service.explain_changes(pr_data, explanation_prompt)

        response_text = f"📖 **Change Explanation**\n\n{explanation}"
        await reply_to_comment(workspace, repo, pr_id, comment_id, response_text)

    except Exception as e:
        logging.exception(f"Error explaining changes: {e}")
        await reply_to_comment(workspace, repo, pr_id, comment_id, "Error explaining changes.")


async def security_analysis(workspace: str, repo: str, pr_id: int, comment_id: int):
    """Perform security analysis"""
    try:
        repo_service = RepoServiceFactory.create_service("bitbucket")
        pr_data = await repo_service.get_pr_diff(workspace, repo, pr_id)

        security_issues = await llm_service.security_analysis(pr_data)

        response_text = f"🔒 **Security Analysis**\n\n{security_issues}"
        await reply_to_comment(workspace, repo, pr_id, comment_id, response_text)

    except Exception as e:
        logging.exception(f"Error in security analysis: {e}")
        await reply_to_comment(workspace, repo, pr_id, comment_id, "Error performing security analysis.")


async def reply_to_comment(workspace: str, repo: str, pr_id: int, comment_id: int, message: str, llm_provider: str = settings.DEFAULT_LLM_PROVIDER):
    """Reply to a specific comment"""
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/pullrequests/{pr_id}/comments"
    data = {
        "content": {"raw": message},
        "parent": {"id": comment_id}  # This makes it a reply
    }
    auth = (settings.BITBUCKET_USERNAME, settings.BITBUCKET_APP_PASSWORD)
    resp = requests.post(url, auth=auth, json=data)
    resp.raise_for_status()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8050)

# uvicorn bitbucket_webhook_server:app --host 0.0.0.0 --port 8050
#  cloudflared tunnel --url http://localhost:8050