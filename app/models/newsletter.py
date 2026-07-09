"""Models describing the assembled newsletter, before and after rendering."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.article import Article

SECTION_TITLES: dict[str, str] = {
    "global_news": "🌍 Global AI News",
    "company_news": "🏢 Company Moves",
    "model_releases": "🚀 New Models",
    "funding": "💰 Investments",
    "talent": "👩‍💻 Talent Trends",
    "research": "📚 Research Highlights",
    "opensource": "🔓 Open Source",
    "policy": "⚖ Policy & Regulation",
}

SECTION_ORDER: list[str] = [
    "global_news",
    "company_news",
    "model_releases",
    "funding",
    "talent",
    "research",
    "opensource",
    "policy",
]


class NewsletterSection(BaseModel):
    """One rendered section of the newsletter (e.g. Global AI News)."""

    key: str
    title: str
    articles: list[Article] = Field(default_factory=list)


class NewsletterContent(BaseModel):
    """Structured newsletter content, produced before final rendering."""

    subject: str
    executive_summary: str
    sections: list[NewsletterSection] = Field(default_factory=list)
    one_thing_to_watch: str = ""
    generated_at: datetime


class NewsletterOutput(BaseModel):
    """Final newsletter artifact returned by the API and persisted to history."""

    subject: str
    summary: str
    html: str
    markdown: str
    json_payload: dict = Field(default_factory=dict)
    timestamp: datetime
