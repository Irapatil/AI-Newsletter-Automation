# Folder Structure

```
AI-Newsletter-Automation/
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml            # black / isort / ruff / mypy / pytest config
├── Dockerfile
├── docker-compose.yml
├── Makefile
│
├── app/
│   ├── main.py                        # FastAPI app factory + entrypoint
│   │
│   ├── api/
│   │   ├── routes.py                  # GET /, /health, POST /generate-newsletter, /newsletter/*
│   │   └── dependencies.py            # X-API-Key auth dependency
│   │
│   ├── agents/
│   │   ├── base_agent.py              # BaseCollectorAgent (retry/logging/freshness filter)
│   │   ├── global_news_agent.py
│   │   ├── company_news_agent.py
│   │   ├── funding_agent.py
│   │   ├── talent_agent.py
│   │   ├── research_agent.py
│   │   ├── opensource_agent.py
│   │   ├── policy_agent.py
│   │   ├── model_release_agent.py
│   │   ├── aggregator_agent.py
│   │   ├── deduplication_agent.py
│   │   ├── ranking_agent.py
│   │   ├── newsletter_generator_agent.py
│   │   └── html_formatter_agent.py
│   │
│   ├── graph/
│   │   ├── workflow.py                # StateGraph construction (nodes, edges, retry policies)
│   │   └── nodes.py                   # Node functions adapting agents to GraphState
│   │
│   ├── services/
│   │   ├── llm_service.py             # OpenAI / Azure OpenAI / Mock LLM + embeddings
│   │   ├── http_client.py             # Shared async HTTP client (retry, timeout)
│   │   ├── rss_service.py             # RSS/Atom parsing (feedparser)
│   │   ├── arxiv_service.py
│   │   ├── github_service.py
│   │   ├── huggingface_service.py
│   │   ├── newsapi_service.py
│   │   ├── job_boards_service.py      # Greenhouse + Lever
│   │   ├── linkedin_provider.py       # LinkedIn provider abstraction (mock/api)
│   │   ├── funding_provider.py        # Crunchbase provider abstraction + Google News fallback
│   │   └── history_service.py         # Filesystem-backed newsletter persistence
│   │
│   ├── models/
│   │   ├── article.py                 # Article, NewsCategory, ArticleScores
│   │   ├── newsletter.py              # NewsletterContent, NewsletterSection, NewsletterOutput
│   │   ├── state.py                   # GraphState (LangGraph shared state)
│   │   └── api_models.py              # FastAPI request/response schemas
│   │
│   ├── config/
│   │   ├── settings.py                # Pydantic BaseSettings (env-driven configuration)
│   │   ├── sources.py                 # RSS feeds, API URLs, source credibility registry
│   │   └── logging_config.py          # structlog configuration
│   │
│   ├── utils/
│   │   ├── retry.py                   # tenacity-based retry decorator
│   │   └── text_utils.py              # HTML stripping, cosine similarity, freshness math
│   │
│   └── templates/
│       └── newsletter.html.j2         # Jinja2 email template (inline-styled, table-based)
│
├── tests/
│   ├── conftest.py                    # Shared fixtures (sample articles, settings reset)
│   ├── fixtures/                      # Sample RSS payloads etc.
│   ├── test_agents/
│   ├── test_services/
│   ├── test_graph/
│   └── test_api/
│
├── docs/
│   ├── ARCHITECTURE.md                # Architecture + sequence diagrams
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── POWER_AUTOMATE.md
│   ├── ENVIRONMENT_VARIABLES.md
│   ├── FOLDER_STRUCTURE.md            # (this file)
│   ├── TROUBLESHOOTING.md
│   ├── ROADMAP.md
│   └── images/                        # Screenshot placeholders referenced by POWER_AUTOMATE.md
│
├── scripts/
│   └── generate_newsletter_cli.py     # Run the pipeline locally without the API
│
├── data/
│   └── history/                       # Persisted newsletter JSON (gitignored contents)
│
└── logs/                              # Application logs (gitignored contents)
```
