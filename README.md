pr-review-mcp/
├── README.md
├── requirements.txt
├── setup.py
├── .env.example
├── .gitignore
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── llm_providers.json
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── mcp_server.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── pr_data.py
│   │   └── review_result.py
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base_provider.py
│   │   ├── openai_provider.py
│   │   ├── claude_provider.py
│   │   ├── gemini_provider.py
│   │   ├── groq_provider.py
│   │   └── perplexity_provider.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── github_service.py
│   │   ├── llm_service.py
│   │   └── config_service.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── exceptions.py
├── ui/
│   ├── __init__.py
│   ├── app.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py
│   │   └── main.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── config.html
│   │   └── review.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       ├── js/
│       │   └── app.js
│       └── img/
├── tests/
│   ├── __init__.py
│   ├── test_mcp_server.py
│   ├── test_providers.py
│   └── test_services.py
└── scripts/
    ├── install.py
    └── run_server.py


{
  "mcpServers": {
    "pr-review-server": {
      "command": "python",
      "args": ["src/mcp_server.py"],
      "env": {
        "GITHUB_TOKEN": "your_token",
        "OPENAI_API_KEY": "your_key"
      }
    }
  }
}
