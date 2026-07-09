"""Tests for Article.id default generation.

Regression coverage for a real bug caught by live end-to-end validation:
`id`'s default-generation logic previously lived in a
`field_validator(mode="before")`, which Pydantic v2 never invokes when a
field is left at its default value (no `validate_default=True`) - so every
Article constructed without an explicit `id=` silently got `id=""`, and
every article compared equal on `.id`. Anything keying off `.id` uniqueness
(e.g. NewsletterGeneratorAgent._apply_global_cap's reserved/fill split)
silently broke as a result.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.models.article import Article, make_article_id


def _make(**overrides) -> Article:
    base = {
        "title": "Sample title",
        "url": "https://example.com/a",
        "source": "Test",
        "category": "global_news",
        "published_at": datetime.now(UTC),
    }
    base.update(overrides)
    return Article(**base)


def test_default_id_is_generated_when_not_provided():
    article = _make(url="https://example.com/a", title="A")
    assert article.id
    assert article.id == make_article_id("https://example.com/a", "A")


def test_default_id_differs_for_different_urls():
    first = _make(url="https://example.com/a", title="Same title")
    second = _make(url="https://example.com/b", title="Same title")
    assert first.id != second.id


def test_default_id_is_deterministic_for_the_same_url_and_title():
    first = _make(url="https://example.com/a", title="A")
    second = _make(url="https://example.com/a", title="A")
    assert first.id == second.id


def test_many_default_constructed_articles_all_get_unique_ids():
    articles = [_make(url=f"https://example.com/{i}", title=f"Story {i}") for i in range(20)]
    assert len({a.id for a in articles}) == 20


def test_explicit_id_is_preserved():
    article = _make(id="custom-id-123")
    assert article.id == "custom-id-123"


def test_default_id_falls_back_to_title_when_url_is_empty():
    article = _make(url="", title="Unique fallback title")
    assert article.id == make_article_id("", "Unique fallback title")
    assert article.id
