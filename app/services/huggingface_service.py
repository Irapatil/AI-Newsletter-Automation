"""Hugging Face Hub API client used by OpenSourceAgent to surface trending models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TypedDict

from app.config.logging_config import get_logger
from app.config.sources import HUGGINGFACE_MODELS_API
from app.services.http_client import HttpClientError, fetch_json

logger = get_logger(__name__)


class HuggingFaceModel(TypedDict):
    model_id: str
    url: str
    likes: int
    downloads: int
    pipeline_tag: str | None
    last_modified: datetime


async def fetch_trending_models(max_results: int = 15) -> list[HuggingFaceModel]:
    params = {"sort": "likes", "direction": "-1", "limit": str(max_results)}

    try:
        payload = await fetch_json(HUGGINGFACE_MODELS_API, params=params)
    except HttpClientError as exc:
        logger.warning("huggingface_fetch_failed", error=str(exc))
        return []

    models: list[HuggingFaceModel] = []
    for item in payload if isinstance(payload, list) else []:
        model_id = item.get("modelId") or item.get("id") or "unknown"
        try:
            last_modified = datetime.fromisoformat(item["lastModified"].replace("Z", "+00:00"))
        except (KeyError, ValueError, AttributeError):
            last_modified = datetime.now(UTC)
        models.append(
            HuggingFaceModel(
                model_id=model_id,
                url=f"https://huggingface.co/{model_id}",
                likes=item.get("likes", 0),
                downloads=item.get("downloads", 0),
                pipeline_tag=item.get("pipeline_tag"),
                last_modified=last_modified,
            )
        )
    return models
