"""Request/response schemas for the FastAPI layer.

Every model carries a `json_schema_extra` example so Swagger UI's "Example
Value" tab is populated automatically for every endpoint that uses it,
without hand-duplicating examples per route.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.newsletter import AgentExecutionRecord, NewsletterStats, TokenUsage

_EXAMPLE_AGENT_EXECUTION: list[dict[str, Any]] = [
    {
        "node": "Orchestrator",
        "status": "success",
        "execution_time_seconds": 0.0,
        "items_processed": 8,
    },
    {
        "node": "GlobalNewsAgent",
        "status": "success",
        "execution_time_seconds": 4.21,
        "items_processed": 160,
    },
    {
        "node": "CompanyNewsAgent",
        "status": "success",
        "execution_time_seconds": 5.87,
        "items_processed": 639,
    },
    {
        "node": "FundingAgent",
        "status": "success",
        "execution_time_seconds": 3.02,
        "items_processed": 20,
    },
    {
        "node": "ResearchAgent",
        "status": "success",
        "execution_time_seconds": 2.61,
        "items_processed": 25,
    },
    {
        "node": "TalentAgent",
        "status": "success",
        "execution_time_seconds": 4.98,
        "items_processed": 10,
    },
    {
        "node": "PolicyAgent",
        "status": "success",
        "execution_time_seconds": 4.40,
        "items_processed": 94,
    },
    {
        "node": "OpenSourceAgent",
        "status": "success",
        "execution_time_seconds": 3.75,
        "items_processed": 16,
    },
    {
        "node": "ModelReleaseAgent",
        "status": "success",
        "execution_time_seconds": 3.10,
        "items_processed": 309,
    },
    {
        "node": "AggregatorAgent",
        "status": "success",
        "execution_time_seconds": 0.02,
        "items_processed": 1298,
    },
    {
        "node": "DeduplicationAgent",
        "status": "success",
        "execution_time_seconds": 8.44,
        "items_processed": 1106,
    },
    {
        "node": "RankingAgent",
        "status": "success",
        "execution_time_seconds": 0.15,
        "items_processed": 40,
    },
    {
        "node": "NewsletterGeneratorAgent",
        "status": "success",
        "execution_time_seconds": 11.36,
        "items_processed": 24,
    },
    {
        "node": "HTMLFormatterAgent",
        "status": "success",
        "execution_time_seconds": 0.08,
        "items_processed": 24,
    },
]

_EXAMPLE_STATISTICS: dict[str, Any] = {
    "aggregated_count": 1298,
    "duplicates_removed": 192,
    "ranked_count": 40,
    "stories_selected": 24,
}

_EXAMPLE_SOURCES_USED: list[str] = [
    "TechCrunch AI",
    "VentureBeat AI",
    "MIT Technology Review",
    "Reuters AI",
    "The Verge AI",
    "Google News",
    "NewsAPI",
    "arXiv",
    "GitHub Trending",
    "Hugging Face",
    "Greenhouse",
    "Lever",
    "LinkedIn Jobs (mock)",
]


class RootResponse(BaseModel):
    """Basic service metadata - a friendly landing response at `GET /`."""

    name: str
    version: str
    description: str
    docs_url: str | None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "AI Newsletter Automation",
                "version": "1.0.0",
                "description": "Enterprise multi-agent AI newsletter pipeline built with LangGraph and FastAPI.",
                "docs_url": "/docs",
            }
        }
    )


class HealthResponse(BaseModel):
    """Liveness probe plus a call-free, per-integration configuration summary."""

    status: str
    timestamp: datetime
    version: str
    providers: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Per-integration status keyed by provider name (api, openai, newsapi, "
            "github, rss, langgraph). Values are informational strings such as "
            "'configured', 'mock', 'not_configured', 'public', 'authenticated', "
            "'operational', or 'error' - not a liveness guarantee, since none of "
            "these are called during a health check."
        ),
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "timestamp": "2026-07-10T08:00:00Z",
                "version": "1.0.0",
                "providers": {
                    "api": "ok",
                    "openai": "configured",
                    "newsapi": "configured",
                    "github": "authenticated",
                    "rss": "available",
                    "langgraph": "operational",
                },
            }
        }
    )


class GenerateNewsletterRequest(BaseModel):
    """Optional trigger payload. Power Automate may POST an empty body."""

    requested_by: str | None = Field(
        default=None, description="Caller identifier for audit logging."
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"requested_by": "power-automate-daily-trigger"}}
    )


class NewsletterResponse(BaseModel):
    """Full newsletter artifact: content, rendering, and LangGraph execution telemetry.

    This is what `POST /generate-newsletter` and `GET /newsletter/latest`
    return, and what Power Automate's "Parse JSON" step consumes (see
    docs/POWER_AUTOMATE.md for the exact schema).
    """

    subject: str = Field(description="Suggested email subject line.")
    summary: str = Field(description="Executive summary (3-4 sentences).")
    generated_at: datetime = Field(description="Generation timestamp (UTC).")
    execution_time_seconds: float = Field(
        description="Wall-clock time for the full LangGraph run, in seconds."
    )
    newsletter_html: str = Field(description="Full HTML email body.")
    newsletter_markdown: str = Field(
        description="Markdown rendition (for Slack/archival/SharePoint)."
    )
    newsletter_json: dict = Field(
        description="Structured NewsletterContent payload (sections, articles, scores)."
    )
    statistics: NewsletterStats = Field(
        description="Pipeline counters: articles aggregated, duplicates removed, ranked, selected."
    )
    sources_used: list[str] = Field(
        default_factory=list,
        description="Distinct publisher/API source names that contributed at least one article.",
    )
    agent_execution: list[AgentExecutionRecord] = Field(
        default_factory=list,
        description="Per-LangGraph-node execution report: status, timing, items processed, in graph order.",
    )
    provider: str = Field(
        description="Effective LLM provider for this run: openai | azure_openai | mock."
    )
    status: Literal["success", "partial_success"] = Field(
        description="'partial_success' means the newsletter was generated but one or more "
        "collectors failed (see `errors`); still a 200, not a failure."
    )
    token_usage: TokenUsage = Field(description="Best-effort LLM token accounting for this run.")
    estimated_cost_usd: float = Field(
        description="Rough cost estimate for this run's LLM usage, not real billing data."
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Non-fatal collection/generation errors from this run, if any.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "subject": "OpenAI unveils new reasoning model | July 10, 2026",
                "summary": "OpenAI announced a new reasoning-focused model; three AI startups raised "
                "over $500M combined; and the EU published new AI Act guidance for foundation models.",
                "generated_at": "2026-07-10T08:00:12Z",
                "execution_time_seconds": 42.7,
                "newsletter_html": "<!DOCTYPE html><html>...</html>",
                "newsletter_markdown": "# OpenAI unveils new reasoning model...",
                "newsletter_json": {
                    "subject": "OpenAI unveils new reasoning model | July 10, 2026",
                    "sections": [
                        {
                            "key": "global_news",
                            "title": "🌍 Global AI News",
                            "articles": [],
                        }
                    ],
                },
                "statistics": _EXAMPLE_STATISTICS,
                # mypy: pydantic's recursive JsonValue alias is invariant on
                # dict/list value types, so these pre-built example lists
                # (already JSON-serializable at runtime) don't structurally
                # unify with it here - a display-only Swagger example, not
                # a real type mismatch.
                "sources_used": _EXAMPLE_SOURCES_USED,  # type: ignore[dict-item]
                "agent_execution": _EXAMPLE_AGENT_EXECUTION,  # type: ignore[dict-item]
                "provider": "openai",
                "status": "success",
                "token_usage": {"prompt_and_completion_tokens": 18420, "is_estimated": True},
                "estimated_cost_usd": 0.0461,
                "errors": [],
            }
        }
    )


class DemoGenerateResponse(BaseModel):
    """Lightweight, Swagger-friendly companion to `POST /generate-newsletter`.

    Omits the (large) HTML payload in favor of a link to
    `GET /newsletter/latest/html`, so the interview demo response stays
    readable directly in Swagger's response viewer while still surfacing the
    full LangGraph execution report, statistics, and cost estimate.
    """

    subject: str
    generated_at: datetime
    execution_time_seconds: float
    provider: str
    status: Literal["success", "partial_success"]
    statistics: NewsletterStats
    sources_used: list[str] = Field(default_factory=list)
    agent_execution: list[AgentExecutionRecord] = Field(default_factory=list)
    token_usage: TokenUsage
    estimated_cost_usd: float
    newsletter_markdown: str
    html_preview_url: str = Field(
        description="Open this URL in a browser to view the rendered HTML newsletter directly."
    )
    errors: list[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "subject": "OpenAI unveils new reasoning model | July 10, 2026",
                "generated_at": "2026-07-10T08:00:12Z",
                "execution_time_seconds": 42.7,
                "provider": "openai",
                "status": "success",
                "statistics": _EXAMPLE_STATISTICS,
                "sources_used": _EXAMPLE_SOURCES_USED,  # type: ignore[dict-item]
                "agent_execution": _EXAMPLE_AGENT_EXECUTION,  # type: ignore[dict-item]
                "token_usage": {"prompt_and_completion_tokens": 18420, "is_estimated": True},
                "estimated_cost_usd": 0.0461,
                "newsletter_markdown": "# OpenAI unveils new reasoning model...",
                "html_preview_url": "/newsletter/latest/html",
                "errors": [],
            }
        }
    )


class NewsletterHistoryItem(BaseModel):
    id: str
    subject: str
    timestamp: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "4ea3ed0a3f7f",
                "subject": "OpenAI unveils new reasoning model | July 10, 2026",
                "timestamp": "2026-07-10T08:00:12Z",
            }
        }
    )


class NewsletterHistoryResponse(BaseModel):
    items: list[NewsletterHistoryItem]
    count: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "4ea3ed0a3f7f",
                        "subject": "OpenAI unveils new reasoning model | July 10, 2026",
                        "timestamp": "2026-07-10T08:00:12Z",
                    },
                    {
                        "id": "2bd619f26969",
                        "subject": "Anthropic expands Claude enterprise tier | July 9, 2026",
                        "timestamp": "2026-07-09T08:00:07Z",
                    },
                ],
                "count": 2,
            }
        }
    )


class ErrorResponse(BaseModel):
    detail: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"detail": "Invalid or missing X-API-Key header"}}
    )


class OutlookDeliveryStatusUpdate(BaseModel):
    """Payload Power Automate POSTs once its "Send an email (V2)" action completes.

    `status="failed"` is accepted too, so a flow can report a failed send
    (e.g. from a `Configure run after` branch) instead of only ever reporting
    success.
    """

    status: Literal["delivered", "failed"] = Field(
        description="Outcome of the Outlook 'Send an email (V2)' action."
    )
    timestamp: datetime = Field(description="UTC time the send action completed.")
    message_id: str | None = Field(
        default=None,
        description="An identifier for this delivery. The Outlook 'Send an email (V2)' "
        "action does not itself return a message id, so flows typically pass "
        "the run identifier (e.g. `workflow().run.name`) or a generated `guid()`.",
    )
    recipient_count: int | None = Field(
        default=None,
        description="Number of recipients the email was sent to, if the flow computes it "
        "(e.g. from a dynamic distribution list).",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "delivered",
                "timestamp": "2026-07-15T08:01:32Z",
                "message_id": "08DA1F2B4C3E5A6D",
                "recipient_count": 42,
            }
        }
    )


class OutlookDeliveryStatus(BaseModel):
    """Current Outlook delivery status, as last reported by Power Automate.

    Defaults to `delivery_status="pending"` with everything else `None` until
    the first `POST /integration/outlook/status` callback arrives - this is
    the state the frontend shows as "Waiting for scheduled Outlook delivery."
    """

    delivery_status: Literal["pending", "delivered", "failed"] = "pending"
    last_delivery_time: datetime | None = None
    message_id: str | None = None
    recipient_count: int | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "delivery_status": "delivered",
                "last_delivery_time": "2026-07-15T08:01:32Z",
                "message_id": "08DA1F2B4C3E5A6D",
                "recipient_count": 42,
            }
        }
    )
