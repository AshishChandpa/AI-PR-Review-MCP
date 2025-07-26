# PR Review MCP Server with Multi-LLM Support & Interactive Webhook Integration

A comprehensive Model Context Protocol (MCP) server that provides automated pull request reviews using multiple LLM providers (OpenAI, Claude, Gemini, Groq, Perplexity) with both GitHub and Bitbucket integration, featuring **real-time webhook processing** and **interactive AI assistant commands**.

## Features

- 🤖 **Multi-LLM Support**: OpenAI, Claude, Gemini, Groq, Perplexity
- 🔧 **Multi-Platform**: GitHub and Bitbucket integration
- 🖥️ **Web UI**: User-friendly interface for PR reviews
- 📡 **MCP Server**: Compatible with VS Code, Cursor, and other MCP clients
- 🔍 **Review Types**: Comprehensive, Security, Performance, Style reviews
- ⚡ **Real-time**: Instant PR analysis and feedback
- 🔔 **Webhook Integration**: Automatic PR review on creation/updates
- 💬 **Interactive Commands**: AI assistant responds to `/assistant` commands in PR comments
- 📝 **Commit-wise Analysis**: Individual commit review with inline comments
- 🛡️ **Security Analysis**: Dedicated security vulnerability scanning

## Prerequisites

- Python 3.8+
- Git
- API keys for your preferred LLM providers
- GitHub Personal Access Token (with `repo` and `pull_requests` scopes)
- (Optional) Bitbucket App Password
- Public URL for webhook endpoints (use ngrok, cloudflared, or similar for local development)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
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

# Default LLM Provider
DEFAULT_LLM_PROVIDER=openai
```

### 3. Run the Services

**Option A: Complete System (MCP + Web UI + Webhooks)**
```bash
python scripts/run_server.py
```

**Option B: Individual Services**
```bash
# MCP Server only
python src/mcp_server.py

# Web UI only
python ui/app.py

# Webhook servers only
python bitbucket_webhook_server.py  # Port 8050
python github_webhook_server.py     # Port 8051
```

This will start:
- ✅ MCP Server (stdio mode)
- ✅ Web UI at http://localhost:8080
- ✅ Bitbucket Webhook at http://localhost:8050/bitbucket-webhook
- ✅ GitHub Webhook at http://localhost:8051/github-webhook

### 4. Webhook Setup

#### For Local Development
```bash
# Expose webhooks publicly using cloudflared
cloudflared tunnel --url http://localhost:8050  # For Bitbucket
cloudflared tunnel --url http://localhost:8051  # For GitHub
```

#### Bitbucket Webhook Configuration
1. Go to your Bitbucket repository → Settings → Webhooks
2. Add webhook with URL: `https://your-domain.com/bitbucket-webhook`
3. Select these events:
   - `pullrequest:created`
   - `pullrequest:updated`
   - `pullrequest:comment_created`
   - `pullrequest:comment_updated`

#### GitHub Webhook Configuration
1. Go to your GitHub repository → Settings → Webhooks
2. Add webhook with URL: `https://your-domain.com/github-webhook`
3. Select these events:
   - `pull_request` (opened, synchronize, reopened)
   - `issue_comment` (created, edited)

## Usage

### 1. Automatic Webhook Reviews

Once webhooks are configured, the system automatically:
- **Reviews new PRs** when created
- **Re-reviews PRs** when updated with new commits
- **Analyzes each commit individually** with inline comments
- **Posts both general and inline feedback**

### 2. Interactive AI Assistant Commands

Use these commands in PR comments to interact with the AI assistant:

#### Basic Commands
```
/assistant
```
Triggers a full re-review of the entire PR

#### Get Suggestions
```
/assistant suggestion
/assistant suggestion for error handling
/assistant suggestion optimize performance
```

#### Explain Changes
```
/assistant explain
/assistant explain the database changes
/assistant explain why this approach was chosen
```

#### Security Analysis
```
/assistant security
```

#### Available Response Types
- **🤖 Full PR Review**: Complete re-analysis with inline comments
- **💡 Code Suggestions**: Targeted improvement recommendations  
- **📖 Change Explanation**: Detailed explanation of changes
- **🔒 Security Analysis**: Security vulnerability assessment

### 3. Web UI

1. Open http://localhost:8080
2. Select repository provider (GitHub/Bitbucket)
3. Choose LLM provider
4. Enter repository details:
   - **Owner**: `microsoft` (for microsoft/vscode)
   - **Repo**: `vscode`
   - **PR Number**: `123`
5. Click "Review Pull Request"

### 4. MCP Integration (VS Code/Cursor)

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

## Project Structure

```
mcp-pr-review/
├── README.md
├── requirements.txt
├── .env.example
├── bitbucket_webhook_server.py    # Bitbucket webhook listener
├── github_webhook_server.py       # GitHub webhook listener
├── config/
│   ├── settings.py
│   └── llm_providers.json
├── src/
│   ├── mcp_server.py              # Main MCP server
│   ├── models/
│   │   ├── pr_data.py             # PR data models
│   │   └── review_result.py       # Review result models
│   ├── providers/                 # LLM provider implementations
│   │   ├── base_provider.py
│   │   ├── openai_provider.py
│   │   ├── claude_provider.py
│   │   └── ...
│   ├── services/                  # Core services
│   │   ├── llm_service.py
│   │   ├── github_service.py
│   │   ├── bitbucket_service.py
│   │   ├── base_repo_service.py
│   │   ├── repo_service_factory.py
│   │   └── config_service.py
│   └── utils/
│       └── logger.py
├── ui/
│   ├── app.py                     # FastAPI web interface
│   ├── templates/
│   └── static/
└── scripts/
    └── run_server.py              # Server launcher
```

