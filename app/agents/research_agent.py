"""Collects recent AI/ML research papers from arXiv."""

from __future__ import annotations

from app.agents.base_agent import BaseCollectorAgent
from app.models.article import Article, NewsCategory
from app.services.arxiv_service import fetch_recent_papers


class ResearchAgent(BaseCollectorAgent):
    category = NewsCategory.RESEARCH
    state_key = "research"
    display_name = "ResearchAgent"

    async def fetch(self) -> list[Article]:
        papers = await fetch_recent_papers(max_results=25)

        return [
            Article(
                title=paper["title"],
                url=paper["url"],
                source="arXiv",
                category=self.category,
                published_at=paper["published_at"],
                snippet=paper["snippet"],
                author=paper["author"],
                metadata={"categories": paper["categories"]},
            )
            for paper in papers
            if paper["url"]
        ]
