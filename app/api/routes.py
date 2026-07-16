"""HTTP routes exposed by the AI Newsletter Automation API.

Endpoints are grouped into five Swagger tags:

- **System** - service metadata (`GET /`).
- **Health** - liveness + per-integration configuration status (`GET /health`).
- **Newsletter** - the production pipeline trigger and its persisted output
  (`POST /generate-newsletter`, `GET /newsletter/latest`,
  `GET /newsletter/latest/html`, `GET /newsletter/history`). This is the
  contract Microsoft Power Automate's daily flow calls.
- **Demo** - a Swagger-friendly companion endpoint for live walkthroughs
  (`POST /demo/generate`), returning a smaller payload plus a link to the
  HTML preview instead of embedding the full HTML inline.
- **Integration** - real Outlook delivery status, reported by Power Automate
  (`POST /integration/outlook/status`) and polled by the frontend
  (`GET /integration/outlook/status`).
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse

from app.api.dependencies import verify_api_key
from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.graph.workflow import get_compiled_workflow
from app.models.api_models import (
    DemoGenerateResponse,
    ErrorResponse,
    GenerateNewsletterRequest,
    HealthResponse,
    NewsletterHistoryResponse,
    NewsletterResponse,
    OutlookDeliveryStatus,
    OutlookDeliveryStatusUpdate,
    RootResponse,
)
from app.models.newsletter import NewsletterOutput, NewsletterStats, TokenUsage
from app.models.state import build_initial_state
from app.services import history_service, outlook_status_service
from app.utils.text_utils import estimate_token_usage_and_cost

logger = get_logger(__name__)

router = APIRouter()

API_VERSION = "1.0.0"


def _to_response(output: NewsletterOutput) -> NewsletterResponse:
    return NewsletterResponse(
        subject=output.subject,
        summary=output.summary,
        generated_at=output.timestamp,
        execution_time_seconds=output.execution_time_seconds,
        newsletter_html=output.html,
        newsletter_markdown=output.markdown,
        newsletter_json=output.json_payload,
        statistics=output.stats,
        sources_used=output.sources_used,
        agent_execution=output.agent_execution,
        provider=output.provider,
        status=output.run_status,
        token_usage=output.token_usage,
        estimated_cost_usd=output.estimated_cost_usd,
        errors=output.errors,
    )


def _provider_statuses() -> dict[str, str]:
    """Best-effort, call-free status per integration, derived from settings
    that are already loaded (no outbound network calls - this is a cheap
    liveness/config check, not a deep health probe of each provider).
    """
    settings = get_settings()
    langgraph_status = "operational"
    try:
        get_compiled_workflow()
    except Exception:  # noqa: BLE001 - report, don't crash the health check
        langgraph_status = "error"

    return {
        "api": "ok",
        "openai": "mock" if settings.uses_mock_llm else "configured",
        "newsapi": (
            "configured" if settings.newsapi_api_key.get_secret_value() else "not_configured"
        ),
        "github": "authenticated" if settings.github_token.get_secret_value() else "public",
        "rss": "available",
        "langgraph": langgraph_status,
    }


async def _run_pipeline_and_build_output(newsletter_id: str) -> NewsletterOutput:
    """Run the LangGraph workflow once and assemble a persisted `NewsletterOutput`.

    Shared by `POST /generate-newsletter` and `POST /demo/generate` so both
    endpoints report identical, correctly-computed statistics/telemetry.
    """
    settings = get_settings()
    workflow = get_compiled_workflow()

    started_at = time.monotonic()
    try:
        final_state = await workflow.ainvoke(build_initial_state())
    except Exception as exc:  # noqa: BLE001 - convert to a clean 502 for the caller
        logger.exception("generate_newsletter_pipeline_crashed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Newsletter pipeline failed to run; see server logs for details",
        ) from exc
    execution_time_seconds = round(time.monotonic() - started_at, 3)

    content = final_state.get("newsletter_content")
    if content is None:
        # `no_content_fallback` always produces a non-None NewsletterContent
        # when there's simply nothing to report, so reaching here means an
        # upstream node failed to populate state - a genuine pipeline bug,
        # not a legitimate "quiet news day".
        logger.error("generate_newsletter_no_content", errors=final_state.get("errors", []))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Newsletter pipeline produced no content; see server logs for details",
        )

    errors = final_state.get("errors", [])
    if errors:
        logger.warning("generate_newsletter_completed_with_errors", errors=errors)

    aggregated_articles = final_state.get("aggregated_articles", [])
    aggregated_count = len(aggregated_articles)
    deduplicated_count = len(final_state.get("deduplicated_articles", []))
    ranked_count = len(final_state.get("ranked_news", []))
    stories_selected = sum(len(section.articles) for section in content.sections)

    generated_texts = [content.executive_summary, content.one_thing_to_watch]
    generated_texts += [
        article.ai_summary
        for section in content.sections
        for article in section.articles
        if article.ai_summary
    ]
    tokens, cost_usd = estimate_token_usage_and_cost(
        generated_texts, settings.llm_cost_per_million_tokens_usd
    )

    output = NewsletterOutput(
        subject=content.subject,
        summary=content.executive_summary,
        html=final_state.get("newsletter_html", ""),
        markdown=final_state.get("newsletter_markdown", ""),
        json_payload=final_state.get("newsletter_json", {}),
        timestamp=content.generated_at,
        stats=NewsletterStats(
            aggregated_count=aggregated_count,
            duplicates_removed=max(aggregated_count - deduplicated_count, 0),
            ranked_count=ranked_count,
            stories_selected=stories_selected,
        ),
        agent_execution=final_state.get("agent_execution", []),
        execution_time_seconds=execution_time_seconds,
        provider="mock" if settings.uses_mock_llm else settings.llm_provider,
        run_status="partial_success" if errors else "success",
        sources_used=sorted({article.source for article in aggregated_articles}),
        token_usage=TokenUsage(prompt_and_completion_tokens=tokens),
        estimated_cost_usd=cost_usd,
        errors=errors,
    )
    history_service.save_newsletter(output, newsletter_id)
    return output


@router.get(
    "/",
    response_model=RootResponse,
    tags=["System"],
    summary="Service metadata",
    description="Basic identity/version info for the running API instance. Always public.",
)
async def root() -> RootResponse:
    is_production = get_settings().app_env == "production"
    return RootResponse(
        name="AI Newsletter Automation",
        version=API_VERSION,
        description="Enterprise multi-agent AI newsletter pipeline built with LangGraph and FastAPI.",
        docs_url=None if is_production else "/docs",
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Liveness + integration configuration status",
    description=(
        "Returns overall API liveness plus a per-integration configuration "
        "summary (OpenAI, NewsAPI, GitHub, RSS, LangGraph). No outbound "
        "network calls are made to any provider - this is a cheap, "
        "call-free config/compile check, not a deep health probe. Always "
        "public; used for infra health checks."
    ),
)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(UTC),
        version=API_VERSION,
        providers=_provider_statuses(),
    )


@router.post(
    "/generate-newsletter",
    response_model=NewsletterResponse,
    dependencies=[Depends(verify_api_key)],
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Missing/incorrect `X-API-Key` header.",
            "content": {
                "application/json": {"example": {"detail": "Invalid or missing X-API-Key header"}}
            },
        },
        502: {
            "model": ErrorResponse,
            "description": "The LangGraph pipeline crashed or produced no content.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Newsletter pipeline failed to run; see server logs for details"
                    }
                }
            },
        },
    },
    tags=["Newsletter"],
    summary="Run the full LangGraph pipeline and generate today's newsletter",
    description=(
        "Runs the complete pipeline end-to-end: Orchestrator -> 8 parallel "
        "collector agents (Global News, Company, Funding, Research, Talent, "
        "Policy, Open Source, Model Release) -> Aggregator -> semantic "
        "Deduplication -> Ranking -> Newsletter Generator (GPT "
        "summarization) -> HTML Formatter -> persisted to history. "
        "This is the endpoint Microsoft Power Automate's daily trigger "
        'calls; the response feeds directly into the Outlook "Send an '
        'email" action (see docs/POWER_AUTOMATE.md). A run typically takes '
        '15-40 seconds. Returns `200` with `status: "partial_success"` '
        "(not an error) if one or more collectors failed but the pipeline "
        "still produced a newsletter from the remaining sources."
    ),
)
async def generate_newsletter(
    payload: GenerateNewsletterRequest | None = None,
) -> NewsletterResponse:
    request = payload or GenerateNewsletterRequest()
    logger.info("generate_newsletter_requested", requested_by=request.requested_by)
    output = await _run_pipeline_and_build_output(uuid.uuid4().hex[:12])
    return _to_response(output)


@router.get(
    "/newsletter/latest",
    response_model=NewsletterResponse,
    dependencies=[Depends(verify_api_key)],
    responses={
        404: {
            "model": ErrorResponse,
            "description": "No newsletter has ever been generated.",
            "content": {
                "application/json": {"example": {"detail": "No newsletter has been generated yet"}}
            },
        }
    },
    tags=["Newsletter"],
    summary="Fetch the most recently generated newsletter",
    description="Returns the same payload shape as `POST /generate-newsletter`, "
    "read from persisted history rather than triggering a new run.",
)
async def newsletter_latest() -> NewsletterResponse:
    output = history_service.get_latest()
    if output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No newsletter has been generated yet"
        )
    return _to_response(output)


@router.get(
    "/newsletter/latest/html",
    response_class=HTMLResponse,
    dependencies=[Depends(verify_api_key)],
    responses={
        200: {
            "content": {"text/html": {}},
            "description": "The rendered newsletter, as a standalone HTML document.",
        },
        404: {
            "model": ErrorResponse,
            "description": "No newsletter has ever been generated.",
        },
    },
    tags=["Newsletter"],
    summary="View the latest newsletter as rendered HTML",
    description=(
        "Returns the latest newsletter's HTML directly (`Content-Type: "
        "text/html`), rather than wrapped in a JSON envelope - open "
        "`http://localhost:8000/newsletter/latest/html` in a browser to see "
        "the rendered email exactly as Outlook would display it."
    ),
)
async def newsletter_latest_html() -> HTMLResponse:
    output = history_service.get_latest()
    if output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No newsletter has been generated yet"
        )
    return HTMLResponse(content=output.html)


@router.get(
    "/newsletter/history",
    response_model=NewsletterHistoryResponse,
    dependencies=[Depends(verify_api_key)],
    responses={
        401: {"model": ErrorResponse},
        422: {
            "description": "`limit` is out of range (must be between 1 and 100). "
            "FastAPI's standard validation-error shape - not `ErrorResponse`.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "less_than_equal",
                                "loc": ["query", "limit"],
                                "msg": "Input should be less than or equal to 100",
                                "input": "500",
                            }
                        ]
                    }
                }
            },
        },
    },
    tags=["Newsletter"],
    summary="List previously generated newsletters",
    description="Returns metadata (id, subject, timestamp) for past editions, newest first. "
    "Only the single latest edition's full content is retrievable "
    "(`GET /newsletter/latest`) - there is no per-edition detail endpoint.",
)
async def newsletter_history(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of editions to return.",
        examples=[20],
    ),
) -> NewsletterHistoryResponse:
    items = history_service.list_history(limit=limit)
    return NewsletterHistoryResponse(items=items, count=len(items))


@router.post(
    "/demo/generate",
    response_model=DemoGenerateResponse,
    dependencies=[Depends(verify_api_key)],
    responses={
        401: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
    tags=["Demo"],
    summary="Swagger-friendly companion: generate a newsletter and return a compact report",
    description=(
        "Functionally identical pipeline run to `POST /generate-newsletter` "
        "(same LangGraph workflow, same persistence to history), but returns "
        "a smaller, Swagger-friendly payload: subject, timing, LangGraph "
        "execution report, statistics, sources used, and cost estimate - "
        "without the large inline HTML blob. Pair with "
        "`GET /newsletter/latest/html` to view the rendered result in a "
        "browser. Intended for live walkthroughs, not for Power Automate "
        "(use `POST /generate-newsletter` for that integration)."
    ),
)
async def demo_generate() -> DemoGenerateResponse:
    output = await _run_pipeline_and_build_output(uuid.uuid4().hex[:12])
    return DemoGenerateResponse(
        subject=output.subject,
        generated_at=output.timestamp,
        execution_time_seconds=output.execution_time_seconds,
        provider=output.provider,
        status=output.run_status,
        statistics=output.stats,
        sources_used=output.sources_used,
        agent_execution=output.agent_execution,
        token_usage=output.token_usage,
        estimated_cost_usd=output.estimated_cost_usd,
        newsletter_markdown=output.markdown,
        html_preview_url="/newsletter/latest/html",
        errors=output.errors,
    )


@router.post(
    "/integration/outlook/status",
    response_model=OutlookDeliveryStatus,
    dependencies=[Depends(verify_api_key)],
    responses={401: {"model": ErrorResponse}},
    tags=["Integration"],
    summary="Record the outcome of a Power Automate Outlook send",
    description=(
        "Called by the Power Automate flow immediately after its "
        '"Send an email (V2)" action completes, reporting real delivery '
        "status back to this API - see docs/POWER_AUTOMATE.md for the exact "
        "flow action configuration. The status this stores is what "
        "`GET /integration/outlook/status` (polled by the frontend) reads "
        "back; there is no mocked or simulated delivery state."
    ),
)
async def update_outlook_delivery_status(
    payload: OutlookDeliveryStatusUpdate,
) -> OutlookDeliveryStatus:
    status_record = OutlookDeliveryStatus(
        delivery_status=payload.status,
        last_delivery_time=payload.timestamp,
        message_id=payload.message_id,
        recipient_count=payload.recipient_count,
    )
    outlook_status_service.save_status(status_record)
    return status_record


@router.get(
    "/integration/outlook/status",
    response_model=OutlookDeliveryStatus,
    tags=["Integration"],
    summary="Current Outlook delivery status",
    description=(
        "Returns the most recent delivery status reported by Power Automate "
        'via `POST /integration/outlook/status`. Defaults to `"pending"` '
        "with no timestamp/message id until the first real callback arrives "
        "- this is the call-free, always-public status the frontend polls "
        "every 30 seconds to show real Outlook delivery state instead of a "
        "hardcoded label."
    ),
)
async def get_outlook_delivery_status() -> OutlookDeliveryStatus:
    return outlook_status_service.load_status()
