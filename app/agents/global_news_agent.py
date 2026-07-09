"""Collects global AI industry news from major tech publishers."""

from __future__ import annotations

import asyncio

from app.agents.base_agent import BaseCollectorAgent
from app.config.settings import get_settings
from app.config.sources import GLOBAL_NEWS_RSS_FEEDS
from app.models.article import Article, NewsCategory
from app.services.newsapi_service import fetch_everything
from app.services.rss_service import fetch_feed_entries


class GlobalNewsAgent(BaseCollectorAgent):
    category = NewsCategory.GLOBAL
    state_key = "global_news"
    display_name = "GlobalNewsAgent"

    async def fetch(self) -> list[Article]:
        feed_results = await asyncio.gather(
            *[fetch_feed_entries(url, source) for source, url in GLOBAL_NEWS_RSS_FEEDS.items()]
        )

        articles: list[Article] = []
        for source, entries in zip(GLOBAL_NEWS_RSS_FEEDS.keys(), feed_results, strict=True):
            for entry in entries:
                if not entry["url"]:
                    continue
                articles.append(
                    Article(
                        title=entry["title"],
                        url=entry["url"],
                        source=source,
                        category=self.category,
                        published_at=entry["published_at"],
                        snippet=entry["snippet"],
                        author=entry["author"],
                    )
                )

        if get_settings().newsapi_api_key:
            supplemental = await fetch_everything("artificial intelligence")
            for entry in supplemental:
                if not entry["url"]:
                    continue
                articles.append(
                    Article(
                        title=entry["title"],
                        url=entry["url"],
                        source="NewsAPI",
                        category=self.category,
                        published_at=entry["published_at"],
                        snippet=entry["snippet"],
                        author=entry["author"],
                    )
                )

        return articles
