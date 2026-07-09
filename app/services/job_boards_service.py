"""Public job-board API clients (Greenhouse, Lever) used by TalentAgent.

Both APIs are public and require no authentication to read published job
postings, so AI hiring-trend signal is available out-of-the-box.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TypedDict

from app.config.logging_config import get_logger
from app.config.sources import AI_TALENT_KEYWORDS, GREENHOUSE_JOB_BOARD_API, LEVER_POSTINGS_API
from app.services.http_client import HttpClientError, fetch_json
from app.utils.text_utils import strip_html

logger = get_logger(__name__)


class JobPosting(TypedDict):
    title: str
    url: str
    company: str
    location: str
    published_at: datetime
    snippet: str


def _matches_ai_keywords(title: str) -> bool:
    lowered = title.lower()
    return any(keyword in lowered for keyword in AI_TALENT_KEYWORDS)


async def fetch_greenhouse_jobs(board_token: str) -> list[JobPosting]:
    url = GREENHOUSE_JOB_BOARD_API.format(board_token=board_token)
    try:
        payload = await fetch_json(url, params={"content": "true"})
    except HttpClientError as exc:
        logger.warning("greenhouse_fetch_failed", board_token=board_token, error=str(exc))
        return []

    jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
    postings: list[JobPosting] = []
    for job in jobs:
        title = job.get("title", "")
        if not _matches_ai_keywords(title):
            continue
        try:
            published_at = datetime.fromisoformat(job["updated_at"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            published_at = datetime.now(UTC)
        postings.append(
            JobPosting(
                title=title,
                url=job.get("absolute_url", ""),
                company=board_token,
                location=(job.get("location") or {}).get("name", ""),
                published_at=published_at,
                snippet=strip_html(job.get("content", ""))[:400],
            )
        )
    return postings


async def fetch_lever_postings(company_slug: str) -> list[JobPosting]:
    url = LEVER_POSTINGS_API.format(company_slug=company_slug)
    try:
        payload = await fetch_json(url)
    except HttpClientError as exc:
        logger.warning("lever_fetch_failed", company_slug=company_slug, error=str(exc))
        return []

    postings: list[JobPosting] = []
    for posting in payload if isinstance(payload, list) else []:
        title = posting.get("text", "")
        if not _matches_ai_keywords(title):
            continue
        created_at_ms = posting.get("createdAt", 0)
        try:
            published_at = datetime.fromtimestamp(created_at_ms / 1000, tz=UTC)
        except (TypeError, ValueError, OSError):
            published_at = datetime.now(UTC)
        categories = posting.get("categories", {})
        postings.append(
            JobPosting(
                title=title,
                url=posting.get("hostedUrl", ""),
                company=company_slug,
                location=categories.get("location", ""),
                published_at=published_at,
                snippet=strip_html(posting.get("descriptionHtml", ""))[:400],
            )
        )
    return postings
