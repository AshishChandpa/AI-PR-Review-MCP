import asyncio
import json
import sys
import os
from typing import Dict, Any
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from mcp.server.http import http_server
from mcp.types import Tool, TextContent


# Simple fallback logger
def simple_logger(message: str):
    print(f"[MCP-HTTP] {message}")


# Initialize the MCP server
app = Server("pr-review-multi-provider")


# Initialize services
def initialize_services():
    """Initialize services with proper error handling"""
    try:
        from src.services.llm_service import LLMService
        from src.services.config_service import ConfigService

        config_service = ConfigService()
        llm_service = LLMService()

        simple_logger("Services initialized successfully")
        return config_service, llm_service
    except Exception as e:
        simple_logger(f"Service initialization failed: {e}")
        return None, None


config_service, llm_service = initialize_services()


@app.list_tools()
async def list_tools():
    """List available tools"""
    return [
        Tool(
            name="review_pr",
            description="Analyze a GitHub PR using specified LLM provider",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "pr_number": {"type": "integer"},
                    "llm_provider": {"type": "string", "default": "openai"},
                    "review_type": {"type": "string", "default": "comprehensive"}
                },
                "required": ["owner", "repo", "pr_number"]
            }
        ),
        Tool(
            name="test_connection",
            description="Test MCP server connection",
            inputSchema={"type": "object", "properties": {}}
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    """Handle tool calls"""
    try:
        if name == "review_pr":
            return await review_pr(**arguments)
        elif name == "test_connection":
            return [TextContent(type="text", text="MCP HTTP Server is running! 🚀")]
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def review_pr(owner: str, repo: str, pr_number: int,
                    llm_provider: str = "openai", review_type: str = "comprehensive"):
    """Review a PR"""
    if not llm_service or not config_service:
        return [TextContent(type="text", text="Services not initialized")]

    try:
        from src.services.repo_service_factory import RepoServiceFactory

        repo_service = RepoServiceFactory.create_service("github")
        pr_data = await repo_service.get_pr_diff(owner, repo, pr_number)
        review_result = await llm_service.review_pr(pr_data, llm_provider, None, review_type)

        response = {
            "success": True,
            "pr_info": {
                "title": pr_data.title,
                "number": pr_number,
                "files_changed": pr_data.files_changed,
                "additions": pr_data.additions,
                "deletions": pr_data.deletions
            },
            "review": review_result.content,
            "llm_provider": llm_provider
        }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error reviewing PR: {str(e)}")]


async def main():
    """Run HTTP server"""
    try:
        simple_logger("Starting MCP HTTP Server...")
        async with http_server(app, host="localhost", port=8001) as (server, url):
            simple_logger(f"MCP HTTP Server running at {url}")
            await server.serve()
    except Exception as e:
        simple_logger(f"HTTP Server error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
