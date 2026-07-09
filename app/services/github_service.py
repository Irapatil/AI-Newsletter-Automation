"""GitHub Search API client used by OpenSourceAgent to surface trending AI repos.

Uses the public Search API (no auth required, 60 req/hr). Setting
`GITHUB_TOKEN` raises the rate limit to 5000 req/hr.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TypedDict

from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.config.sources import GITHUB_SEARCH_API
from app.services.http_client import HttpClientError, fetch_json

logger = get_logger(__name__)


class GithubRepo(TypedDict):
    name: str
    url: str
    description: str
    stars: int
    language: str | None
    created_at: datetime


def _build_query(days: int) -> str:
    since = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%d")
    return f"(artificial-intelligence OR llm OR machine-learning) created:>{since}"


async def fetch_trending_ai_repos(max_results: int = 15, days: int = 7) -> list[GithubRepo]:
    settings = get_settings()
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    params = {
        "q": _build_query(days),
        "sort": "stars",
        "order": "desc",
        "per_page": str(max_results),
    }

    try:
        payload = await fetch_json(GITHUB_SEARCH_API, params=params, headers=headers)
    except HttpClientError as exc:
        logger.warning("github_search_failed", error=str(exc))
        return []

    items = payload.get("items", []) if isinstance(payload, dict) else []
    repos: list[GithubRepo] = []
    for item in items:
        try:
            created_at = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            created_at = datetime.now(UTC)
        repos.append(
            GithubRepo(
                name=item.get("full_name", "unknown/unknown"),
                url=item.get("html_url", ""),
                description=item.get("description") or "",
                stars=item.get("stargazers_count", 0),
                language=item.get("language"),
                created_at=created_at,
            )
        )
    return repos
