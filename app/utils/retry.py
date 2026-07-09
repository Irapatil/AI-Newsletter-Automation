"""Shared retry policy for outbound network calls (HTTP, LLM APIs)."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

T = TypeVar("T")

RETRYABLE_EXCEPTIONS = (
    httpx.HTTPError,
    httpx.TimeoutException,
    httpx.TransportError,
    ConnectionError,
    TimeoutError,
)


def with_retry(max_attempts: int = 3) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Exponential-backoff retry decorator, works for both sync and async callables.

    Retries only on transient network errors; programming errors (KeyError,
    ValueError, etc.) propagate immediately.
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        reraise=True,
    )
