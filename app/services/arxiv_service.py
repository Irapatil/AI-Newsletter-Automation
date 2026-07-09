"""arXiv API client (public, unauthenticated) for the ResearchAgent."""

from __future__ import annotations

from typing import Any, TypedDict

import feedparser

from app.config.logging_config import get_logger
from app.config.sources import ARXIV_API_URL, ARXIV_CATEGORIES
from app.services.http_client import HttpClientError, fetch_text
from app.services.rss_service import normalize_entry

logger = get_logger(__name__)


class ArxivPaper(TypedDict):
    title: str
    url: str
    snippet: str
    published_at: Any
    author: str | None
    categories: list[str]


def _build_search_query() -> str:
    return " OR ".join(f"cat:{category}" for category in ARXIV_CATEGORIES)


async def fetch_recent_papers(max_results: int = 20) -> list[ArxivPaper]:
    """Fetch the most recent arXiv papers across the configured AI categories."""
    params = {
        "search_query": _build_search_query(),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": str(max_results),
    }
    try:
        raw_atom = await fetch_text(ARXIV_API_URL, params=params)
    except HttpClientError as exc:
        logger.warning("arxiv_fetch_failed", error=str(exc))
        return []

    parsed = feedparser.parse(raw_atom)
    papers: list[ArxivPaper] = []
    for entry in parsed.entries:
        normalized = normalize_entry(entry)
        authors = entry.get("authors", [])
        author_name = authors[0].get("name") if authors else None
        categories = [tag.get("term") for tag in entry.get("tags", []) if tag.get("term")]
        papers.append(
            ArxivPaper(
                title=normalized["title"],
                url=normalized["url"],
                snippet=normalized["snippet"],
                published_at=normalized["published_at"],
                author=author_name,
                categories=categories,
            )
        )
    return papers
