from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional

# ---- Your imports ----

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
    try:
        payload = await request.json()
    except Exception:
        payload = None

    # Require a JSON body
    if not payload:
        return JSONResponse(content={"status": "ignored", "detail": "No payload"}, status_code=200)

    event_key = request.headers.get("X-Event-Key", "")

    # Only process PR created/updated, ignore others
    if not (event_key.startswith("pullrequest:")):
        return JSONResponse(content={"status": "ignored", "detail": f"Event {event_key} not a PR event"}, status_code=200)

    info = extract_info(payload)
    if not info:
        return JSONResponse(content={
            "status": "error",
            "detail": "Missing PR data (need pullrequest.id, repository.workspace.slug/project.key, repository.slug/name)"
        }, status_code=400)

    # Trigger review in the background
    background_tasks.add_task(
        review_and_comment, info["workspace"], info["repo_slug"], info["pr_id"]
    )
    return JSONResponse(content={"status": "review started", "pr": info}, status_code=202)



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
        for c in review_result["inline_comments"]:
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8050)

# uvicorn bitbucket_webhook_server:app --host 0.0.0.0 --port 8050
#  cloudflared tunnel --url http://localhost:8050