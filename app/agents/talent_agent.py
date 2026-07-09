"""Tracks AI hiring and talent trends across Greenhouse, Lever, and LinkedIn."""

from __future__ import annotations

import asyncio

from app.agents.base_agent import BaseCollectorAgent
from app.config.settings import get_settings
from app.models.article import Article, NewsCategory
from app.services.job_boards_service import JobPosting, fetch_greenhouse_jobs, fetch_lever_postings
from app.services.linkedin_provider import get_linkedin_provider


class TalentAgent(BaseCollectorAgent):
    category = NewsCategory.TALENT
    state_key = "talent"
    display_name = "TalentAgent"

    async def fetch(self) -> list[Article]:
        settings = get_settings()

        greenhouse_task = asyncio.gather(
            *[fetch_greenhouse_jobs(token) for token in settings.greenhouse_board_token_list]
        )
        lever_task = asyncio.gather(
            *[fetch_lever_postings(slug) for slug in settings.lever_company_slug_list]
        )
        linkedin_task = get_linkedin_provider().fetch_ai_jobs(max_results=10)

        greenhouse_results, lever_results, linkedin_postings = await asyncio.gather(
            greenhouse_task, lever_task, linkedin_task
        )

        postings: list[JobPosting] = [p for batch in greenhouse_results for p in batch]
        postings += [p for batch in lever_results for p in batch]
        postings += linkedin_postings

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
