"""Scores and ranks articles across six weighted dimensions.

Freshness, source credibility, and research-impact use structural signals
(publish time, source registry, category). Importance, business impact, and
AI relevance use transparent keyword heuristics, which keeps ranking fast,
deterministic, and fully unit-testable without an LLM call per article.
"""

from __future__ import annotations

from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.config.sources import SOURCE_CREDIBILITY
from app.models.article import Article, ArticleScores, NewsCategory
from app.utils.text_utils import hours_since

logger = get_logger(__name__)

_DEFAULT_CREDIBILITY_BY_CATEGORY: dict[NewsCategory, float] = {
    NewsCategory.GLOBAL: 0.8,
    NewsCategory.COMPANY: 0.7,
    NewsCategory.FUNDING: 0.65,
    NewsCategory.TALENT: 0.6,
    NewsCategory.RESEARCH: 0.9,
    NewsCategory.OPENSOURCE: 0.75,
    NewsCategory.POLICY: 0.75,
    NewsCategory.MODEL_RELEASE: 0.75,
}

_IMPORTANCE_KEYWORDS = [
    "breakthrough",
    "first",
    "record",
    "major",
    "significant",
    "announces",
    "unveils",
    "launches",
    "releases",
    "milestone",
]

_BUSINESS_IMPACT_KEYWORDS = [
    "funding",
    "raises",
    "million",
    "billion",
    "acquisition",
    "acquires",
    "ipo",
    "valuation",
    "revenue",
    "partnership",
    "layoffs",
    "hires",
]

_AI_RELEVANCE_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "machine learning",
    "llm",
    "gpt",
    "neural",
    "deep learning",
    "generative ai",
    "genai",
    "chatbot",
    "copilot",
    "model",
]

_RESEARCH_KEYWORDS = ["state-of-the-art", "sota", "benchmark", "dataset", "novel"]


def _keyword_density_score(text: str, keywords: list[str]) -> float:
    lowered = text.lower()
    matches = sum(1 for keyword in keywords if keyword in lowered)
    return min(1.0, matches * 0.25)


def _freshness_score(article: Article, max_age_hours: float) -> float:
    if max_age_hours <= 0:
        return 0.0
    age = hours_since(article.published_at)
    return max(0.0, 1.0 - (age / max_age_hours))


def _source_credibility_score(article: Article) -> float:
    for known_source, score in SOURCE_CREDIBILITY.items():
        if known_source.lower() in article.source.lower():
            return score
    return _DEFAULT_CREDIBILITY_BY_CATEGORY.get(article.category, 0.6)


def _research_impact_score(article: Article) -> float:
    text = f"{article.title} {article.snippet}"
    if article.category == NewsCategory.RESEARCH:
        return min(1.0, 0.6 + _keyword_density_score(text, _RESEARCH_KEYWORDS))
    if article.category == NewsCategory.MODEL_RELEASE:
        return min(1.0, 0.4 + _keyword_density_score(text, _RESEARCH_KEYWORDS))
    return _keyword_density_score(text, _RESEARCH_KEYWORDS) * 0.3


def score_article(
    article: Article, max_age_hours: float, weights: dict[str, float]
) -> ArticleScores:
    text = f"{article.title} {article.snippet}"
    scores = ArticleScores(
        freshness=_freshness_score(article, max_age_hours),
        importance=_keyword_density_score(text, _IMPORTANCE_KEYWORDS),
        business_impact=_keyword_density_score(text, _BUSINESS_IMPACT_KEYWORDS),
        source_credibility=_source_credibility_score(article),
        research_impact=_research_impact_score(article),
        ai_relevance=_keyword_density_score(text, _AI_RELEVANCE_KEYWORDS),
    )
    scores.total = (
        weights["freshness"] * scores.freshness
        + weights["importance"] * scores.importance
        + weights["business_impact"] * scores.business_impact
        + weights["source_credibility"] * scores.source_credibility
        + weights["research_impact"] * scores.research_impact
        + weights["ai_relevance"] * scores.ai_relevance
    )
    return scores


class RankingAgent:
    display_name = "RankingAgent"

    def run(self, articles: list[Article]) -> list[Article]:
        settings = get_settings()
        weights = settings.ranking_weights
        top_n = settings.ranking_top_stories_per_section

        for article in articles:
            article.scores = score_article(article, settings.max_article_age_hours, weights)

        by_category: dict[NewsCategory, list[Article]] = {}
        for article in articles:
            by_category.setdefault(article.category, []).append(article)

        ranked: list[Article] = []
        for category_articles in by_category.values():
            category_articles.sort(key=lambda a: a.scores.total if a.scores else 0.0, reverse=True)
            ranked.extend(category_articles[:top_n])

        logger.info(
            "ranking_completed", input_count=len(articles), output_count=len(ranked), top_n=top_n
        )
        return ranked
