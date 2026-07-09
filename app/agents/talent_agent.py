"""Tracks AI hiring and talent trends across Greenhouse, Lever, and LinkedIn."""

from __future__ import annotations

import asyncio

from app.agents.base_agent import BaseCollectorAgent, gather_isolated
from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.models.article import Article, NewsCategory
from app.services.job_boards_service import JobPosting, fetch_greenhouse_jobs, fetch_lever_postings
from app.services.linkedin_provider import get_linkedin_provider

logger = get_logger(__name__)


class TalentAgent(BaseCollectorAgent):
    category = NewsCategory.TALENT
    state_key = "talent"
    display_name = "TalentAgent"

    async def fetch(self) -> list[Article]:
        settings = get_settings()

        greenhouse_task = gather_isolated(
            (fetch_greenhouse_jobs(token) for token in settings.greenhouse_board_token_list),
            agent_name=self.display_name,
            labels=settings.greenhouse_board_token_list,
        )
        lever_task = gather_isolated(
            (fetch_lever_postings(slug) for slug in settings.lever_company_slug_list),
            agent_name=self.display_name,
            labels=settings.lever_company_slug_list,
        )
        linkedin_task = get_linkedin_provider().fetch_ai_jobs(max_results=10)

        greenhouse_batches, lever_batches, linkedin_result = await asyncio.gather(
            greenhouse_task, lever_task, linkedin_task, return_exceptions=True
        )

        postings: list[JobPosting] = []
        if isinstance(greenhouse_batches, BaseException):
            logger.warning(
                "agent_source_failed",
                agent=self.display_name,
                source="greenhouse",
                error=str(greenhouse_batches),
            )
        else:
            postings += [p for batch in greenhouse_batches for p in batch]

        if isinstance(lever_batches, BaseException):
            logger.warning(
                "agent_source_failed",
                agent=self.display_name,
                source="lever",
                error=str(lever_batches),
            )
        else:
            postings += [p for batch in lever_batches for p in batch]

        if isinstance(linkedin_result, BaseException):
            logger.warning(
                "agent_source_failed",
                agent=self.display_name,
                source="linkedin",
                error=str(linkedin_result),
            )
        else:
            postings += linkedin_result

        return [self._to_article(posting) for posting in postings if posting["url"]]

    def _to_article(self, posting: JobPosting) -> Article:
        return Article(
            title=f"{posting['title']} at {posting['company']}",
            url=posting["url"],
            source="LinkedIn Jobs" if "linkedin.com" in posting["url"] else "Greenhouse/Lever",
            category=self.category,
            published_at=posting["published_at"],
            snippet=posting["snippet"],
            metadata={"company": posting["company"], "location": posting["location"]},
        )
