"""Tests for LLM-driven newsletter assembly (summaries, exec summary, subject, sections)."""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.agents.newsletter_generator_agent import NewsletterGeneratorAgent
from app.models.article import Article, ArticleScores, NewsCategory
from app.models.newsletter import SECTION_TITLES
from app.services.llm_service import MockLLMService


def _scored(article: Article, total: float) -> Article:
    article.scores = ArticleScores(total=total)
    return article


@pytest.fixture
def ranked_articles(article_factory, now) -> list[Article]:
    return [
        _scored(
            article_factory(
                title="OpenAI announces breakthrough model",
                url="https://a.com/1",
                source="TechCrunch AI",
                category=NewsCategory.GLOBAL,
                published_at=now,
                snippet="OpenAI unveils a major new AI model breakthrough.",
            ),
            0.9,
        ),
        _scored(
            article_factory(
                title="Startup raises Series B for AI research",
                url="https://a.com/2",
                source="VentureBeat AI",
                category=NewsCategory.GLOBAL,
                published_at=now - timedelta(hours=1),
                snippet="A well-funded startup expands its research team.",
            ),
            0.4,
        ),
        _scored(
            article_factory(
                title="Novel benchmark dataset for LLM reasoning",
                url="https://arxiv.org/abs/1",
                source="arXiv",
                category=NewsCategory.RESEARCH,
                published_at=now - timedelta(hours=5),
                snippet="A state-of-the-art benchmark dataset.",
            ),
            0.6,
        ),
    ]


@pytest.mark.asyncio
async def test_run_builds_sections_grouped_by_category(ranked_articles):
    agent = NewsletterGeneratorAgent(llm_service=MockLLMService())
    content = await agent.run(ranked_articles)

    section_keys = [section.key for section in content.sections]
    assert set(section_keys) == {"global_news", "research"}
    # SECTION_ORDER puts global_news before research.
    assert section_keys == ["global_news", "research"]

    for section in content.sections:
        assert section.title == SECTION_TITLES[section.key]

    global_section = next(s for s in content.sections if s.key == "global_news")
    assert {a.url for a in global_section.articles} == {"https://a.com/1", "https://a.com/2"}
    # Within a section, articles should be sorted by total score, descending.
    assert [a.url for a in global_section.articles] == ["https://a.com/1", "https://a.com/2"]

    research_section = next(s for s in content.sections if s.key == "research")
    assert [a.url for a in research_section.articles] == ["https://arxiv.org/abs/1"]


@pytest.mark.asyncio
async def test_run_populates_ai_summary_for_every_article(ranked_articles):
    agent = NewsletterGeneratorAgent(llm_service=MockLLMService())
    content = await agent.run(ranked_articles)

    all_articles = [a for section in content.sections for a in section.articles]
    assert len(all_articles) == len(ranked_articles)
    for article in all_articles:
        assert article.ai_summary
        assert isinstance(article.ai_summary, str)


@pytest.mark.asyncio
async def test_run_produces_nonempty_subject_and_executive_summary(ranked_articles):
    agent = NewsletterGeneratorAgent(llm_service=MockLLMService())
    content = await agent.run(ranked_articles)

    assert isinstance(content.subject, str) and content.subject.strip()
    assert isinstance(content.executive_summary, str) and content.executive_summary.strip()
    assert isinstance(content.one_thing_to_watch, str) and content.one_thing_to_watch.strip()
    # The subject line should reference the top-scored article's headline in some form.
    assert "|" in content.subject


@pytest.mark.asyncio
async def test_run_empty_article_list_returns_fallback_content():
    agent = NewsletterGeneratorAgent(llm_service=MockLLMService())
    content = await agent.run([])

    assert content.sections == []
    assert content.subject.startswith("AI Newsletter - ")
    assert content.executive_summary == (
        "No significant AI developments were detected in the last collection window."
    )
    assert content.one_thing_to_watch == "No standout story to highlight today."
    assert content.generated_at is not None


def test_apply_global_cap_reserves_one_article_per_category_before_trimming(
    article_factory, now, monkeypatch: pytest.MonkeyPatch
):
    """Regression test for a real bug: when candidates exceed the global cap,
    every present category must keep at least one article - a category-blind
    score cutoff previously could (and once did, due to a since-fixed
    Article.id bug) erase whole sections despite RankingAgent having
    deliberately kept them alive.
    """
    monkeypatch.setenv("NEWSLETTER_MAX_TOTAL_ARTICLES", "10")

    articles = []
    for category in NewsCategory:
        for i in range(5):
            # TALENT's articles all score lower than every other category's,
            # so a pure top-10-by-score cutoff would drop TALENT entirely.
            base_score = 0.1 if category == NewsCategory.TALENT else 0.5
            articles.append(
                _scored(
                    article_factory(
                        title=f"{category.value} story {i}",
                        url=f"https://example.com/{category.value}/{i}",
                        category=category,
                        published_at=now,
                    ),
                    base_score - i * 0.01,
                )
            )

    capped = NewsletterGeneratorAgent._apply_global_cap(articles)

    assert len(capped) == 10
    assert len({a.id for a in capped}) == 10, "capped articles must have unique ids"
    present_categories = {a.category for a in capped}
    assert present_categories == set(NewsCategory), "every category must be represented"


def test_apply_global_cap_no_trim_needed_returns_all(article_factory, now):
    articles = [_scored(article_factory(title="Only story", url="https://example.com/1"), 0.5)]
    capped = NewsletterGeneratorAgent._apply_global_cap(articles)
    assert capped == articles


@pytest.mark.asyncio
async def test_constructor_defaults_to_get_llm_service(monkeypatch):
    """When no llm_service is passed, the agent falls back to get_llm_service()."""
    sentinel = MockLLMService()
    monkeypatch.setattr("app.agents.newsletter_generator_agent.get_llm_service", lambda: sentinel)
    agent = NewsletterGeneratorAgent()
    assert agent._llm is sentinel
