"""FastAPI application entrypoint for AI Newsletter Automation."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.config.logging_config import configure_logging, get_logger
from app.config.settings import get_settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("application_startup", app_env=settings.app_env, llm_mock=settings.uses_mock_llm)
    yield
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Newsletter Automation",
        description=(
            "Enterprise multi-agent AI newsletter pipeline: LangGraph orchestration, "
            "GPT summarization, semantic deduplication, and multi-dimensional ranking, "
            "exposed over a FastAPI backend for Microsoft Power Automate / Outlook delivery."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )
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
