"""Filesystem-backed persistence for the latest Outlook delivery status.

Power Automate calls `POST /integration/outlook/status` once its "Send an
email (V2)" action completes; `GET /integration/outlook/status` (polled by
the frontend) reads back the same file, so delivery status survives
backend restarts exactly like newsletter history does.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.models.api_models import OutlookDeliveryStatus

logger = get_logger(__name__)


def _status_file() -> Path:
    path = Path(get_settings().outlook_status_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_status(status: OutlookDeliveryStatus) -> None:
    path = _status_file()
    path.write_text(status.model_dump_json(indent=2), encoding="utf-8")
    logger.info(
        "outlook_delivery_status_updated",
        delivery_status=status.delivery_status,
        message_id=status.message_id,
    )


def load_status() -> OutlookDeliveryStatus:
    path = _status_file()
    if not path.exists():
        return OutlookDeliveryStatus()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return OutlookDeliveryStatus.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("outlook_status_file_unreadable", error=str(exc))
        return OutlookDeliveryStatus()
