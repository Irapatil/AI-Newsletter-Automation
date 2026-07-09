"""Tracks new foundation-model release announcements across major labs."""

from __future__ import annotations

from app.agents.base_agent import BaseCollectorAgent, gather_isolated
from app.config.sources import MODEL_RELEASE_QUERIES, google_news_query_url
from app.models.article import Article, NewsCategory
from app.services.rss_service import fetch_feed_entries


class ModelReleaseAgent(BaseCollectorAgent):
    category = NewsCategory.MODEL_RELEASE
    state_key = "model_releases"
    display_name = "ModelReleaseAgent"

    async def fetch(self) -> list[Article]:
        urls = {
            company: google_news_query_url(query)
            for company, query in MODEL_RELEASE_QUERIES.items()
        }
        results = await gather_isolated(
            (fetch_feed_entries(url, company) for company, url in urls.items()),
            agent_name=self.display_name,
            labels=urls.keys(),
        )

        articles: list[Article] = []
        for company, entries in zip(urls.keys(), results, strict=True):
            for entry in entries:
                if not entry["url"]:
                    continue
                articles.append(
                    Article(
                        title=entry["title"],
                        url=entry["url"],
                        source=f"{company} Model Release",
                        category=self.category,
                        published_at=entry["published_at"],
                        snippet=entry["snippet"],
                        author=entry["author"],
                        metadata={"company": company},
                    )
                )
        return articles
