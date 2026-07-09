"""FastAPI dependencies (auth) shared across routes."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.config.settings import get_settings


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Validate the `X-API-Key` header against `API_AUTH_TOKEN`.

    Auth is skipped entirely when `API_AUTH_TOKEN` is unset, so local
    development and CI never need a secret configured.
    """
    settings = get_settings()
    if not settings.api_auth_token:
        return
    if x_api_key != settings.api_auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header",
        )
