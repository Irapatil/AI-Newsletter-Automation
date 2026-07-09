"""Surfaces trending open-source AI repositories and models."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from app.agents.base_agent import BaseCollectorAgent
from app.config.logging_config import get_logger
from app.models.article import Article, NewsCategory
from app.services.github_service import GithubRepo, fetch_trending_ai_repos
from app.services.huggingface_service import HuggingFaceModel, fetch_trending_models

logger = get_logger(__name__)


class OpenSourceAgent(BaseCollectorAgent):
    category = NewsCategory.OPENSOURCE
    state_key = "opensource"
    display_name = "OpenSourceAgent"

    async def fetch(self) -> list[Article]:
        repos_result, models_result = await asyncio.gather(
            fetch_trending_ai_repos(max_results=15),
            fetch_trending_models(max_results=15),
            return_exceptions=True,
        )
        repos = self._unwrap(repos_result, "github")
        models = self._unwrap(models_result, "huggingface")

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

    def _unwrap(
        self, result: list[GithubRepo] | list[HuggingFaceModel] | BaseException, source: str
    ) -> list:
        if isinstance(result, BaseException):
            logger.warning(
                "agent_source_failed", agent=self.display_name, source=source, error=str(result)
            )
            return []
        return result
