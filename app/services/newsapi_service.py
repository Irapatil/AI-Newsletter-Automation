"""NewsAPI.org client - optional supplementary source for global/policy news."""

from __future__ import annotations

from datetime import UTC, datetime

from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.config.sources import NEWSAPI_EVERYTHING_URL
from app.services.http_client import HttpClientError, fetch_json
from app.services.rss_service import FeedEntry
from app.utils.text_utils import strip_html

logger = get_logger(__name__)


async def fetch_everything(query: str, max_results: int = 20) -> list[FeedEntry]:
    settings = get_settings()
    if not settings.newsapi_api_key:
        return []

    params = {
        "q": query,
        "sortBy": "publishedAt",
        "pageSize": str(max_results),
        "language": "en",
        "apiKey": settings.newsapi_api_key,
    }

    try:
        payload = await fetch_json(NEWSAPI_EVERYTHING_URL, params=params)
    except HttpClientError as exc:
        logger.warning("newsapi_fetch_failed", query=query, error=str(exc))
        return []

    articles = payload.get("articles", []) if isinstance(payload, dict) else []
    entries: list[FeedEntry] = []
    for article in articles:
        try:
            published_at = datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            published_at = datetime.now(UTC)
        entries.append(
            FeedEntry(
                title=strip_html(article.get("title", "")),
                url=article.get("url", ""),
                snippet=strip_html(article.get("description") or ""),
                published_at=published_at,
                author=article.get("author"),
            )
        )
    return entries