## Review Types & Features

### Automatic Review Features
- **Commit-wise Analysis**: Each commit reviewed individually
- **Inline Comments**: Specific suggestions on code lines
- **General Comments**: Overall PR assessment
- **Multi-file Support**: Reviews across all changed files

### Review Types
- **Comprehensive**: Full code review covering all aspects
- **Security**: Focus on vulnerabilities and security best practices
- **Performance**: Analyze performance implications and optimizations
- **Style**: Code style, consistency, and best practices

### Interactive Features
- **Command Recognition**: Responds to `/assistant` commands in comments
- **Context-Aware**: Understands specific requests (e.g., "explain database changes")
- **Threaded Replies**: Responses appear as comment replies
- **Multi-Platform**: Works on both GitHub and Bitbucket

## API Endpoints

### Webhook Endpoints
- `POST /bitbucket-webhook` - Handles Bitbucket PR and comment events
- `POST /github-webhook` - Handles GitHub PR and comment events

### Web UI Endpoints
- `GET /` - Main review interface
- `POST /api/review` - Manual PR review API
- `GET /api/providers` - List available LLM providers
- `GET /debug/providers` - Debug provider information

## Getting API Keys

### GitHub Token
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo` (full repository access), `pull_requests`
4. Copy the token to your `.env` file

### LLM Provider Keys
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic (Claude)**: https://console.anthropic.com/
- **Google (Gemini)**: https://ai.google.dev/
- **Groq**: https://console.groq.com/keys
- **Perplexity**: https://www.perplexity.ai/settings/api

### Bitbucket App Password (Optional)
1. Bitbucket → Personal settings → App passwords
2. Create app password with permissions: Repositories (Read), Pull requests (Read/Write)
3. Use your Bitbucket username (not email) + app password

## Troubleshooting

### Common Issues

1. **"No module named 'config'" error**:
   ```bash
   # Make sure you're in the project root directory
   cd mcp-pr-review
   python scripts/run_server.py
   ```

2. **Webhook not receiving events**:
   - Verify webhook URL is publicly accessible
   - Check webhook event configuration in repository settings
   - Review webhook server logs for errors

3. **Assistant commands not working**:
   - Ensure comment events are enabled in webhook configuration
   - Verify the comment contains `/assistant` at the beginning
   - Check authentication credentials

4. **GitHub 401 Unauthorized**:
   - Verify your GitHub token has `repo` and `pull_requests` scopes
   - Check token hasn't expired

5. **Bitbucket 401 Unauthorized**:
   - Use Bitbucket username (not email)
   - Use App Password (not login password)
   - Ensure app password has repository and PR permissions

### Debug Commands

```bash
# Test imports
python -c "from src.services.llm_service import LLMService; print('✓ Imports work')"

# Check providers
curl http://localhost:8080/api/providers

# Debug endpoint
curl http://localhost:8080/debug/providers

# Test webhook endpoints
curl -X POST http://localhost:8050/bitbucket-webhook -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:8051/github-webhook -H "Content-Type: application/json" -d '{}'
```

### Required Permissions

#### GitHub Token Scopes
- `repo` - Full repository access
- `pull_requests` - PR read/write access

#### Bitbucket App Password Permissions
- Repositories: Read
- Pull requests: Read, Write

## Development

### Adding New LLM Providers

1. Create provider class in `src/providers/`
2. Implement `BaseProvider` interface
3. Add to `LLMService._initialize_providers()`
4. Update configuration files

### Adding New Assistant Commands

1. Update `parse_assistant_command()` function
2. Add new command handler function
3. Update help text and documentation

### Extending Webhook Functionality

- Add new event types in webhook handlers
- Extend repository service classes for additional API endpoints
- Add new review types or analysis methods

## Example Workflows

### Workflow 1: Automatic Review
1. Developer creates/updates PR
2. Webhook triggers automatic review
3. System posts general comment and inline suggestions
4. Developer receives feedback instantly

### Workflow 2: Interactive Assistant
1. Developer comments: `/assistant suggestion for error handling`
2. Assistant analyzes PR focusing on error handling
3. Assistant replies with specific suggestions
4. Developer can ask follow-up questions

### Workflow 3: Security Review
1. Developer comments: `/assistant security`
2. Assistant performs security-focused analysis
3. Assistant reports potential vulnerabilities
4. Developer addresses security concerns

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Test webhook functionality with ngrok/cloudflared
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: Create an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check the `docs/` folder for detailed guides
- **Webhook Testing**: Use ngrok or cloudflared for local webhook testing

**Note**: This project requires at least one LLM provider API key to function. For webhook functionality, you'll also need publicly accessible URLs. Start with OpenAI for the most reliable experience, then add other providers and webhook integration as needed.

Sources
[1] base_repo_service.py https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/81348741/9928a771-5197-4379-a7c3-155d3c647bcb/base_repo_service.py
[2] bitbucket_service.py https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/81348741/1e7d4876-9ef7-43cd-9d99-82c91cd08fc5/bitbucket_service.py
[3] bitbucket_webhook_server.py https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/81348741/5137e542-49d9-4e21-90db-0b5dc396c475/bitbucket_webhook_server.py
