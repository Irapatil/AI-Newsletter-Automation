"""Abstract base class shared by all collector agents.

Each collector agent is responsible for exactly one `NewsCategory` / one
`GraphState` field. `collect()` wraps the agent-specific `fetch()` with
timing, structured logging, freshness filtering, and exception isolation so
a single failing source never aborts the whole LangGraph run.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import ClassVar

from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.models.article import Article, NewsCategory
from app.utils.text_utils import hours_since

logger = get_logger(__name__)


class CollectorResult:
    """Outcome of a single agent's `collect()` call."""

    __slots__ = ("articles", "logs", "errors")

    def __init__(self, articles: list[Article], logs: list[str], errors: list[str]) -> None:
        self.articles = articles
        self.logs = logs
        self.errors = errors


class BaseCollectorAgent(ABC):
    """Base class for the eight parallel collector agents."""

    category: ClassVar[NewsCategory]
    state_key: ClassVar[str]
    display_name: ClassVar[str]

    @abstractmethod
    async def fetch(self) -> list[Article]:
        """Fetch and normalize articles from this agent's sources."""
        raise NotImplementedError

    async def collect(self) -> CollectorResult:
        start = time.monotonic()
        try:
            articles = await self.fetch()
        except Exception as exc:  # noqa: BLE001 - isolate failures per agent
            elapsed = time.monotonic() - start
            logger.error("collector_agent_failed", agent=self.display_name, error=str(exc))
            return CollectorResult(
                articles=[],
                logs=[],
                errors=[f"{self.display_name}: failed after {elapsed:.2f}s - {exc}"],
            )

        fresh_articles = self._filter_stale(articles)
        elapsed = time.monotonic() - start
        logger.info(
            "collector_agent_completed",
            agent=self.display_name,
            collected=len(articles),
            fresh=len(fresh_articles),
            elapsed_seconds=round(elapsed, 2),
        )
        log_line = (
            f"{self.display_name}: collected {len(fresh_articles)} fresh articles "
            f"({len(articles)} total) in {elapsed:.2f}s"
        )
        return CollectorResult(articles=fresh_articles, logs=[log_line], errors=[])

    def _filter_stale(self, articles: list[Article]) -> list[Article]:
        max_age = get_settings().max_article_age_hours
        return [a for a in articles if hours_since(a.published_at) <= max_age]
