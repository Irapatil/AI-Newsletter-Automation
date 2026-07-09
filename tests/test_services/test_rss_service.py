"""Tests for RSS/Atom feed fetching and normalization."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from app.services.http_client import HttpClientError, fetch_text
from app.services.rss_service import fetch_feed_entries

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
SAMPLE_RSS = (FIXTURES_DIR / "sample_rss.xml").read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_fetch_feed_entries_parses_and_normalizes() -> None:
    url = "https://example.com/feed.xml"
    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(200, text=SAMPLE_RSS))
        entries = await fetch_feed_entries(url, source_name="Sample Feed")

    assert len(entries) == 2
    first = entries[0]
    assert first["title"] == "OpenAI unveils major new model"
    assert first["url"] == "https://example.com/articles/1"
    assert "major" in first["snippet"]
    assert "<b>" not in first["snippet"]
    assert first["published_at"].year == 2024


@pytest.mark.asyncio
async def test_fetch_feed_entries_returns_empty_on_http_error() -> None:
    url = "https://example.com/broken-feed.xml"
    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(500))
        entries = await fetch_feed_entries(url, source_name="Broken Feed")

    assert entries == []


@pytest.mark.asyncio
async def test_fetch_text_raises_http_client_error_after_retries() -> None:
    url = "https://example.com/always-fails.xml"
    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(503))
        with pytest.raises(HttpClientError):
            await fetch_text(url)
