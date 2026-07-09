"""Generates GPT-written summaries and assembles the structured newsletter content."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.models.article import Article
from app.models.newsletter import (
    SECTION_ORDER,
    SECTION_TITLES,
    NewsletterContent,
    NewsletterSection,
)
from app.services.llm_service import LLMService, get_llm_service

logger = get_logger(__name__)

_SUMMARY_SYSTEM_PROMPT = (
    "You are a senior AI industry analyst writing for a C-suite executive newsletter. "
    "Summarize the given article in 1-2 crisp, factual sentences. No fluff, no hype, "
    "no markdown formatting."
)

_EXEC_SUMMARY_SYSTEM_PROMPT = (
    "You are a senior AI industry analyst. Write a 3-4 sentence executive summary "
    "synthesizing the most important themes across today's top AI stories, for a "
    "C-suite audience. Be concise, specific, and avoid generic statements."
)

_SUBJECT_SYSTEM_PROMPT = (
    "You write concise, compelling email subject lines (under 90 characters) for a "
    "daily executive AI newsletter, based on the day's top story. Return only the "
    "subject line text."
)

_WATCH_SYSTEM_PROMPT = (
    "You are a senior AI industry analyst. In 2 sentences, explain why the given "
    "story is the single most important thing readers should watch going forward."
)

_MAX_CONCURRENT_SUMMARIES = 5


class NewsletterGeneratorAgent:
    display_name = "NewsletterGeneratorAgent"

    def __init__(self, llm_service: LLMService | None = None) -> None:
        self._llm = llm_service or get_llm_service()

    async def run(self, ranked_articles: list[Article]) -> NewsletterContent:
        capped_articles = self._apply_global_cap(ranked_articles)

        if capped_articles:
            await self._summarize_articles(capped_articles)

        top_story = max(
            capped_articles, key=lambda a: a.scores.total if a.scores else 0.0, default=None
        )

        executive_summary, subject, one_thing_to_watch = await asyncio.gather(
            self._generate_executive_summary(capped_articles),
            self._generate_subject(top_story),
            self._generate_one_thing_to_watch(top_story),
        )

        return NewsletterContent(
            subject=subject,
            executive_summary=executive_summary,
            sections=self._build_sections(capped_articles),
            one_thing_to_watch=one_thing_to_watch,
            generated_at=datetime.now(UTC),
        )

    @staticmethod
    def _apply_global_cap(articles: list[Article]) -> list[Article]:
        max_total = get_settings().newsletter_max_total_articles
        ordered = sorted(articles, key=lambda a: a.scores.total if a.scores else 0.0, reverse=True)
        return ordered[:max_total]

    async def _summarize_articles(self, articles: list[Article]) -> None:
        semaphore = asyncio.Semaphore(_MAX_CONCURRENT_SUMMARIES)

        async def _summarize_one(article: Article) -> None:
            async with semaphore:
                article.ai_summary = await self._llm.generate_text(
                    _SUMMARY_SYSTEM_PROMPT, article.text_for_summarization(), max_tokens=120
                )

        await asyncio.gather(*[_summarize_one(article) for article in articles])

    @staticmethod
    def _build_sections(articles: list[Article]) -> list[NewsletterSection]:
        by_category: dict[str, list[Article]] = {}
        for article in articles:
            by_category.setdefault(article.category.value, []).append(article)

        sections: list[NewsletterSection] = []
        for key in SECTION_ORDER:
            section_articles = by_category.get(key, [])
            if not section_articles:
                continue
            section_articles.sort(key=lambda a: a.scores.total if a.scores else 0.0, reverse=True)
            sections.append(
                NewsletterSection(key=key, title=SECTION_TITLES[key], articles=section_articles)
            )
        return sections

    async def _generate_executive_summary(self, articles: list[Article]) -> str:
        if not articles:
            return "No significant AI developments were detected in the last collection window."
        headlines = "\n".join(f"- {article.title} ({article.source})" for article in articles[:15])
        return await self._llm.generate_text(_EXEC_SUMMARY_SYSTEM_PROMPT, headlines, max_tokens=220)

    async def _generate_subject(self, top_story: Article | None) -> str:
        today_str = datetime.now(UTC).strftime("%B %d, %Y")
        if top_story is None:
            return f"AI Newsletter - {today_str}"
        headline = await self._llm.generate_text(
            _SUBJECT_SYSTEM_PROMPT, top_story.title, max_tokens=30
        )
        return f"{headline.strip() or top_story.title} | {today_str}"

    async def _generate_one_thing_to_watch(self, top_story: Article | None) -> str:
        if top_story is None:
            return "No standout story to highlight today."
        return await self._llm.generate_text(
            _WATCH_SYSTEM_PROMPT, top_story.text_for_summarization(), max_tokens=120
        )
