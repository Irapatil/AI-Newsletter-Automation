"""Tests for BaseCollectorAgent's exception isolation and freshness filtering."""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.agents.base_agent import BaseCollectorAgent
from app.models.article import Article, NewsCategory
from tests.conftest import make_article


class _FailingAgent(BaseCollectorAgent):
    category = NewsCategory.GLOBAL
    state_key = "global_news"
    display_name = "FailingAgent"

    async def fetch(self) -> list[Article]:
        raise RuntimeError("simulated network failure")


class _WorkingAgent(BaseCollectorAgent):
    category = NewsCategory.GLOBAL
    state_key = "global_news"
    display_name = "WorkingAgent"

    def __init__(self, articles: list[Article]) -> None:
        self._articles = articles

    async def fetch(self) -> list[Article]:
        return self._articles


@pytest.mark.asyncio
async def test_collect_isolates_exceptions():
    result = await _FailingAgent().collect()
    assert result.articles == []
    assert result.logs == []
    assert len(result.errors) == 1
    assert "simulated network failure" in result.errors[0]


@pytest.mark.asyncio
async def test_collect_filters_stale_articles(now, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MAX_ARTICLE_AGE_HOURS", "24")
    articles = [
        make_article(title="Fresh", published_at=now),
        make_article(title="Stale", published_at=now - timedelta(hours=48)),
    ]
    result = await _WorkingAgent(articles).collect()

    assert [a.title for a in result.articles] == ["Fresh"]
    assert result.errors == []
    assert "1 fresh" in result.logs[0] or "collected 1" in result.logs[0]
