"""Semantic deduplication via embedding cosine similarity.

Articles are sorted freshest-first so, among near-duplicate stories
(the same news covered by multiple publishers), the most recent copy is
kept as canonical.
"""

from __future__ import annotations

from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.models.article import Article
from app.services.llm_service import LLMService, get_llm_service
from app.utils.text_utils import cosine_similarity

logger = get_logger(__name__)


class DeduplicationAgent:
    display_name = "DeduplicationAgent"

    def __init__(
        self, llm_service: LLMService | None = None, threshold: float | None = None
    ) -> None:
        self._llm_service = llm_service or get_llm_service()
        self._threshold = (
            threshold if threshold is not None else get_settings().dedup_similarity_threshold
        )

    async def run(self, articles: list[Article]) -> list[Article]:
        if not articles:
            return []

        ordered = sorted(articles, key=lambda a: a.published_at, reverse=True)
        embeddings = await self._llm_service.embed_texts([a.text_for_embedding() for a in ordered])
        for article, embedding in zip(ordered, embeddings, strict=True):
            article.embedding = embedding

        kept: list[Article] = []
        duplicate_count = 0
        for article in ordered:
            if article.embedding and self._is_duplicate(article.embedding, kept):
                duplicate_count += 1
                continue
            kept.append(article)

        logger.info(
            "deduplication_completed",
            input_count=len(articles),
            output_count=len(kept),
            duplicates_removed=duplicate_count,
            threshold=self._threshold,
        )
        return kept

    def _is_duplicate(self, embedding: list[float], kept: list[Article]) -> bool:
        return any(
            cosine_similarity(embedding, other.embedding) >= self._threshold
            for other in kept
            if other.embedding
        )
