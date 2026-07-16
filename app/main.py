"""FastAPI application entrypoint for AI Newsletter Automation."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config.logging_config import configure_logging, get_logger
from app.config.settings import get_settings

logger = get_logger(__name__)

REPO_URL = "https://github.com/Irapatil/AI-Newsletter-Automation"

OPENAPI_TAGS = [
    {
        "name": "System",
        "description": "Service identity and metadata. Always public.",
    },
    {
        "name": "Health",
        "description": "Liveness probe plus a call-free, per-integration configuration "
        "summary (OpenAI, NewsAPI, GitHub, RSS, LangGraph). Always public.",
    },
    {
        "name": "Newsletter",
        "description": "The production pipeline: trigger a run, and read the latest/"
        "historical output. This is the contract Microsoft Power Automate's daily "
        "flow calls (see docs/POWER_AUTOMATE.md).",
    },
    {
        "name": "Demo",
        "description": "A Swagger-friendly companion endpoint for live "
        "walkthroughs - same LangGraph pipeline, a smaller response payload.",
    },
    {
        "name": "Integration",
        "description": "Real Outlook delivery status: Power Automate reports the outcome "
        "of its 'Send an email (V2)' action here, and the frontend polls it - "
        "no mocked or simulated delivery state (see docs/POWER_AUTOMATE.md).",
    },
]

APP_DESCRIPTION = f"""\
Enterprise multi-agent AI newsletter pipeline: **LangGraph** orchestration, \
**GPT** summarization, semantic deduplication, and multi-dimensional ranking, \
exposed over a **FastAPI** backend for Microsoft Power Automate / Outlook \
delivery.

**Demo flow:** `POST /demo/generate` -> `GET /newsletter/latest/html` \
(see [DEMO.md]({REPO_URL}/blob/main/DEMO.md) for the full interview walkthrough).

## LangGraph workflow

A single compiled `StateGraph` fans out to eight collector agents in \
parallel, fans back in, and flows through four sequential stages before \
the response is returned:

```
Orchestrator
  |-- fan-out (parallel) --> 8 collector agents --> fan-in
                                                        |
                                                        v
                                                 AggregatorAgent
                                                        |
                                                        v
                                    DeduplicationAgent (embedding cosine similarity)
                                                        |
                                                        v
                                    RankingAgent (6-dimension weighted score)
                                     /                                    \\
                          articles found                       nothing cleared the bar
                              |                                              |
                              v                                              v
              NewsletterGeneratorAgent (GPT)                       NoContentFallback
                              \\                                            /
                               `------------> HTMLFormatterAgent <---------'
                                                     |
                                                     v
                                    HTML + Markdown + JSON response
```

Every node is wrapped with a stopwatch and reports one `AgentExecutionRecord` \
(node, status, execution time, items processed) in the `agent_execution` \
field of every `POST /generate-newsletter` / `POST /demo/generate` response - \
a node-by-node execution report for each run, with zero effect on routing, \
retries, or agent logic. Full write-up: \
[docs/ARCHITECTURE.md]({REPO_URL}/blob/main/docs/ARCHITECTURE.md).

## Agents

| Agent | Responsibility |
|---|---|
| **GlobalNewsAgent** | Publisher RSS (TechCrunch, VentureBeat, MIT Tech Review, The Verge, Reuters via Google News) + NewsAPI |
| **CompanyAgent** | Per-company Google News RSS (OpenAI, Anthropic, Microsoft AI, DeepMind, Meta AI, NVIDIA, Amazon AI, xAI) |
| **ResearchAgent** | arXiv API (`cs.AI`, `cs.LG`, `cs.CL`) |
| **FundingAgent** | Crunchbase API (if key present), Google News fallback otherwise |
| **TalentAgent** | Greenhouse + Lever public job boards, LinkedIn provider (mock/api) |
| **PolicyAgent** | Google News RSS + NewsAPI (EU AI Act, India AI Mission, US AI Executive Orders) |
| **OpenSourceAgent** | GitHub Search API (trending) + Hugging Face Hub API |
| **ModelReleaseAgent** | Google News RSS per lab, new model-release announcements |
| **AggregatorAgent** | Fan-in: merges all eight collector outputs into one article list |
| **DeduplicationAgent** | Embedding cosine-similarity dedup; freshest copy of a story wins |
| **RankingAgent** | 6-dimension weighted scoring (freshness, importance, business impact, source credibility, research impact, AI relevance); keeps the top-N per section |
| **NewsletterGeneratorAgent** | GPT per-article summaries, executive summary, subject line, "one thing to watch" |
| **HTMLFormatterAgent** | Renders the final Jinja2 HTML, Markdown, and JSON payloads |

*(`AggregatorAgent` through `HTMLFormatterAgent` are the four sequential \
stages that run after the eight collectors fan in - included here for a \
complete, accurate picture of every node in the graph.)*
"""


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level, settings.app_env)
    logger.info("application_startup", app_env=settings.app_env, llm_mock=settings.uses_mock_llm)
    yield
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    is_production = settings.app_env == "production"

    app = FastAPI(
        title="AI Newsletter Automation",
        summary="Enterprise multi-agent AI newsletter automation, orchestrated with LangGraph.",
        description=APP_DESCRIPTION,
        version="1.0.0",
        contact={
            "name": "AI Newsletter Automation - Engineering",
            "url": REPO_URL,
        },
        license_info={
            "name": "MIT",
            "url": f"{REPO_URL}/blob/main/LICENSE",
        },
        lifespan=lifespan,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
        openapi_tags=OPENAPI_TAGS,
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def _handle_unhandled_exception(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", error=str(exc))
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.include_router(router)

    def _custom_openapi() -> dict[str, object]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            summary=app.summary,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
            contact=app.contact,
            license_info=app.license_info,
        )
        schema["externalDocs"] = {
            "description": "Full documentation: architecture, agent responsibilities, "
            "Power Automate integration guide, and the interview demo walkthrough.",
            "url": f"{REPO_URL}#readme",
        }
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = _custom_openapi  # type: ignore[method-assign]
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )
