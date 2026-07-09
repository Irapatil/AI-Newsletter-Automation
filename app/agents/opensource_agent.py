"""Surfaces trending open-source AI repositories and models."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from app.agents.base_agent import BaseCollectorAgent
from app.models.article import Article, NewsCategory
from app.services.github_service import fetch_trending_ai_repos
from app.services.huggingface_service import fetch_trending_models


class OpenSourceAgent(BaseCollectorAgent):
    category = NewsCategory.OPENSOURCE
    state_key = "opensource"
    display_name = "OpenSourceAgent"

    async def fetch(self) -> list[Article]:
        repos, models = await asyncio.gather(
            fetch_trending_ai_repos(max_results=15),
            fetch_trending_models(max_results=15),
        )

        articles: list[Article] = [
            Article(
                title=repo["name"],
                url=repo["url"],
                source="GitHub Trending",
                category=self.category,
                published_at=repo["created_at"],
                snippet=repo["description"],
                metadata={"stars": repo["stars"], "language": repo["language"]},
            )
            for repo in repos
            if repo["url"]
        ]

        articles += [
            Article(
                title=model["model_id"],
                url=model["url"],
                source="Hugging Face",
                category=self.category,
                published_at=model.get("last_modified", datetime.now(UTC)),
                snippet=f"Pipeline: {model['pipeline_tag'] or 'n/a'} | Likes: {model['likes']}",
                metadata={"likes": model["likes"], "downloads": model["downloads"]},
            )
            for model in models
            if model["url"]
        ]
        return articles
