# AI Newsletter Automation

Enterprise multi-agent AI newsletter platform built with **LangGraph**,
**FastAPI**, and **OpenAI/Azure OpenAI**, delivered daily through
**Microsoft Power Automate** and **Outlook**. It automatically discovers,
categorizes, deduplicates, ranks, summarizes, and formats AI industry news
into an executive-ready newsletter — with zero manual steps.

**This is a backend engineering showcase.** The entire demonstration runs
through FastAPI's Swagger UI - no frontend, no build step. See
[`DEMO.md`](DEMO.md) for the full interview walkthrough.

[![CI](https://github.com/Irapatil/AI-Newsletter-Automation/actions/workflows/ci.yml/badge.svg)](https://github.com/Irapatil/AI-Newsletter-Automation/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-1c3d5a.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Table of Contents

- [Problem Statement](#problem-statement)
- [Solution](#solution)
- [Architecture](#architecture)
- [LangGraph Workflow](#langgraph-workflow)
- [Technology Stack](#technology-stack)
- [Folder Structure](#folder-structure)
- [Running Locally](#running-locally)
- [Environment Variables](#environment-variables)
- [FastAPI APIs](#fastapi-apis)
- [Swagger](#swagger)
- [Power Automate Integration](#power-automate-integration)
- [Outlook Integration](#outlook-integration)
- [Docker](#docker)
- [Testing & Code Quality](#testing--code-quality)
- [Documentation](#documentation)
- [Future Enhancements](#future-enhancements)
- [Screenshots](#screenshots)
- [License](#license)

## Problem Statement

Staying current on AI industry news — model releases, funding, research,
hiring trends, open-source activity, and regulation — is a full-time job in
itself. Manually curating a daily executive digest from a dozen+ scattered
sources doesn't scale, is inconsistent, and is the kind of repetitive
knowledge-work task that's a natural fit for automation.

## Solution

A LangGraph-orchestrated pipeline runs on a schedule (triggered by Power
Automate), fans out to **eight parallel collector agents** across global
news, company moves, funding, talent, research, open source, policy, and
model releases, then:

1. **Aggregates** everything into one list.
2. **Deduplicates** semantically (embedding cosine similarity) — the same
   story covered by five publishers becomes one entry.
3. **Ranks** every remaining story across six weighted dimensions
   (freshness, importance, business impact, source credibility, research
   impact, AI relevance).
4. **Summarizes** the top stories with GPT into a tight executive voice.
5. **Renders** the result as HTML, Markdown, and JSON.
6. **Serves** it over a FastAPI endpoint that Power Automate calls daily and
   pipes straight into an Outlook "Send an email" action.

Every response also carries a **full LangGraph execution report** - one
entry per node with its status, timing, and items processed - plus
pipeline statistics, sources used, and an estimated token/cost figure. See
[`DEMO.md`](DEMO.md) for what this looks like in practice.

Every external dependency (LLM, news APIs, job boards, funding data) has a
mock or free fallback, so the entire pipeline runs and is fully testable
**before you add a single API key**.

## Architecture

```mermaid
flowchart LR
    PA[Power Automate<br/>Daily Trigger] -->|HTTP POST| API[FastAPI]
    API --> WF[LangGraph Workflow]
    WF -->|8 parallel collectors| AGG[Aggregator]
    AGG --> DEDUP[Deduplication<br/>embeddings]
    DEDUP --> RANK[Ranking<br/>6 dimensions]
    RANK --> GEN[Newsletter Generator<br/>GPT summaries]
    GEN --> FMT[HTML Formatter]
    FMT --> API
    API -->|JSON: newsletter_html/markdown/json + execution report| PA
    PA --> OUTLOOK[Outlook: Send Email]
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full agent graph,
sequence diagram, and a breakdown of the ranking/deduplication algorithms —
and why this is built on LangGraph rather than a conversational-agent
framework like AutoGen.

## LangGraph Workflow

```
START → Orchestrator → [8 parallel collector agents] → Aggregator
      → Semantic Deduplication → Ranking
      → (conditional) Newsletter Generator | NoContentFallback
      → HTML Formatter → END
```

Every node is instrumented with a stopwatch that reports its `status`,
`execution_time_seconds`, and `items_processed` - surfaced directly in the
API response as `agent_execution` (see [`docs/API.md`](docs/API.md) and
[`DEMO.md`](DEMO.md)). This is pure observability added around each agent's
existing call; no routing, retry behavior, or agent logic changed to add it.

## Technology Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph (`StateGraph`, parallel fan-out/fan-in, conditional edges, retry policies) |
| LLM | OpenAI / Azure OpenAI via LangChain, with a deterministic offline mock provider |
| API | FastAPI + Pydantic v2, fully documented OpenAPI/Swagger schema |
| News collection | `feedparser` (RSS/Atom), `httpx` (async HTTP), `BeautifulSoup4` |
| Sources | Google News RSS, arXiv API, GitHub Search API, Hugging Face Hub API, Greenhouse/Lever job board APIs, NewsAPI.org, Crunchbase API v4 |
| Rendering | Jinja2 (HTML email template), custom Markdown builder |
| Config | `pydantic-settings`, `.env` |
| Logging | `structlog` (structured JSON logs) |
| Testing | `pytest`, `pytest-asyncio`, `respx` (HTTP mocking), `pytest-cov` |
| Quality | `black`, `ruff`, `isort`, `mypy` |
| Packaging | Docker, docker-compose, Makefile |

## Folder Structure

```
app/
├── api/          FastAPI routes + auth dependency
├── agents/       13 agents: 8 collectors + aggregator/dedup/ranking/newsletter/formatter
├── graph/        LangGraph StateGraph construction (workflow.py, nodes.py)
├── services/     External integrations (LLM, RSS, arXiv, GitHub, HF, job boards, funding, history)
├── models/       Pydantic domain models + GraphState
├── config/       Settings, source registry, logging config
├── utils/        Retry decorator, text/embedding helpers
└── templates/    Jinja2 HTML email template
```

Full breakdown: [`docs/FOLDER_STRUCTURE.md`](docs/FOLDER_STRUCTURE.md).

## Running Locally

```bash
git clone https://github.com/Irapatil/AI-Newsletter-Automation.git
cd AI-Newsletter-Automation

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements-dev.txt
cp .env.example .env
```

Run it immediately — no API keys required (mock LLM + free/fallback sources):

```bash
uvicorn app.main:app --reload
# -> http://localhost:8000/docs
```

(or `make dev`, equivalent). Then follow the [5-minute demo in `DEMO.md`](DEMO.md).

Prefer not to stand up the API at all? Run the pipeline directly:

```bash
python scripts/generate_newsletter_cli.py --output-dir newsletter_output
```

## Environment Variables

All configuration is via environment variables (`.env`). Every field has a
safe default; see [`docs/ENVIRONMENT_VARIABLES.md`](docs/ENVIRONMENT_VARIABLES.md)
for the full reference. The highlights:

```bash
# Enable real GPT summaries + embeddings
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Protect the API (required in production)
API_AUTH_TOKEN=$(openssl rand -hex 32)

# Optional: raise GitHub rate limits, enable NewsAPI/Crunchbase supplements
GITHUB_TOKEN=
NEWSAPI_API_KEY=
CRUNCHBASE_API_KEY=
```

## FastAPI APIs

| Endpoint | Tag | Purpose |
|---|---|---|
| `GET /` | System | Service identity |
| `GET /health` | Health | Liveness + per-integration config status |
| `POST /generate-newsletter` | Newsletter | Run the full pipeline (Power Automate's integration point) |
| `GET /newsletter/latest` | Newsletter | Re-read the latest edition as JSON |
| `GET /newsletter/latest/html` | Newsletter | **Open in a browser** for the rendered HTML newsletter |
| `GET /newsletter/history` | Newsletter | List past editions (metadata only) |
| `POST /demo/generate` | Demo | Same pipeline, compact response - built for live walkthroughs |

```bash
# Trigger a full pipeline run
curl -X POST http://localhost:8000/generate-newsletter \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_AUTH_TOKEN" \
  -d '{}'

# Compact demo response + link to the rendered HTML
curl -X POST http://localhost:8000/demo/generate -H "X-API-Key: $API_AUTH_TOKEN"

# Open the rendered newsletter directly
open http://localhost:8000/newsletter/latest/html
```

Full endpoint reference (every field explained, realistic examples,
error codes): [`docs/API.md`](docs/API.md).

## Swagger

Interactive docs are served at `/docs` (Swagger UI) and `/redoc` in
`development`/`staging` (disabled in `production`). Every request/response
model carries a realistic, populated example - visible in Swagger's
"Example Value" tab without needing to execute a request first. Endpoints
are grouped into four tags: **System**, **Health**, **Newsletter**, **Demo**.
This is the primary demo surface for this project - see
[`DEMO.md`](DEMO.md) for the full walkthrough.

## Power Automate Integration

```
Daily Trigger (Recurrence) → HTTP (POST /generate-newsletter) → Parse JSON
      → Compose (HTML) → Outlook: Send an email (V2) → (optional) SharePoint archive
```

Full step-by-step flow setup, with the exact JSON schema for the Parse JSON
step and screenshot placeholders for each action:
[`docs/POWER_AUTOMATE.md`](docs/POWER_AUTOMATE.md).

## Outlook Integration

The Power Automate flow's final step is Outlook's **Send an email (V2)**
action, fed directly from `newsletter_html` (no transformation needed - it's
already a complete, professionally-styled HTML document with inline CSS
for email-client compatibility). If you don't have a live Power Automate
environment handy, `GET /newsletter/latest/html` in a browser renders the
identical HTML Outlook would send.

## Docker

```bash
cp .env.example .env
make docker-build
make docker-up
make docker-logs
```

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for cloud deployment patterns
(Azure Container Apps, ECS, Kubernetes) and secrets guidance.

## Testing & Code Quality

```bash
make test        # pytest, 146 tests (including an end-to-end LangGraph run), all external calls mocked (respx / MockLLMService)
make lint         # ruff + isort --check + black --check
make format       # ruff --fix + isort + black
make typecheck    # mypy
make check        # lint + typecheck + test
```

No network access or API keys are required to run the test suite — outbound
HTTP is mocked with `respx`, and the LLM defaults to `MockLLMService`.
[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs the same `make check`
steps on every push and pull request to `main`.

## Documentation

| Doc | Contents |
|---|---|
| [`DEMO.md`](DEMO.md) | **Start here** - the full interview demo walkthrough |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Agent graph, sequence diagram, dedup/ranking algorithms |
| [`docs/API.md`](docs/API.md) | Endpoint reference, auth, error codes, every response field explained |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Local, Docker, and cloud deployment |
| [`docs/POWER_AUTOMATE.md`](docs/POWER_AUTOMATE.md) | Step-by-step Power Automate flow + exact Parse JSON schema |
| [`docs/ENVIRONMENT_VARIABLES.md`](docs/ENVIRONMENT_VARIABLES.md) | Full env var reference |
| [`docs/FOLDER_STRUCTURE.md`](docs/FOLDER_STRUCTURE.md) | Full repository layout |
| [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) | Common issues and fixes |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Planned enhancements |

## Future Enhancements

Per-recipient personalization, LangGraph checkpointing for resumable runs,
a real LinkedIn Talent API integration, database-backed history for
multi-instance deployments, real (non-heuristic) token/cost accounting via
provider usage APIs, and multi-language newsletters. Full list:
[`docs/ROADMAP.md`](docs/ROADMAP.md).

## Screenshots

> `docs/images/newsletter-html-preview.png` — *(placeholder: rendered HTML newsletter)*
>
> `docs/images/swagger-ui.png` — *(placeholder: FastAPI `/docs` Swagger UI, showing `POST /demo/generate`'s example response)*
>
> `docs/images/power-automate-flow-overview.png` — *(placeholder: end-to-end Power Automate flow canvas)*

## License

[MIT](LICENSE) © 2026 Irapatil

---

<details>
<summary><strong>Appendix: optional React frontend (not part of the interview demo)</strong></summary>

An earlier iteration of this project also includes a React/TypeScript
dashboard in [`frontend/`](frontend/). It is **not required or used** for
the demo described above - the demo is Swagger-only by design - but is left
in the repository as a secondary artifact. It has not been updated for the
`agent_execution`/`statistics`/`provider`/`token_usage` response fields
added since it was built, so treat it as unmaintained if you choose to run
it. See [`frontend/README.md`](frontend/README.md) for its own setup
instructions.

</details>
