import asyncio
import json
import sys
import os
from typing import Dict, Any, List
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# Simple fallback logger
def simple_logger(message: str):
    print(f"[MCP] {message}")


# Initialize the MCP server
app = Server("pr-review-multi-provider")


# Simple service initialization with fallbacks
def initialize_services():
    """Initialize services with proper error handling"""
    try:
        from src.services.llm_service import LLMService
        from src.services.config_service import ConfigService
        from src.services.repo_service_factory import RepoServiceFactory

        config_service = ConfigService()
        llm_service = LLMService()

        simple_logger("Services initialized successfully")
        return config_service, llm_service
    except Exception as e:
        simple_logger(f"Service initialization failed: {e}")
        return None, None


# Initialize services
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
                    "owner": {
                        "type": "string",
                        "description": "Repository owner (GitHub username or organization)"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "pr_number": {
                        "type": "integer",
                        "description": "Pull request number"
                    },
                    "repo_provider": {
                        "type": "string",
                        "enum": ["github"],
                        "default": "github",
                        "description": "Repository provider (currently only github)"
                    },
                    "llm_provider": {
                        "type": "string",
                        "description": "LLM provider to use for review (openai, claude, etc.)"
                    },
                    "review_type": {
                        "type": "string",
                        "enum": ["comprehensive", "security", "performance", "style"],
                        "default": "comprehensive",
                        "description": "Type of review to perform"
                    }
                },
                "required": ["owner", "repo", "pr_number"]
            }
        ),
        Tool(
            name="get_available_providers",
            description="Get list of available LLM providers",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="test_connection",
            description="Test MCP server connection",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    """Handle tool calls"""
    try:
        if name == "review_pr":
            return await review_pr(**arguments)
        elif name == "get_available_providers":
            return await get_available_providers()
        elif name == "test_connection":
            return await test_connection()
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        error_msg = f"Error in tool {name}: {str(e)}"
        simple_logger(error_msg)
        return [TextContent(type="text", text=error_msg)]


async def review_pr(owner: str, repo: str, pr_number: int,
                    repo_provider: str = "github", llm_provider: str = "openai",
                    review_type: str = "comprehensive"):
    """Review a PR using specified providers"""

    if not llm_service or not config_service:
        return [TextContent(type="text", text="Error: Services not initialized. Please check your configuration.")]

    try:
        # Import here to avoid circular imports
        from src.services.repo_service_factory import RepoServiceFactory

        # Create repository service
        repo_service = RepoServiceFactory.create_service(repo_provider)

        # Get PR data
        pr_data = await repo_service.get_pr_diff(owner, repo, pr_number)

        # Perform review
        review_result = await llm_service.review_pr(
            pr_data, llm_provider, None, review_type
        )

        # Format response
        response = {
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
        }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    except Exception as e:
        error_msg = f"Error reviewing PR: {str(e)}"
        simple_logger(error_msg)
        return [TextContent(type="text", text=error_msg)]


async def get_available_providers():
    """Get available providers"""
    try:
        if not config_service:
            return [TextContent(type="text", text="Config service not available")]

        providers = config_service.get_available_providers()
        return [TextContent(type="text", text=json.dumps(providers, indent=2))]

    except Exception as e:
        error_msg = f"Error getting providers: {str(e)}"
        simple_logger(error_msg)
        return [TextContent(type="text", text=error_msg)]


async def test_connection():
    """Test MCP server connection"""
    return [TextContent(type="text", text="MCP Server is running successfully! 🚀")]


def main():
    """Main function to run the MCP server"""
    try:
        simple_logger("Starting MCP Server...")

        # Use asyncio.run with a simple server setup
        asyncio.run(run_server())

    except KeyboardInterrupt:
        simple_logger("Server stopped by user")
    except Exception as e:
        simple_logger(f"Server error: {str(e)}")


async def run_server():
    """Run the server with proper error handling"""
    try:
        async with stdio_server(app) as (read_stream, write_stream):
            simple_logger("MCP Server started successfully")
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except Exception as e:
        simple_logger(f"Server run error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
