"""Tests for the ResearchAgent, a thin wrapper around the arXiv service."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.agents.research_agent import ResearchAgent
from app.models.article import NewsCategory
from app.services.arxiv_service import ArxivPaper


def _make_paper(**overrides) -> ArxivPaper:
    paper: ArxivPaper = {
        "title": "Attention Is All You Need, Again",
        "url": "https://arxiv.org/abs/9999.99999",
        "snippet": "We revisit the transformer architecture and propose a new variant.",
        "published_at": datetime(2026, 7, 8, tzinfo=UTC),
        "author": "Jane Researcher",
        "categories": ["cs.CL", "cs.LG"],
    }
    paper.update(overrides)
    return paper


@pytest.mark.asyncio
async def test_fetch_maps_arxiv_papers_to_articles(monkeypatch: pytest.MonkeyPatch):
    papers = [
        _make_paper(),
        _make_paper(
            title="Scaling Laws for Everything",
            url="https://arxiv.org/abs/8888.88888",
            snippet="An empirical study of scaling behavior.",
            published_at=datetime(2026, 7, 7, tzinfo=UTC),
            author=None,
            categories=["cs.AI"],
        ),
    ]

    async def fake_fetch_recent_papers(max_results: int = 25):
        assert max_results == 25
        return papers

    monkeypatch.setattr("app.agents.research_agent.fetch_recent_papers", fake_fetch_recent_papers)

    articles = await ResearchAgent().fetch()

    assert len(articles) == 2

    first = articles[0]
    assert first.title == "Attention Is All You Need, Again"
    assert first.url == "https://arxiv.org/abs/9999.99999"
    assert first.source == "arXiv"
    assert first.category == NewsCategory.RESEARCH
    assert first.published_at == datetime(2026, 7, 8, tzinfo=UTC)
    assert first.snippet == "We revisit the transformer architecture and propose a new variant."
    assert first.author == "Jane Researcher"
    assert first.metadata == {"categories": ["cs.CL", "cs.LG"]}

    second = articles[1]
    assert second.title == "Scaling Laws for Everything"
    assert second.author is None
    assert second.metadata == {"categories": ["cs.AI"]}


@pytest.mark.asyncio
async def test_fetch_returns_empty_list_when_arxiv_service_returns_nothing(
    monkeypatch: pytest.MonkeyPatch,
):
    async def fake_fetch_recent_papers(max_results: int = 25):
        return []

    monkeypatch.setattr("app.agents.research_agent.fetch_recent_papers", fake_fetch_recent_papers)

    articles = await ResearchAgent().fetch()

    assert articles == []


@pytest.mark.asyncio
async def test_fetch_skips_papers_without_a_url(monkeypatch: pytest.MonkeyPatch):
    papers = [_make_paper(url=""), _make_paper(title="Has A URL")]

    async def fake_fetch_recent_papers(max_results: int = 25):
        return papers

    monkeypatch.setattr("app.agents.research_agent.fetch_recent_papers", fake_fetch_recent_papers)

    articles = await ResearchAgent().fetch()

    assert len(articles) == 1
    assert articles[0].title == "Has A URL"
