"""Shared retry policy for outbound network calls (HTTP, LLM APIs)."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

T = TypeVar("T")

# httpx.TimeoutException/TransportError are already subclasses of HTTPError.
RETRYABLE_EXCEPTIONS = (httpx.HTTPError, ConnectionError, TimeoutError)


def _is_retryable(exc: BaseException) -> bool:
    """A 4xx response can never succeed on retry; only 5xx/network errors can."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return isinstance(exc, RETRYABLE_EXCEPTIONS)


def with_retry(max_attempts: int = 3) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Exponential-backoff retry decorator, works for both sync and async callables.

    Retries only on transient network errors and 5xx responses; 4xx
    responses and programming errors (KeyError, ValueError, etc.) propagate
    immediately since retrying them can never succeed.
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception(_is_retryable),
        reraise=True,
    )
