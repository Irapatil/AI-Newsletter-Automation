"""HTTP routes exposed by the AI Newsletter Automation API."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import verify_api_key
from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.graph.workflow import get_compiled_workflow
from app.models.api_models import (
    ErrorResponse,
    GenerateNewsletterRequest,
    HealthResponse,
    NewsletterHistoryResponse,
    NewsletterResponse,
    RootResponse,
)
from app.models.newsletter import NewsletterOutput
from app.models.state import build_initial_state
from app.services import history_service

logger = get_logger(__name__)

router = APIRouter()

API_VERSION = "1.0.0"


def _to_response(output: NewsletterOutput, errors: list[str] | None = None) -> NewsletterResponse:
    return NewsletterResponse(
        subject=output.subject,
        summary=output.summary,
        html=output.html,
        markdown=output.markdown,
        json=output.json_payload,
        timestamp=output.timestamp,
        errors=errors or [],
    )


@router.get("/", response_model=RootResponse, tags=["meta"])
async def root() -> RootResponse:
    is_production = get_settings().app_env == "production"
    return RootResponse(
        name="AI Newsletter Automation",
        version=API_VERSION,
        description="Enterprise multi-agent AI newsletter pipeline built with LangGraph and FastAPI.",
        docs_url=None if is_production else "/docs",
    )


@router.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.now(UTC), version=API_VERSION)


@router.post(
    "/generate-newsletter",
    response_model=NewsletterResponse,
    dependencies=[Depends(verify_api_key)],
    responses={401: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    tags=["newsletter"],
)
async def generate_newsletter(
    payload: GenerateNewsletterRequest | None = None,
) -> NewsletterResponse:
    """Run the full LangGraph pipeline and return the generated newsletter.

    This is the endpoint Microsoft Power Automate calls on the daily
    trigger; the response feeds directly into the Outlook "Send an email"
    action (see docs/POWER_AUTOMATE.md).
    """
    request = payload or GenerateNewsletterRequest()
    logger.info("generate_newsletter_requested", requested_by=request.requested_by)

    workflow = get_compiled_workflow()
    try:
        final_state = await workflow.ainvoke(build_initial_state())
    except Exception as exc:  # noqa: BLE001 - convert to a clean 502 for the caller
        logger.exception("generate_newsletter_pipeline_crashed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Newsletter pipeline failed to run; see server logs for details",
        ) from exc

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

    output = NewsletterOutput(
        subject=content.subject,
        summary=content.executive_summary,
        html=final_state.get("newsletter_html", ""),
        markdown=final_state.get("newsletter_markdown", ""),
        json_payload=final_state.get("newsletter_json", {}),
        timestamp=content.generated_at,
    )
    history_service.save_newsletter(output, uuid.uuid4().hex[:12])

    return _to_response(output, errors=errors)


@router.get(
    "/newsletter/latest",
    response_model=NewsletterResponse,
    dependencies=[Depends(verify_api_key)],
    responses={404: {"model": ErrorResponse}},
    tags=["newsletter"],
)
async def newsletter_latest() -> NewsletterResponse:
    output = history_service.get_latest()
    if output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No newsletter has been generated yet"
        )
    return _to_response(output)


@router.get(
    "/newsletter/history",
    response_model=NewsletterHistoryResponse,
    dependencies=[Depends(verify_api_key)],
    responses={401: {"model": ErrorResponse}},
    tags=["newsletter"],
)
async def newsletter_history(
    limit: int = Query(default=20, ge=1, le=100),
) -> NewsletterHistoryResponse:
    items = history_service.list_history(limit=limit)
    return NewsletterHistoryResponse(items=items, count=len(items))
