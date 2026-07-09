"""RSS/Atom feed fetching and normalization (feedparser-based).

Used directly by collector agents for publisher RSS feeds and Google News
RSS search queries, and indirectly by the arXiv service (the arXiv API
returns Atom XML, which feedparser parses natively).
"""

from __future__ import annotations

import calendar
import time
from datetime import UTC, datetime
from typing import Any, TypedDict

import feedparser

from app.config.logging_config import get_logger
from app.services.http_client import HttpClientError, fetch_text
from app.utils.text_utils import strip_html

logger = get_logger(__name__)


class FeedEntry(TypedDict):
    title: str
    url: str
    snippet: str
    published_at: datetime
    author: str | None


def _parse_published(entry: dict[str, Any]) -> datetime:
    struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if isinstance(struct, time.struct_time):
        return datetime.fromtimestamp(calendar.timegm(struct), tz=UTC)
    return datetime.now(UTC)


def normalize_entry(entry: dict[str, Any]) -> FeedEntry:
    raw_summary = entry.get("summary") or entry.get("description") or ""
    return FeedEntry(
        title=strip_html(entry.get("title", "")),
        url=entry.get("link", ""),
        snippet=strip_html(raw_summary),
        published_at=_parse_published(entry),
        author=entry.get("author"),
    )


async def fetch_feed_entries(url: str, source_name: str) -> list[FeedEntry]:
    """Fetch and parse a single RSS/Atom feed, returning normalized entries.

    Network or parse failures are logged and result in an empty list rather
    than raising, so one broken feed never fails the whole collection run.
    """
    try:
        raw_xml = await fetch_text(url)
    except HttpClientError as exc:
        logger.warning("rss_feed_unavailable", source=source_name, url=url, error=str(exc))
        return []

    parsed = feedparser.parse(raw_xml)
    if parsed.bozo and not parsed.entries:
        logger.warning("rss_feed_parse_error", source=source_name, url=url)
        return []

    return [normalize_entry(entry) for entry in parsed.entries]
