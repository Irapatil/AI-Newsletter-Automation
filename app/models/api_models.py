"""Request/response schemas for the FastAPI layer."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RootResponse(BaseModel):
    name: str
    version: str
    description: str
    docs_url: str


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str


class GenerateNewsletterRequest(BaseModel):
    """Optional trigger payload. Power Automate may POST an empty body."""

    force_refresh: bool = Field(
        default=False,
        description="If true, bypass the deduplication cache against prior history.",
    )
    requested_by: str | None = Field(
        default=None, description="Caller identifier for audit logging."
    )


class NewsletterResponse(BaseModel):
    """Newsletter payload consumed by Power Automate to compose the Outlook email."""

    model_config = ConfigDict(populate_by_name=True)

    subject: str
    summary: str
    html: str
    markdown: str
    json_data: dict = Field(alias="json")
    timestamp: datetime


class NewsletterHistoryItem(BaseModel):
    id: str
    subject: str
    timestamp: datetime


class NewsletterHistoryResponse(BaseModel):
    items: list[NewsletterHistoryItem]
    count: int


class ErrorResponse(BaseModel):
    detail: str
