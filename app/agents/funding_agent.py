"""Tracks AI startup funding rounds and investment activity."""

from __future__ import annotations

from app.agents.base_agent import BaseCollectorAgent
from app.models.article import Article, NewsCategory
from app.services.funding_provider import get_funding_provider


class FundingAgent(BaseCollectorAgent):
    category = NewsCategory.FUNDING
    state_key = "funding"
    display_name = "FundingAgent"

    async def fetch(self) -> list[Article]:
        provider = get_funding_provider()
        rounds = await provider.fetch_recent_funding_rounds(max_results=20)

        articles: list[Article] = []
        for round_ in rounds:
            if not round_["url"]:
                continue
            articles.append(
                Article(
                    title=round_["title"],
                    url=round_["url"],
                    source=type(provider).__name__,
                    category=self.category,
                    published_at=round_["published_at"],
                    snippet=round_["snippet"],
                    metadata={"company": round_["company"], "amount_usd": round_["amount_usd"]},
                )
            )
        return articles
