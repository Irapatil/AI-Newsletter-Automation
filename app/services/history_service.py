"""Filesystem-backed persistence for generated newsletters.

Each generated newsletter is written as a timestamped JSON file under
`NEWSLETTER_HISTORY_DIR`, which backs the `/newsletter/latest` and
`/newsletter/history` API endpoints.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.models.api_models import NewsletterHistoryItem
from app.models.newsletter import NewsletterOutput

logger = get_logger(__name__)


def _history_dir() -> Path:
    directory = Path(get_settings().newsletter_history_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _slugify_timestamp(timestamp: datetime) -> str:
    return timestamp.strftime("%Y%m%dT%H%M%SZ")


def save_newsletter(output: NewsletterOutput, newsletter_id: str) -> Path:
    directory = _history_dir()
    filename = f"{_slugify_timestamp(output.timestamp)}_{newsletter_id}.json"
    path = directory / filename
    payload = {"id": newsletter_id, **output.model_dump(mode="json")}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("newsletter_saved", path=str(path))
    return path


def _sorted_history_files() -> list[Path]:
    return sorted(_history_dir().glob("*.json"), reverse=True)


def get_latest() -> NewsletterOutput | None:
    for path in _sorted_history_files():
        output = _load(path)
        if output is not None:
            return output
    return None


def list_history(limit: int = 20) -> list[NewsletterHistoryItem]:
    items: list[NewsletterHistoryItem] = []
    for path in _sorted_history_files()[:limit]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            items.append(
                NewsletterHistoryItem(
                    id=payload["id"],
                    subject=payload["subject"],
                    timestamp=payload["timestamp"],
                )
            )
        except (KeyError, json.JSONDecodeError, ValidationError) as exc:
            logger.warning("history_file_unreadable", path=str(path), error=str(exc))
    return items


def _load(path: Path) -> NewsletterOutput | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload.pop("id", None)
        return NewsletterOutput.model_validate(payload)
    except (KeyError, json.JSONDecodeError, ValidationError) as exc:
        logger.warning("history_file_unreadable", path=str(path), error=str(exc))
        return None
