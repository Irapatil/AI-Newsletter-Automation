"""Request/response schemas for the FastAPI layer."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RootResponse(BaseModel):
    name: str
    version: str
    description: str
    docs_url: str | None


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str


class GenerateNewsletterRequest(BaseModel):
    """Optional trigger payload. Power Automate may POST an empty body."""

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
    errors: list[str] = Field(
        default_factory=list,
        description="Non-fatal collection/generation errors from this run, if any.",
    )


class NewsletterHistoryItem(BaseModel):
    id: str
    subject: str
    timestamp: datetime


class NewsletterHistoryResponse(BaseModel):
    items: list[NewsletterHistoryItem]
    count: int


class ErrorResponse(BaseModel):
    detail: str
