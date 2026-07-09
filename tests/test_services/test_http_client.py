"""Direct tests for the shared async HTTP client wrapper.

These tests exercise `app.services.http_client` in isolation (not through any
particular caller such as `rss_service` or `funding_provider`) to pin down its
own retry/timeout/error-handling contract: successful GET responses are
returned as-is, query params/headers are forwarded verbatim, and persistent
failures are retried exactly `settings.http_max_retries` times before being
wrapped in `HttpClientError`.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from app.config.settings import get_settings
from app.services.http_client import HttpClientError, fetch_json, fetch_text


@pytest.mark.asyncio
async def test_fetch_text_returns_body_on_200() -> None:
    url = "https://example.com/feed.xml"
    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(200, text="<rss>hello</rss>"))
        body = await fetch_text(url)

    assert body == "<rss>hello</rss>"


@pytest.mark.asyncio
async def test_fetch_json_returns_dict_on_200() -> None:
    url = "https://example.com/api/object"
    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(200, json={"ok": True, "count": 3}))
        body = await fetch_json(url)

    assert body == {"ok": True, "count": 3}


@pytest.mark.asyncio
async def test_fetch_json_returns_list_on_200() -> None:
    url = "https://example.com/api/list"
    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(200, json=[{"id": 1}, {"id": 2}]))
        body = await fetch_json(url)

    assert body == [{"id": 1}, {"id": 2}]


@pytest.mark.asyncio
async def test_fetch_text_raises_http_client_error_after_exhausting_retries() -> None:
    """`with_retry` uses `stop_after_attempt(max_attempts)`, so the request is
    attempted exactly `http_max_retries` times in total (not that many
    *retries* on top of the first attempt) before the final exception is
    reraised and wrapped in `HttpClientError`.
    """
    url = "https://example.com/always-fails.xml"
    settings = get_settings()

    with respx.mock:
        route = respx.get(url).mock(return_value=httpx.Response(503))
        with pytest.raises(HttpClientError):
            await fetch_text(url)

        assert route.call_count == settings.http_max_retries


@pytest.mark.asyncio
async def test_fetch_json_raises_http_client_error_after_exhausting_retries() -> None:
    url = "https://example.com/api/always-fails"
    settings = get_settings()

    with respx.mock:
        route = respx.get(url).mock(return_value=httpx.Response(500))
        with pytest.raises(HttpClientError):
            await fetch_json(url)

        assert route.call_count == settings.http_max_retries


@pytest.mark.asyncio
async def test_http_max_retries_env_override_reduces_attempts(monkeypatch) -> None:
    monkeypatch.setenv("HTTP_MAX_RETRIES", "1")
    get_settings.cache_clear()
    assert get_settings().http_max_retries == 1

    url = "https://example.com/always-fails-one-try.xml"
    with respx.mock:
        route = respx.get(url).mock(return_value=httpx.Response(503))
        with pytest.raises(HttpClientError):
            await fetch_text(url)

        assert route.call_count == 1


@pytest.mark.asyncio
async def test_fetch_text_forwards_query_params_and_headers() -> None:
    url = "https://example.com/feed.xml"
    with respx.mock:
        route = respx.get(url).mock(return_value=httpx.Response(200, text="ok"))
        await fetch_text(
            url,
            params={"category": "ai", "limit": "10"},
            headers={"X-Test-Header": "abc123"},
        )

        sent_request = route.calls.last.request
        assert sent_request.url.params["category"] == "ai"
        assert sent_request.url.params["limit"] == "10"
        assert sent_request.headers["X-Test-Header"] == "abc123"


@pytest.mark.asyncio
async def test_fetch_json_forwards_query_params_and_headers() -> None:
    url = "https://example.com/api/search"
    with respx.mock:
        route = respx.get(url).mock(return_value=httpx.Response(200, json={"results": []}))
        await fetch_json(
            url,
            params={"q": "funding round"},
            headers={"Authorization": "Bearer test-token"},
        )

        sent_request = route.calls.last.request
        assert sent_request.url.params["q"] == "funding round"
        assert sent_request.headers["Authorization"] == "Bearer test-token"
