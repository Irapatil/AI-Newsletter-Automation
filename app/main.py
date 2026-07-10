"""FastAPI application entrypoint for AI Newsletter Automation."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config.logging_config import configure_logging, get_logger
from app.config.settings import get_settings

logger = get_logger(__name__)

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
        "description": "A Swagger-friendly companion endpoint for live interview "
        "walkthroughs - same LangGraph pipeline, a smaller response payload.",
    },
]


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
        description=(
            "Enterprise multi-agent AI newsletter pipeline: LangGraph orchestration, "
            "GPT summarization, semantic deduplication, and multi-dimensional ranking, "
            "exposed over a FastAPI backend for Microsoft Power Automate / Outlook delivery.\n\n"
            "**Demo flow:** `POST /demo/generate` -> `GET /newsletter/latest/html` "
            "(see DEMO.md for the full interview walkthrough)."
        ),
        version="1.0.0",
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
