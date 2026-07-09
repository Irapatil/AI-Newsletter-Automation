"""Tests for PolicyAgent's per-topic Google News RSS collection and optional
NewsAPI supplement.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from app.agents.policy_agent import PolicyAgent
from app.config.sources import NEWSAPI_EVERYTHING_URL, POLICY_QUERIES, google_news_query_url
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

# PolicyAgent scopes its Google News queries to a 7-day recency window
# (unlike the 2-day default used elsewhere), so URLs must be built the same
# way here to match respx's exact-URL routes.
POLICY_URLS: dict[str, str] = {
    topic: google_news_query_url(query, when="7d") for topic, query in POLICY_QUERIES.items()
}


def _newsapi_payload() -> dict:
    return {
        "articles": [
            {
                "title": "NewsAPI policy story one",
                "url": "https://example.com/newsapi/1",
                "description": "First supplemental policy story.",
                "author": "Reporter One",
                "publishedAt": "2024-03-01T08:00:00Z",
            },
            {
                "title": "NewsAPI policy story two",
                "url": "https://example.com/newsapi/2",
                "description": "Second supplemental policy story.",
                "author": "Reporter Two",
                "publishedAt": "2024-03-02T08:00:00Z",
            },
        ]
    }


@pytest.mark.asyncio
async def test_fetch_queries_every_topic_and_tags_articles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NEWSAPI_API_KEY", raising=False)

    with respx.mock:
        for url in POLICY_URLS.values():
            respx.get(url).mock(return_value=httpx.Response(200, text=SAMPLE_RSS))

        articles = await PolicyAgent().fetch()

    assert len(articles) == len(POLICY_QUERIES) * 2

    articles_by_topic: dict[str, list] = {}
    for article in articles:
        articles_by_topic.setdefault(article.metadata["topic"], []).append(article)

    assert set(articles_by_topic) == set(POLICY_QUERIES)
    for topic, topic_articles in articles_by_topic.items():
        assert len(topic_articles) == 2
        for article in topic_articles:
            assert article.source == f"Policy: {topic}"
            assert article.category == NewsCategory.POLICY
            assert article.metadata == {"topic": topic}


@pytest.mark.asyncio
async def test_fetch_one_topic_failure_does_not_drop_others(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NEWSAPI_API_KEY", raising=False)
    # Avoid slow exponential-backoff retries against the failing feed.
    monkeypatch.setenv("HTTP_MAX_RETRIES", "1")
    failing_topic = "EU AI Act"

    with respx.mock:
        for topic, url in POLICY_URLS.items():
            if topic == failing_topic:
                respx.get(url).mock(return_value=httpx.Response(500))
            else:
                respx.get(url).mock(return_value=httpx.Response(200, text=SAMPLE_RSS))

        articles = await PolicyAgent().fetch()

    topics_present = {article.metadata["topic"] for article in articles}
    assert failing_topic not in topics_present
    assert topics_present == set(POLICY_QUERIES) - {failing_topic}
    assert len(articles) == (len(POLICY_QUERIES) - 1) * 2


@pytest.mark.asyncio
async def test_fetch_returns_empty_list_when_all_feeds_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NEWSAPI_API_KEY", raising=False)

    with respx.mock:
        for url in POLICY_URLS.values():
            respx.get(url).mock(return_value=httpx.Response(200, text=EMPTY_RSS))

        articles = await PolicyAgent().fetch()

    assert articles == []


@pytest.mark.asyncio
async def test_fetch_without_newsapi_key_skips_supplement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NEWSAPI_API_KEY", raising=False)

    with respx.mock:
        for url in POLICY_URLS.values():
            respx.get(url).mock(return_value=httpx.Response(200, text=SAMPLE_RSS))
        newsapi_route = respx.get(NEWSAPI_EVERYTHING_URL).mock(
            return_value=httpx.Response(200, json=_newsapi_payload())
        )

        articles = await PolicyAgent().fetch()

    assert newsapi_route.call_count == 0
    assert len(articles) == len(POLICY_QUERIES) * 2
    assert all("(NewsAPI)" not in article.source for article in articles)


@pytest.mark.asyncio
async def test_fetch_with_newsapi_key_appends_supplemental_articles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NEWSAPI_API_KEY", "test-newsapi-key")

    with respx.mock:
        for url in POLICY_URLS.values():
            respx.get(url).mock(return_value=httpx.Response(200, text=SAMPLE_RSS))
        newsapi_route = respx.get(NEWSAPI_EVERYTHING_URL).mock(
            return_value=httpx.Response(200, json=_newsapi_payload())
        )

        articles = await PolicyAgent().fetch()

    assert newsapi_route.call_count == len(POLICY_QUERIES)

    organic = [a for a in articles if "(NewsAPI)" not in a.source]
    supplemental = [a for a in articles if "(NewsAPI)" in a.source]

    assert len(organic) == len(POLICY_QUERIES) * 2
    assert len(supplemental) == len(POLICY_QUERIES) * 2

    supplemental_by_topic: dict[str, list] = {}
    for article in supplemental:
        supplemental_by_topic.setdefault(article.metadata["topic"], []).append(article)

    assert set(supplemental_by_topic) == set(POLICY_QUERIES)
    for topic, topic_articles in supplemental_by_topic.items():
        assert len(topic_articles) == 2
        for article in topic_articles:
            assert article.source == f"Policy: {topic} (NewsAPI)"
            assert article.category == NewsCategory.POLICY
            assert article.metadata == {"topic": topic}
            assert article.title in {
                "NewsAPI policy story one",
                "NewsAPI policy story two",
            }
