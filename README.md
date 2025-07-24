# PR Review MCP Server with Multi-LLM Support

A comprehensive Model Context Protocol (MCP) server that provides automated pull request reviews using multiple LLM providers (OpenAI, Claude, Gemini, Groq, Perplexity) with both GitHub and Bitbucket integration.

## Features

- 🤖 **Multi-LLM Support**: OpenAI, Claude, Gemini, Groq, Perplexity
- 🔧 **Multi-Platform**: GitHub and Bitbucket integration
- 🖥️ **Web UI**: User-friendly interface for PR reviews
- 📡 **MCP Server**: Compatible with VS Code, Cursor, and other MCP clients
- 🔍 **Review Types**: Comprehensive, Security, Performance, Style reviews
- ⚡ **Real-time**: Instant PR analysis and feedback

## Prerequisites

- Python 3.8+
- Git
- API keys for your preferred LLM providers
- GitHub Personal Access Token
- (Optional) Bitbucket App Password

## Quick Start

### 1. Clone and Setup

```bash
git clone 
cd mcp-pr-review
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
# GitHub Configuration
GITHUB_TOKEN=your_github_token_here

# Bitbucket Configuration (Optional)
BITBUCKET_USERNAME=your_bitbucket_username
BITBUCKET_APP_PASSWORD=your_bitbucket_app_password

# LLM Provider API Keys (Add at least one)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_claude_key_here
GOOGLE_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here
```

### 3. Run the Server

```bash
python scripts/run_server.py
```

This will start:
- ✅ MCP Server (stdio mode)
- ✅ Web UI at http://localhost:8080

## Getting API Keys

### GitHub Token
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo` (full repository access)
4. Copy the token to your `.env` file

### LLM Provider Keys
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic (Claude)**: https://console.anthropic.com/
- **Google (Gemini)**: https://ai.google.dev/
- **Groq**: https://console.groq.com/keys
- **Perplexity**: https://www.perplexity.ai/settings/api

### Bitbucket App Password (Optional)
1. Bitbucket → Personal settings → App passwords
2. Create app password with permissions: Repositories (Read), Pull requests (Read)
3. Use your Bitbucket username (not email) + app password

## Usage

### Web UI
1. Open http://localhost:8080
2. Select repository provider (GitHub/Bitbucket)
3. Choose LLM provider
4. Enter repository details:
   - **Owner**: `microsoft` (for microsoft/vscode)
   - **Repo**: `vscode`
   - **PR Number**: `123`
5. Click "Review Pull Request"

### MCP Integration (VS Code/Cursor)

Add to your MCP configuration:

**VS Code** (`.vscode/settings.json`):
```json
{
  "mcpServers": {
    "pr-review-server": {
      "command": "python",
      "args": ["src/mcp_server.py"],
      "cwd": "/path/to/mcp-pr-review",
      "env": {
        "GITHUB_TOKEN": "your_github_token",
        "OPENAI_API_KEY": "your_openai_key"
      }
    }
  }
}
```

**Cursor** (`mcp.json`):
```json
{
  "mcpServers": {
    "pr-review-server": {
      "command": "python",
      "args": ["src/mcp_server.py"],
      "cwd": "/path/to/mcp-pr-review",
      "env": {
        "GITHUB_TOKEN": "your_github_token",
        "OPENAI_API_KEY": "your_openai_key"
      }
    }
  }
}
```

Then use commands like:
- "Review PR #123 in microsoft/vscode using OpenAI"
- "Get available providers"

## Project Structure

```
mcp-pr-review/
├── README.md
├── requirements.txt
├── .env.example
├── config/
│   ├── settings.py
│   └── llm_providers.json
├── src/
│   ├── mcp_server.py          # Main MCP server
│   ├── models/
│   │   ├── pr_data.py         # PR data models
│   │   └── review_result.py   # Review result models
│   ├── providers/             # LLM provider implementations
│   │   ├── base_provider.py
│   │   ├── openai_provider.py
│   │   ├── claude_provider.py
│   │   └── ...
│   ├── services/              # Core services
│   │   ├── llm_service.py
│   │   ├── github_service.py
│   │   ├── bitbucket_service.py
│   │   └── config_service.py
│   └── utils/
│       └── logger.py
├── ui/
│   ├── app.py                 # FastAPI web interface
│   ├── templates/
│   └── static/
└── scripts/
    └── run_server.py          # Server launcher
```

## Review Types

- **Comprehensive**: Full code review covering all aspects
- **Security**: Focus on vulnerabilities and security best practices
- **Performance**: Analyze performance implications and optimizations
- **Style**: Code style, consistency, and best practices

## Troubleshooting

### Common Issues

1. **"No module named 'config'" error**:
   ```bash
   # Make sure you're in the project root directory
   cd mcp-pr-review
   python scripts/run_server.py
   ```

2. **"Provider not available" error**:
   - Check your API keys in `.env`
   - Restart the server after adding new keys

3. **GitHub 401 Unauthorized**:
   - Verify your GitHub token has `repo` scope
   - Check token hasn't expired

4. **Bitbucket 401 Unauthorized**:
   - Use Bitbucket username (not email)
   - Use App Password (not login password)

### Debug Commands

```bash
# Test imports
python -c "from src.services.llm_service import LLMService; print('✓ Imports work')"

# Check providers
curl http://localhost:8080/api/providers

# Debug endpoint
curl http://localhost:8080/debug/providers
```

## Development

### Adding New LLM Providers

1. Create provider class in `src/providers/`
2. Implement `BaseProvider` interface
3. Add to `LLMService._initialize_providers()`
4. Update configuration files

### Extending Functionality

- Add new review types in `LLMService._generate_review_prompt()`
- Extend repository providers in `services/`
- Customize UI in `ui/templates/`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: Create an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check the `docs/` folder for detailed guides

**Note**: This project requires at least one LLM provider API key to function. Start with OpenAI for the most reliable experience, then add other providers as needed.
