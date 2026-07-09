"""Tests for GlobalNewsAgent's multi-publisher RSS collection and optional
NewsAPI supplement.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from app.agents.global_news_agent import GlobalNewsAgent
from app.config.sources import GLOBAL_NEWS_RSS_FEEDS, NEWSAPI_EVERYTHING_URL
from app.models.article import NewsCategory

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
SAMPLE_RSS = (FIXTURES_DIR / "sample_rss.xml").read_text(encoding="utf-8")

EMPTY_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Empty Feed</title>
    <link>https://example.com</link>
    <description>No items</description>
  </channel>
</rss>
"""

# GLOBAL_NEWS_RSS_FEEDS already stores fully-built URLs (direct publisher
# feeds for some sources, Google News query URLs for others), so we can
# route respx directly against its values.
GLOBAL_URLS: dict[str, str] = GLOBAL_NEWS_RSS_FEEDS


def _newsapi_payload() -> dict:
    return {
        "articles": [
            {
                "title": "NewsAPI global story one",
                "url": "https://example.com/newsapi/1",
                "description": "First supplemental global story.",
                "author": "Reporter One",
                "publishedAt": "2024-03-01T08:00:00Z",
            },
            {
                "title": "NewsAPI global story two",
                "url": "https://example.com/newsapi/2",
                "description": "Second supplemental global story.",
                "author": "Reporter Two",
                "publishedAt": "2024-03-02T08:00:00Z",
            },
        ]
    }


@pytest.mark.asyncio
async def test_fetch_aggregates_every_source_and_tags_articles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NEWSAPI_API_KEY", raising=False)

    with respx.mock:
        for url in GLOBAL_URLS.values():
            respx.get(url).mock(return_value=httpx.Response(200, text=SAMPLE_RSS))

        articles = await GlobalNewsAgent().fetch()

    assert len(articles) == len(GLOBAL_NEWS_RSS_FEEDS) * 2

    articles_by_source: dict[str, list] = {}
    for article in articles:
        articles_by_source.setdefault(article.source, []).append(article)

    assert set(articles_by_source) == set(GLOBAL_NEWS_RSS_FEEDS)
    for source, source_articles in articles_by_source.items():
        assert len(source_articles) == 2
        for article in source_articles:
            assert article.source == source
            assert article.category == NewsCategory.GLOBAL
            assert article.title
            assert article.url
            assert article.published_at is not None

    # Spot-check that entry fields from the RSS fixture flow through onto
    # the Article correctly for at least one source.
    techcrunch_articles = articles_by_source["TechCrunch AI"]
    titles = {a.title for a in techcrunch_articles}
    assert "OpenAI unveils major new model" in titles
    assert "Anthropic raises new funding round" in titles
    first = next(a for a in techcrunch_articles if a.title == "OpenAI unveils major new model")
    assert first.url == "https://example.com/articles/1"
    assert first.author == "jane@example.com"
    assert "major" in first.snippet


@pytest.mark.asyncio
async def test_fetch_one_source_failure_does_not_drop_others(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NEWSAPI_API_KEY", raising=False)
    # Avoid slow exponential-backoff retries against the failing feed.
    monkeypatch.setenv("HTTP_MAX_RETRIES", "1")
    failing_source = "VentureBeat AI"

    with respx.mock:
        for source, url in GLOBAL_URLS.items():
            if source == failing_source:
                respx.get(url).mock(return_value=httpx.Response(500))
            else:
                respx.get(url).mock(return_value=httpx.Response(200, text=SAMPLE_RSS))

        articles = await GlobalNewsAgent().fetch()

    sources_present = {article.source for article in articles}
    assert failing_source not in sources_present
    assert sources_present == set(GLOBAL_NEWS_RSS_FEEDS) - {failing_source}
    assert len(articles) == (len(GLOBAL_NEWS_RSS_FEEDS) - 1) * 2


@pytest.mark.asyncio
async def test_fetch_returns_empty_list_when_all_feeds_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NEWSAPI_API_KEY", raising=False)

    with respx.mock:
        for url in GLOBAL_URLS.values():
            respx.get(url).mock(return_value=httpx.Response(200, text=EMPTY_RSS))

        articles = await GlobalNewsAgent().fetch()

    assert articles == []


@pytest.mark.asyncio
async def test_fetch_without_newsapi_key_skips_supplement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NEWSAPI_API_KEY", raising=False)

    with respx.mock:
        for url in GLOBAL_URLS.values():
            respx.get(url).mock(return_value=httpx.Response(200, text=SAMPLE_RSS))
        newsapi_route = respx.get(NEWSAPI_EVERYTHING_URL).mock(
            return_value=httpx.Response(200, json=_newsapi_payload())
        )

        articles = await GlobalNewsAgent().fetch()

    assert newsapi_route.call_count == 0
    assert len(articles) == len(GLOBAL_NEWS_RSS_FEEDS) * 2
    assert all(article.source != "NewsAPI" for article in articles)


@pytest.mark.asyncio
async def test_fetch_with_newsapi_key_appends_supplemental_articles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NEWSAPI_API_KEY", "test-newsapi-key")

    with respx.mock:
        for url in GLOBAL_URLS.values():
            respx.get(url).mock(return_value=httpx.Response(200, text=SAMPLE_RSS))
        newsapi_route = respx.get(NEWSAPI_EVERYTHING_URL).mock(
            return_value=httpx.Response(200, json=_newsapi_payload())
        )

        articles = await GlobalNewsAgent().fetch()

    assert newsapi_route.call_count == 1

    organic = [a for a in articles if a.source != "NewsAPI"]
    supplemental = [a for a in articles if a.source == "NewsAPI"]

    assert len(organic) == len(GLOBAL_NEWS_RSS_FEEDS) * 2
    assert len(supplemental) == 2

    for article in supplemental:
        assert article.category == NewsCategory.GLOBAL
        assert article.title in {
            "NewsAPI global story one",
            "NewsAPI global story two",
        }
