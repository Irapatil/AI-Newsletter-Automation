"""Tests for the NewsAPI.org client (optional supplementary source)."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
import respx

from app.config.sources import NEWSAPI_EVERYTHING_URL
from app.services.newsapi_service import fetch_everything


@pytest.mark.asyncio
async def test_fetch_everything_returns_empty_without_api_key() -> None:
    with respx.mock:
        route = respx.get(NEWSAPI_EVERYTHING_URL).mock(return_value=httpx.Response(200, json={}))
        entries = await fetch_everything("AI startups")

    assert entries == []
    assert route.called is False


@pytest.mark.asyncio
async def test_fetch_everything_parses_articles(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEWSAPI_API_KEY", "test-key-123")
    payload = {
        "status": "ok",
        "totalResults": 2,
        "articles": [
            {
                "title": "<b>OpenAI</b> unveils major new model",
                "url": "https://example.com/articles/1",
                "description": "A <i>major</i> new AI model breakthrough.",
                "publishedAt": "2024-05-01T12:00:00Z",
                "author": "Jane Doe",
            },
            {
                "title": "Anthropic ships new Claude release",
                "url": "https://example.com/articles/2",
                "description": "Anthropic announces a new Claude model.",
                "publishedAt": "2024-05-02T08:30:00Z",
                "author": "John Smith",
            },
        ],
    }
    with respx.mock:
        respx.get(NEWSAPI_EVERYTHING_URL).mock(return_value=httpx.Response(200, json=payload))
        entries = await fetch_everything("AI")

    assert len(entries) == 2
    first = entries[0]
    assert first["title"] == "OpenAI unveils major new model"
    assert "<b>" not in first["title"]
    assert first["url"] == "https://example.com/articles/1"
    assert first["snippet"] == "A major new AI model breakthrough."
    assert "<i>" not in first["snippet"]
    assert first["author"] == "Jane Doe"
    assert first["published_at"] == datetime(2024, 5, 1, 12, 0, 0, tzinfo=UTC)

    second = entries[1]
    assert second["title"] == "Anthropic ships new Claude release"
    assert second["published_at"] == datetime(2024, 5, 2, 8, 30, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_fetch_everything_falls_back_to_now_on_bad_published_at(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NEWSAPI_API_KEY", "test-key-123")
    payload = {
        "articles": [
            {
                "title": "Missing publishedAt field",
                "url": "https://example.com/articles/3",
                "description": "No publishedAt key present.",
                "author": None,
            },
            {
                "title": "Malformed publishedAt field",
                "url": "https://example.com/articles/4",
                "description": "publishedAt is not a valid ISO8601 timestamp.",
                "publishedAt": "not-a-date",
                "author": None,
            },
        ],
    }
    before = datetime.now(UTC)
    with respx.mock:
        respx.get(NEWSAPI_EVERYTHING_URL).mock(return_value=httpx.Response(200, json=payload))
        entries = await fetch_everything("AI")
    after = datetime.now(UTC)

    assert len(entries) == 2
    for entry in entries:
        assert before <= entry["published_at"] <= after


@pytest.mark.asyncio
async def test_fetch_everything_returns_empty_on_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NEWSAPI_API_KEY", "test-key-123")
    with respx.mock:
        respx.get(NEWSAPI_EVERYTHING_URL).mock(return_value=httpx.Response(500))
        entries = await fetch_everything("AI")

    assert entries == []
