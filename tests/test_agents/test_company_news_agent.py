"""Tests for CompanyNewsAgent's per-company Google News RSS collection."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from app.agents.company_news_agent import CompanyNewsAgent
from app.config.sources import COMPANY_NEWS_QUERIES, google_news_query_url
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

COMPANY_URLS: dict[str, str] = {
    company: google_news_query_url(query) for company, query in COMPANY_NEWS_QUERIES.items()
}


@pytest.mark.asyncio
async def test_fetch_queries_every_company_and_tags_articles() -> None:
    with respx.mock:
        for url in COMPANY_URLS.values():
            respx.get(url).mock(return_value=httpx.Response(200, text=SAMPLE_RSS))

        articles = await CompanyNewsAgent().fetch()

    assert len(articles) == len(COMPANY_NEWS_QUERIES) * 2

    articles_by_company: dict[str, list] = {}
    for article in articles:
        articles_by_company.setdefault(article.metadata["company"], []).append(article)

    assert set(articles_by_company) == set(COMPANY_NEWS_QUERIES)
    for company, company_articles in articles_by_company.items():
        assert len(company_articles) == 2
        for article in company_articles:
            assert article.source == f"{company} (Google News)"
            assert article.category == NewsCategory.COMPANY
            assert article.metadata == {"company": company}


@pytest.mark.asyncio
async def test_fetch_one_company_failure_does_not_drop_others(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Avoid slow exponential-backoff retries against the failing feed.
    monkeypatch.setenv("HTTP_MAX_RETRIES", "1")
    failing_company = "Anthropic"

    with respx.mock:
        for company, url in COMPANY_URLS.items():
            if company == failing_company:
                respx.get(url).mock(return_value=httpx.Response(500))
            else:
                respx.get(url).mock(return_value=httpx.Response(200, text=SAMPLE_RSS))

        articles = await CompanyNewsAgent().fetch()

    companies_present = {article.metadata["company"] for article in articles}
    assert failing_company not in companies_present
    assert companies_present == set(COMPANY_NEWS_QUERIES) - {failing_company}
    assert len(articles) == (len(COMPANY_NEWS_QUERIES) - 1) * 2


@pytest.mark.asyncio
async def test_fetch_returns_empty_list_when_all_feeds_empty() -> None:
    with respx.mock:
        for url in COMPANY_URLS.values():
            respx.get(url).mock(return_value=httpx.Response(200, text=EMPTY_RSS))

        articles = await CompanyNewsAgent().fetch()

    assert articles == []
