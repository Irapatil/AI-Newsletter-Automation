"""Tests for HTMLFormatterAgent: HTML/Markdown/JSON rendering of newsletter content."""

from __future__ import annotations

from datetime import datetime

from app.agents.html_formatter_agent import HTMLFormatterAgent
from app.config.settings import get_settings
from app.models.article import Article
from app.models.newsletter import NewsletterContent, NewsletterOutput, NewsletterSection
from tests.conftest import make_article


def _make_content(
    *, sections: list[NewsletterSection] | None = None, now: datetime
) -> NewsletterContent:
    return NewsletterContent(
        subject="Your Daily AI Briefing",
        executive_summary="A concise recap of the most important AI developments today.",
        sections=sections if sections is not None else [],
        one_thing_to_watch="Watch for the next foundation model release.",
        generated_at=now,
    )


def _make_section(article: Article) -> NewsletterSection:
    return NewsletterSection(
        key="global_news",
        title="🌍 Global AI News",
        articles=[article],
    )


def test_run_renders_populated_content_to_html_markdown_and_json(now: datetime) -> None:
    article = make_article(
        title="OpenAI announces breakthrough model",
        url="https://a.com/1",
        published_at=now,
    )
    content = _make_content(sections=[_make_section(article)], now=now)
    sender_name = get_settings().newsletter_sender_name

    output = HTMLFormatterAgent().run(content)

    assert isinstance(output, NewsletterOutput)

    # HTML contains the article title and the configured sender name.
    assert article.title in output.html
    assert sender_name in output.html

    # Markdown also contains the article title.
    assert article.title in output.markdown

    # JSON payload round-trips subject/executive_summary correctly.
    assert output.json_payload["subject"] == content.subject
    assert output.json_payload["executive_summary"] == content.executive_summary

    # Top-level output fields mirror the source content.
    assert output.subject == content.subject
    assert output.summary == content.executive_summary
    assert output.timestamp == content.generated_at


def test_run_with_no_sections_still_renders_without_raising(now: datetime) -> None:
    content = _make_content(sections=[], now=now)

    output = HTMLFormatterAgent().run(content)

    assert isinstance(output, NewsletterOutput)
    assert output.html
    assert output.markdown
    assert content.subject in output.html
    assert content.subject in output.markdown
    assert content.executive_summary in output.html
    assert content.executive_summary in output.markdown
    assert output.json_payload["sections"] == []


def test_html_output_has_no_unrendered_jinja_syntax(now: datetime) -> None:
    article = make_article(title="Novel benchmark dataset for LLM reasoning", published_at=now)
    content = _make_content(sections=[_make_section(article)], now=now)

    output = HTMLFormatterAgent().run(content)

    assert "{{" not in output.html
    assert "}}" not in output.html
    assert "{%" not in output.html
    assert "%}" not in output.html
