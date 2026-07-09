"""Small text-processing helpers shared by collector agents and dedup/ranking."""

from __future__ import annotations

import math
import re
from datetime import UTC, datetime

from bs4 import BeautifulSoup

_WHITESPACE_RE = re.compile(r"\s+")


def strip_html(raw_html: str) -> str:
    """Remove HTML markup, returning clean plain text."""
    if not raw_html:
        return ""
    if "<" not in raw_html:
        return _WHITESPACE_RE.sub(" ", raw_html).strip()
    text = BeautifulSoup(raw_html, "html.parser").get_text(separator=" ")
    return _WHITESPACE_RE.sub(" ", text).strip()


def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Cosine similarity between two equal-length vectors, in [-1, 1]."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b, strict=True))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def hours_since(timestamp: datetime, now: datetime | None = None) -> float:
    """Number of hours elapsed since `timestamp`, tolerant of naive/aware mixes."""
    reference = now or datetime.now(UTC)
    ts = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=UTC)
    reference = reference if reference.tzinfo else reference.replace(tzinfo=UTC)
    delta = reference - ts
    return max(delta.total_seconds() / 3600.0, 0.0)


def normalize_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()
