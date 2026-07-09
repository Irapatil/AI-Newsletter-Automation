"""FastAPI dependencies (auth) shared across routes."""

from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from app.config.settings import get_settings


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Validate the `X-API-Key` header against `API_AUTH_TOKEN`.

    Auth is skipped entirely when `API_AUTH_TOKEN` is unset, so local
    development and CI never need a secret configured. `Settings` refuses to
    load with an empty token when `APP_ENV=production`, so this fallback only
    ever applies to development/test environments.
    """
    settings = get_settings()
    token = settings.api_auth_token.get_secret_value()
    if not token:
        return
    if not secrets.compare_digest(x_api_key or "", token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header",
        )
