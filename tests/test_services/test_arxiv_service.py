"""Tests for the arXiv API client (fetch + Atom parsing)."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.config.sources import ARXIV_API_URL
from app.services.arxiv_service import fetch_recent_papers

SAMPLE_ARXIV_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <link href="http://export.arxiv.org/api/query" rel="self" type="application/atom+xml"/>
  <title type="text">ArXiv Query: search_query=cat:cs.AI</title>
  <id>http://arxiv.org/api/cHxbW1SxIuNS6TQpZzsc0hkg9RQ</id>
  <updated>2024-01-02T00:00:00-05:00</updated>
  <opensearch:totalResults>2</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
  <opensearch:itemsPerPage>2</opensearch:itemsPerPage>
  <entry>
    <id>http://arxiv.org/abs/2401.00001v1</id>
    <updated>2024-01-01T12:00:00Z</updated>
    <published>2024-01-01T12:00:00Z</published>
    <title>A Novel Approach to Large Language Model Reasoning</title>
    <summary>  This paper introduces a &lt;b&gt;novel&lt;/b&gt; approach to reasoning in
      large language models.
    </summary>
    <author><name>Jane Doe</name></author>
    <author><name>John Smith</name></author>
    <link href="http://arxiv.org/abs/2401.00001v1" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2401.00001v1" rel="related" type="application/pdf"/>
    <arxiv:primary_category xmlns:arxiv="http://arxiv.org/schemas/atom" term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2401.00002v2</id>
    <updated>2024-01-01T09:30:00Z</updated>
    <published>2024-01-01T09:30:00Z</published>
    <title>Scaling Laws for Multilingual Text Classification</title>
    <summary>An empirical study of scaling laws for multilingual text classifiers.</summary>
    <link href="http://arxiv.org/abs/2401.00002v2" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2401.00002v2" rel="related" type="application/pdf"/>
    <arxiv:primary_category xmlns:arxiv="http://arxiv.org/schemas/atom" term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
</feed>
"""

EMPTY_ARXIV_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
  <link href="http://export.arxiv.org/api/query" rel="self" type="application/atom+xml"/>
  <title type="text">ArXiv Query: search_query=cat:cs.AI</title>
  <id>http://arxiv.org/api/cHxbW1SxIuNS6TQpZzsc0hkg9RQ</id>
  <updated>2024-01-02T00:00:00-05:00</updated>
  <opensearch:totalResults>0</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
  <opensearch:itemsPerPage>0</opensearch:itemsPerPage>
</feed>
"""


@pytest.mark.asyncio
async def test_fetch_recent_papers_parses_and_normalizes() -> None:
    with respx.mock:
        respx.get(url__startswith=ARXIV_API_URL).mock(
            return_value=httpx.Response(200, text=SAMPLE_ARXIV_ATOM)
        )
        papers = await fetch_recent_papers(max_results=5)

    assert len(papers) == 2

    first = papers[0]
    assert first["title"] == "A Novel Approach to Large Language Model Reasoning"
    assert first["url"] == "http://arxiv.org/abs/2401.00001v1"
    assert "novel" in first["snippet"]
    assert "<b>" not in first["snippet"]
    assert first["published_at"].year == 2024
    assert first["author"] == "Jane Doe"
    assert first["categories"] == ["cs.AI", "cs.LG"]

    second = papers[1]
    assert second["title"] == "Scaling Laws for Multilingual Text Classification"
    assert second["url"] == "http://arxiv.org/abs/2401.00002v2"
    assert second["author"] is None
    assert second["categories"] == ["cs.CL"]


@pytest.mark.asyncio
async def test_fetch_recent_papers_returns_empty_on_http_error() -> None:
    with respx.mock:
        respx.get(url__startswith=ARXIV_API_URL).mock(return_value=httpx.Response(500))
        papers = await fetch_recent_papers(max_results=5)

    assert papers == []


@pytest.mark.asyncio
async def test_fetch_recent_papers_returns_empty_when_no_entries() -> None:
    with respx.mock:
        respx.get(url__startswith=ARXIV_API_URL).mock(
            return_value=httpx.Response(200, text=EMPTY_ARXIV_ATOM)
        )
        papers = await fetch_recent_papers(max_results=5)

    assert papers == []
