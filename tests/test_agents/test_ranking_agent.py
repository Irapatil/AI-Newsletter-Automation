"""Tests for the deterministic keyword/structural ranking engine."""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.agents.ranking_agent import RankingAgent, score_article
from app.models.article import NewsCategory
from tests.conftest import make_article


def test_freshness_score_decays_with_age(now):
    fresh = make_article(published_at=now)
    stale = make_article(published_at=now - timedelta(hours=40))
    weights = {
        "freshness": 1.0,
        "importance": 0.0,
        "business_impact": 0.0,
        "source_credibility": 0.0,
        "research_impact": 0.0,
        "ai_relevance": 0.0,
    }
    fresh_score = score_article(fresh, max_age_hours=48, weights=weights)
    stale_score = score_article(stale, max_age_hours=48, weights=weights)
    assert fresh_score.total > stale_score.total


def test_business_impact_keywords_increase_score(now):
    funding_article = make_article(
        title="Startup raises $50 million in Series B funding",
        category=NewsCategory.FUNDING,
        published_at=now,
    )
    plain_article = make_article(
        title="A quiet Tuesday in AI", category=NewsCategory.FUNDING, published_at=now
    )
    weights = {
        "freshness": 0.0,
        "importance": 0.0,
        "business_impact": 1.0,
        "source_credibility": 0.0,
        "research_impact": 0.0,
        "ai_relevance": 0.0,
    }
    funding_score = score_article(funding_article, max_age_hours=48, weights=weights)
    plain_score = score_article(plain_article, max_age_hours=48, weights=weights)
    assert funding_score.business_impact > plain_score.business_impact
    assert funding_score.total > plain_score.total


def test_research_impact_favors_research_category(now):
    research_article = make_article(category=NewsCategory.RESEARCH, published_at=now)
    company_article = make_article(category=NewsCategory.COMPANY, published_at=now)
    weights = {
        "freshness": 0.0,
        "importance": 0.0,
        "business_impact": 0.0,
        "source_credibility": 0.0,
        "research_impact": 1.0,
        "ai_relevance": 0.0,
    }
    research_score = score_article(research_article, max_age_hours=48, weights=weights)
    company_score = score_article(company_article, max_age_hours=48, weights=weights)
    assert research_score.total > company_score.total


def test_ranking_agent_caps_articles_per_category(monkeypatch: pytest.MonkeyPatch, now):
    monkeypatch.setenv("RANKING_TOP_STORIES_PER_SECTION", "2")
    articles = [
        make_article(title=f"Global story {i}", category=NewsCategory.GLOBAL, published_at=now)
        for i in range(5)
    ]
    ranked = RankingAgent().run(articles)
    assert len(ranked) == 2
    assert all(a.scores is not None for a in ranked)


def test_ranking_agent_ranks_each_category_independently(now):
    articles = [
        make_article(title="Global 1", category=NewsCategory.GLOBAL, published_at=now),
        make_article(title="Research 1", category=NewsCategory.RESEARCH, published_at=now),
    ]
    ranked = RankingAgent().run(articles)
    categories = {a.category for a in ranked}
    assert categories == {NewsCategory.GLOBAL, NewsCategory.RESEARCH}
