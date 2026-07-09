"""Tracks AI policy and regulation developments (EU AI Act, India AI Mission, US EOs)."""

from __future__ import annotations

import asyncio

from app.agents.base_agent import BaseCollectorAgent
from app.config.settings import get_settings
from app.config.sources import POLICY_QUERIES, google_news_query_url
from app.models.article import Article, NewsCategory
from app.services.newsapi_service import fetch_everything
from app.services.rss_service import fetch_feed_entries


class PolicyAgent(BaseCollectorAgent):
    category = NewsCategory.POLICY
    state_key = "policy"
    display_name = "PolicyAgent"

    async def fetch(self) -> list[Article]:
        urls = {
            topic: google_news_query_url(query, when="7d")
            for topic, query in POLICY_QUERIES.items()
        }
        results = await asyncio.gather(
            *[fetch_feed_entries(url, topic) for topic, url in urls.items()]
        )

        articles: list[Article] = []
        for topic, entries in zip(urls.keys(), results, strict=True):
            for entry in entries:
                if not entry["url"]:
                    continue
                articles.append(
                    Article(
                        title=entry["title"],
                        url=entry["url"],
                        source=f"Policy: {topic}",
                        category=self.category,
                        published_at=entry["published_at"],
                        snippet=entry["snippet"],
                        author=entry["author"],
                        metadata={"topic": topic},
                    )
                )

        if get_settings().newsapi_api_key:
            for topic, query in POLICY_QUERIES.items():
                supplemental = await fetch_everything(query)
                for entry in supplemental:
                    if not entry["url"]:
                        continue
                    articles.append(
                        Article(
                            title=entry["title"],
                            url=entry["url"],
                            source=f"Policy: {topic} (NewsAPI)",
                            category=self.category,
                            published_at=entry["published_at"],
                            snippet=entry["snippet"],
                            author=entry["author"],
                            metadata={"topic": topic},
                        )
                    )

        return articles
