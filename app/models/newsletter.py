"""Models describing the assembled newsletter, before and after rendering."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

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


class NewsletterStats(BaseModel):
    """Pipeline counters surfaced for observability/demo purposes.

    Populated from state the pipeline already computes (see
    `app/api/routes.py::generate_newsletter`); defaults to zeros so older
    persisted history files without this field still parse.
    """

    aggregated_count: int = 0
    duplicates_removed: int = 0
    ranked_count: int = 0
    stories_selected: int = 0


class AgentExecutionRecord(BaseModel):
    """One LangGraph node's execution outcome for a single pipeline run.

    Populated by the thin node wrappers in `app/graph/nodes.py` around each
    agent's existing call - pure timing/counting instrumentation, no change
    to what any agent actually does. Only successful node completions are
    recorded here: a raising node's exception still propagates untouched
    (so graph-level retry/error handling behaves exactly as before), and the
    route handler surfaces that failure as a 502 rather than a partial
    execution report.
    """

    node: str
    status: Literal["success"] = "success"
    execution_time_seconds: float
    items_processed: int


class TokenUsage(BaseModel):
    """Best-effort token accounting for the LLM calls made during one run.

    There is no real usage endpoint to query - this is a character-based
    heuristic (~4 chars/token) computed from the actual generated content,
    the same approach used for `estimated_cost_usd`. When the mock LLM
    provider is active, `is_estimated` is still true because there is no
    real token cost to report at all.
    """

    prompt_and_completion_tokens: int
    is_estimated: bool = True


class NewsletterOutput(BaseModel):
    """Final newsletter artifact returned by the API and persisted to history."""

    subject: str
    summary: str
    html: str
    markdown: str
    json_payload: dict = Field(default_factory=dict)
    timestamp: datetime
    stats: NewsletterStats = Field(default_factory=NewsletterStats)
    agent_execution: list[AgentExecutionRecord] = Field(default_factory=list)
    execution_time_seconds: float = 0.0
    provider: str = "mock"
    run_status: Literal["success", "partial_success"] = "success"
    sources_used: list[str] = Field(default_factory=list)
    token_usage: TokenUsage = Field(
        default_factory=lambda: TokenUsage(prompt_and_completion_tokens=0)
    )
    estimated_cost_usd: float = 0.0
    errors: list[str] = Field(default_factory=list)
