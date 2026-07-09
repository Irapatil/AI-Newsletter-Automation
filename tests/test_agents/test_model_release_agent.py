"""Tests for ModelReleaseAgent: one Google News RSS query per configured lab."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.agents.model_release_agent import ModelReleaseAgent
from app.config.sources import MODEL_RELEASE_QUERIES, google_news_query_url
from app.models.article import NewsCategory


def _rss_for(company: str) -> str:
    """Two-item RSS feed for a given lab, mirroring tests/fixtures/sample_rss.xml."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{company} model release news</title>
    <link>https://example.com</link>
    <description>Sample feed for tests</description>
    <item>
      <title>{company} unveils new flagship model</title>
      <link>https://example.com/{company}/1</link>
      <description>{company} ships a major new model release.</description>
      <author>reporter@example.com</author>
      <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>{company} model release roundup</title>
      <link>https://example.com/{company}/2</link>
      <description>A roundup of {company} model release news.</description>
      <author>reporter2@example.com</author>
      <pubDate>Mon, 01 Jan 2024 09:30:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


_EMPTY_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Empty feed</title>
    <link>https://example.com</link>
    <description>No items</description>
  </channel>
</rss>
"""


@pytest.mark.asyncio
async def test_fetch_queries_every_configured_lab_and_tags_category() -> None:
    with respx.mock:
        for company, query in MODEL_RELEASE_QUERIES.items():
            respx.get(google_news_query_url(query)).mock(
                return_value=httpx.Response(200, text=_rss_for(company))
            )

        articles = await ModelReleaseAgent().fetch()

    assert len(articles) == len(MODEL_RELEASE_QUERIES) * 2

    by_company: dict[str, list] = {}
    for article in articles:
        by_company.setdefault(article.metadata["company"], []).append(article)

    assert set(by_company.keys()) == set(MODEL_RELEASE_QUERIES.keys())
    for company, company_articles in by_company.items():
        assert len(company_articles) == 2
        for article in company_articles:
            assert article.category == NewsCategory.MODEL_RELEASE
            assert article.source == f"{company} Model Release"
            assert article.metadata == {"company": company}

    openai_first = by_company["OpenAI"][0]
    assert openai_first.title == "OpenAI unveils new flagship model"
    assert openai_first.url == "https://example.com/OpenAI/1"
    assert "OpenAI ships a major new model release" in openai_first.snippet
    assert openai_first.author == "reporter@example.com"
    assert openai_first.published_at.year == 2024


@pytest.mark.asyncio
async def test_fetch_isolates_a_single_failing_feed() -> None:
    failing_company = next(iter(MODEL_RELEASE_QUERIES))
    with respx.mock:
        for company, query in MODEL_RELEASE_QUERIES.items():
            url = google_news_query_url(query)
            if company == failing_company:
                respx.get(url).mock(return_value=httpx.Response(500))
            else:
                respx.get(url).mock(return_value=httpx.Response(200, text=_rss_for(company)))

        articles = await ModelReleaseAgent().fetch()

    companies_returned = {article.metadata["company"] for article in articles}
    assert failing_company not in companies_returned
    assert companies_returned == set(MODEL_RELEASE_QUERIES.keys()) - {failing_company}
    assert len(articles) == (len(MODEL_RELEASE_QUERIES) - 1) * 2


@pytest.mark.asyncio
async def test_fetch_returns_empty_list_when_all_feeds_are_empty() -> None:
    with respx.mock:
        for query in MODEL_RELEASE_QUERIES.values():
            respx.get(google_news_query_url(query)).mock(
                return_value=httpx.Response(200, text=_EMPTY_RSS)
            )

        articles = await ModelReleaseAgent().fetch()

    assert articles == []
