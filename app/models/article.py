"""Core domain models representing a collected news item and its scoring."""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class NewsCategory(str, Enum):
    """The eight collection categories fanned out to by the LangGraph orchestrator."""

    GLOBAL = "global_news"
    COMPANY = "company_news"
    FUNDING = "funding"
    TALENT = "talent"
    RESEARCH = "research"
    OPENSOURCE = "opensource"
    POLICY = "policy"
    MODEL_RELEASE = "model_releases"


def make_article_id(url: str, title: str) -> str:
    """Deterministic id so the same story collected twice collapses naturally."""
    digest_source = url or title
    return hashlib.sha256(digest_source.strip().lower().encode("utf-8")).hexdigest()[:16]


class ArticleScores(BaseModel):
    """Per-dimension ranking scores, each normalized to [0, 1]."""

    freshness: float = 0.0
    importance: float = 0.0
    business_impact: float = 0.0
    source_credibility: float = 0.0
    research_impact: float = 0.0
    ai_relevance: float = 0.0
    total: float = 0.0


class Article(BaseModel):
    """A single collected news item, enriched through the pipeline."""

    id: str = ""
    title: str
    url: str
    source: str
    category: NewsCategory
    published_at: datetime
    snippet: str = ""
    content: str = ""
    author: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    embedding: list[float] | None = None
    scores: ArticleScores = Field(default_factory=ArticleScores)
    ai_summary: str | None = None

    @model_validator(mode="after")
    def _default_id(self) -> Article:
        # A `field_validator(mode="before")` on `id` itself would never fire
        # when `id` is left at its default (Pydantic v2 skips before-validators
        # for unset fields unless `validate_default=True`), and even with that
        # set, `id`'s position before `url`/`title` in the field order would
        # mean those fields weren't validated yet when it ran. An `after`
        # model validator runs once every field is populated, regardless of
        # declaration order.
        if not self.id:
            self.id = make_article_id(self.url, self.title)
        return self

    def text_for_embedding(self) -> str:
        """Text representation used to compute semantic-deduplication embeddings."""
        return f"{self.title}\n{self.snippet}".strip()

    def text_for_summarization(self) -> str:
        return f"Title: {self.title}\nSource: {self.source}\nSnippet: {self.snippet}\n{self.content}".strip()
