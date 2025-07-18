import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import json
import asyncio
from src.services.config_service import ConfigService
from src.services.llm_service import LLMService
from src.services.repo_service_factory import RepoServiceFactory

app = FastAPI(title="Multi-Provider PR Review MCP Server UI")
templates = Jinja2Templates(directory="ui/templates")
app.mount("/static", StaticFiles(directory="ui/static"), name="static")

# Initialize services
try:
    config_service = ConfigService()
    llm_service = LLMService()
except Exception as e:
    print(f"Service initialization error: {e}")
    config_service = None
    llm_service = None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        # Get LLM providers with full configuration
        llm_providers = llm_service.get_available_providers() if llm_service else {}

        # Get repository providers with status
        repo_provider_status = RepoServiceFactory.get_provider_status()
        repo_providers = list(repo_provider_status.keys())

        return templates.TemplateResponse("index.html", {
            "request": request,
            "llm_providers": llm_providers,
            "repo_providers": repo_providers,
            "repo_provider_status": repo_provider_status
        })
    except Exception as e:
        return HTMLResponse(f"Error loading page: {str(e)}", status_code=500)


@app.post("/api/review")
async def review_pr(
        owner: str = Form(...),
        repo: str = Form(...),
        pr_number: int = Form(...),
        repo_provider: str = Form("github"),
        llm_provider: str = Form(...),
        model: str = Form(None),
        review_type: str = Form("comprehensive")
):
    try:
        # Create repository service
        repo_service = RepoServiceFactory.create_service(repo_provider)

        # Get PR data
        pr_data = await repo_service.get_pr_diff(owner, repo, pr_number)

        # Perform review
        review_result = await llm_service.review_pr(
            pr_data, llm_provider, model, review_type
        )

        return JSONResponse({
            "success": True,
            "pr_info": {
                "title": pr_data.title,
                "number": pr_number,
                "files_changed": pr_data.files_changed,
                "additions": pr_data.additions,
                "deletions": pr_data.deletions,
                "provider": pr_data.provider,
                "url": repo_service.get_pr_url(owner, repo, pr_number)
            },
            "review": review_result.content,
            "llm_provider": llm_provider,
            "model": review_result.model_used,
            "review_type": review_type
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get("/api/providers")
async def get_providers():
    try:
        llm_providers = llm_service.get_available_providers() if llm_service else {}
        repo_providers = RepoServiceFactory.get_provider_status()

        return JSONResponse({
            "llm_providers": llm_providers,
            "repo_providers": repo_providers
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e)
        }, status_code=500)

@app.get("/debug/status")
async def debug_status():
    try:
        status = {
            "config_service": config_service is not None,
            "llm_service": llm_service is not None,
            "github_token": bool(os.getenv("GITHUB_TOKEN")),
            "openai_key": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic_key": bool(os.getenv("ANTHROPIC_API_KEY")),
        }
        return JSONResponse(status)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/debug/providers")
async def debug_providers():
    """Debug endpoint to check provider status"""
    try:
        debug_info = {
            "environment_variables": {
                "GITHUB_TOKEN": bool(os.getenv("GITHUB_TOKEN")),
                "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
                "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY")),
                "GOOGLE_API_KEY": bool(os.getenv("GOOGLE_API_KEY")),
                "GROQ_API_KEY": bool(os.getenv("GROQ_API_KEY")),
                "PERPLEXITY_API_KEY": bool(os.getenv("PERPLEXITY_API_KEY"))
            },
            "service_status": {
                "config_service": config_service is not None,
                "llm_service": llm_service is not None
            }
        }

        if llm_service:
            debug_info["llm_providers"] = llm_service.get_available_providers()

        return JSONResponse(debug_info)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/models/{provider}")
async def get_models_for_provider(provider: str):
    """Get available models for a specific LLM provider"""
    try:
        if not llm_service:
            return JSONResponse({"error": "LLM service not available"}, status_code=503)

        providers = llm_service.get_available_providers()
        if provider not in providers:
            return JSONResponse({"error": f"Provider {provider} not found"}, status_code=404)

        provider_info = providers[provider]
        return JSONResponse({
            "models": provider_info.get("models", []),
            "default_model": provider_info.get("default_model", "")
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)