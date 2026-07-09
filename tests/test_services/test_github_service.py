"""Tests for the GitHub Search API client used to surface trending AI repos."""

from __future__ import annotations

from datetime import UTC

import httpx
import pytest
import respx

from app.config.sources import GITHUB_SEARCH_API
from app.services.github_service import fetch_trending_ai_repos


def _make_item(
    *,
    full_name: str = "acme/llm-toolkit",
    html_url: str = "https://github.com/acme/llm-toolkit",
    description: str = "A toolkit for building LLM apps.",
    stargazers_count: int = 1234,
    language: str | None = "Python",
    created_at: str = "2024-01-01T12:00:00Z",
) -> dict:
    return {
        "full_name": full_name,
        "html_url": html_url,
        "description": description,
        "stargazers_count": stargazers_count,
        "language": language,
        "created_at": created_at,
    }


@pytest.mark.asyncio
async def test_fetch_trending_ai_repos_parses_items() -> None:
    payload = {
        "items": [
            _make_item(
                full_name="acme/llm-toolkit",
                html_url="https://github.com/acme/llm-toolkit",
                description="A toolkit for building LLM apps.",
                stargazers_count=1234,
                language="Python",
                created_at="2024-01-01T12:00:00Z",
            ),
            _make_item(
                full_name="other/agentic-flow",
                html_url="https://github.com/other/agentic-flow",
                description="Agentic workflow orchestration.",
                stargazers_count=42,
                language="TypeScript",
                created_at="2024-06-15T08:30:00Z",
            ),
        ]
    }
    with respx.mock:
        respx.get(GITHUB_SEARCH_API).mock(return_value=httpx.Response(200, json=payload))
        repos = await fetch_trending_ai_repos()

    assert len(repos) == 2

    first = repos[0]
    assert first["name"] == "acme/llm-toolkit"
    assert first["url"] == "https://github.com/acme/llm-toolkit"
    assert first["description"] == "A toolkit for building LLM apps."
    assert first["stars"] == 1234
    assert first["language"] == "Python"
    assert first["created_at"].tzinfo is not None
    assert first["created_at"] == first["created_at"].astimezone(UTC)
    assert first["created_at"].year == 2024
    assert first["created_at"].month == 1
    assert first["created_at"].day == 1

    second = repos[1]
    assert second["name"] == "other/agentic-flow"
    assert second["stars"] == 42
    assert second["language"] == "TypeScript"
    assert second["created_at"].month == 6


@pytest.mark.asyncio
async def test_fetch_trending_ai_repos_omits_auth_header_when_token_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    payload = {"items": [_make_item()]}
    with respx.mock:
        route = respx.get(GITHUB_SEARCH_API).mock(return_value=httpx.Response(200, json=payload))
        await fetch_trending_ai_repos()

    sent_headers = route.calls.last.request.headers
    assert "authorization" not in sent_headers


@pytest.mark.asyncio
async def test_fetch_trending_ai_repos_adds_auth_header_when_token_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test123")
    payload = {"items": [_make_item()]}
    with respx.mock:
        route = respx.get(GITHUB_SEARCH_API).mock(return_value=httpx.Response(200, json=payload))
        await fetch_trending_ai_repos()

    sent_headers = route.calls.last.request.headers
    assert sent_headers["authorization"] == "Bearer ghp_test123"


@pytest.mark.asyncio
async def test_fetch_trending_ai_repos_returns_empty_list_on_http_error() -> None:
    with respx.mock:
        respx.get(GITHUB_SEARCH_API).mock(return_value=httpx.Response(500))
        repos = await fetch_trending_ai_repos()

    assert repos == []


@pytest.mark.asyncio
async def test_fetch_trending_ai_repos_falls_back_to_now_on_bad_created_at() -> None:
    payload = {
        "items": [
            _make_item(full_name="acme/broken-dates", created_at="not-a-real-date"),
        ]
    }
    with respx.mock:
        respx.get(GITHUB_SEARCH_API).mock(return_value=httpx.Response(200, json=payload))
        repos = await fetch_trending_ai_repos()

    assert len(repos) == 1
    assert repos[0]["name"] == "acme/broken-dates"
    # Malformed created_at should fall back to "now" rather than raising.
    assert repos[0]["created_at"].tzinfo is not None


@pytest.mark.asyncio
async def test_fetch_trending_ai_repos_falls_back_to_now_on_missing_created_at() -> None:
    item = _make_item(full_name="acme/no-date")
    del item["created_at"]
    payload = {"items": [item]}
    with respx.mock:
        respx.get(GITHUB_SEARCH_API).mock(return_value=httpx.Response(200, json=payload))
        repos = await fetch_trending_ai_repos()

    assert len(repos) == 1
    assert repos[0]["name"] == "acme/no-date"
    assert repos[0]["created_at"].tzinfo is not None
