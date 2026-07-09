"""Shared pytest fixtures for the AI Newsletter Automation test suite."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.config.settings import Settings, get_settings
from app.models.article import Article, NewsCategory
from app.services.llm_service import MockLLMService


@pytest.fixture(autouse=True)
def _reset_settings_cache(monkeypatch: pytest.MonkeyPatch):
    """Ensure `get_settings()` reflects env vars set/unset within a test.

    Also disables loading a real `.env` file for the duration of the test
    suite: `Settings` reads `env_file=".env"` on construction regardless of
    `monkeypatch.setenv`/`delenv`, so a developer's real `.env` (with real
    API keys) would otherwise leak into tests that expect a key to be unset,
    making the suite depend on local machine state instead of being hermetic.
    """
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def mock_llm_service() -> MockLLMService:
    return MockLLMService()


@pytest.fixture
def now() -> datetime:
    return datetime.now(UTC)


def make_article(
    *,
    title: str = "Sample AI Article",
    url: str = "https://example.com/article",
    source: str = "TechCrunch AI",
    category: NewsCategory = NewsCategory.GLOBAL,
    published_at: datetime | None = None,
    snippet: str = "A sample snippet about artificial intelligence.",
    **kwargs,
) -> Article:
    return Article(
        title=title,
        url=url,
        source=source,
        category=category,
        published_at=published_at or datetime.now(UTC),
        snippet=snippet,
        **kwargs,
    )


@pytest.fixture
def article_factory():
    return make_article


@pytest.fixture
def sample_articles(now: datetime) -> list[Article]:
    return [
        make_article(
            title="OpenAI announces breakthrough model",
            url="https://a.com/1",
            source="TechCrunch AI",
            category=NewsCategory.GLOBAL,
            published_at=now,
            snippet="OpenAI unveils a major new AI model breakthrough.",
        ),
        make_article(
            title="OpenAI announces breakthrough model release",
            url="https://a.com/1-duplicate",
            source="VentureBeat AI",
            category=NewsCategory.GLOBAL,
            published_at=now - timedelta(hours=1),
            snippet="OpenAI unveils a major new AI model breakthrough today.",
        ),
        make_article(
            title="Novel benchmark dataset for LLM reasoning",
            url="https://arxiv.org/abs/1",
            source="arXiv",
            category=NewsCategory.RESEARCH,
            published_at=now - timedelta(hours=5),
            snippet="A state-of-the-art benchmark dataset.",
        ),
    ]
