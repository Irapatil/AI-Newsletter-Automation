"""Thin async HTTP client wrapper with timeout, retry, and structured logging.

Every collector agent that hits an external HTTP/REST API goes through this
module so retry/timeout/error-handling behavior is consistent and testable
via `respx` mocks in the test suite.
"""

from __future__ import annotations

import httpx

from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.utils.retry import with_retry

logger = get_logger(__name__)


class HttpClientError(RuntimeError):
    """Raised when an HTTP request fails after all retries are exhausted."""


async def fetch_text(url: str, params: dict | None = None, headers: dict | None = None) -> str:
    """GET a URL and return the raw response body as text (e.g. RSS/Atom XML)."""
    settings = get_settings()

    @with_retry(max_attempts=settings.http_max_retries)
    async def _do_fetch() -> str:
        async with httpx.AsyncClient(
            timeout=settings.http_timeout_seconds, follow_redirects=True
        ) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.text

    try:
        return await _do_fetch()
    except (httpx.HTTPError, ConnectionError, TimeoutError) as exc:
        logger.warning("http_fetch_failed", url=url, error=str(exc))
        raise HttpClientError(f"Failed to fetch {url}: {exc}") from exc


async def fetch_json(
    url: str, params: dict | None = None, headers: dict | None = None
) -> dict | list:
    """GET a URL and return the parsed JSON response body."""
    settings = get_settings()

    @with_retry(max_attempts=settings.http_max_retries)
    async def _do_fetch() -> dict | list:
        async with httpx.AsyncClient(
            timeout=settings.http_timeout_seconds, follow_redirects=True
        ) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()

    try:
        return await _do_fetch()
    except (httpx.HTTPError, ConnectionError, TimeoutError) as exc:
        logger.warning("http_fetch_json_failed", url=url, error=str(exc))
        raise HttpClientError(f"Failed to fetch {url}: {exc}") from exc


async def post_json(
    url: str,
    json_body: dict | list,
    params: dict | None = None,
    headers: dict | None = None,
) -> dict | list:
    """POST a JSON body to a URL and return the parsed JSON response body."""
    settings = get_settings()

    @with_retry(max_attempts=settings.http_max_retries)
    async def _do_post() -> dict | list:
        async with httpx.AsyncClient(
            timeout=settings.http_timeout_seconds, follow_redirects=True
        ) as client:
            response = await client.post(url, params=params, headers=headers, json=json_body)
            response.raise_for_status()
            return response.json()

    try:
        return await _do_post()
    except (httpx.HTTPError, ConnectionError, TimeoutError) as exc:
        logger.warning("http_post_json_failed", url=url, error=str(exc))
        raise HttpClientError(f"Failed to POST {url}: {exc}") from exc
