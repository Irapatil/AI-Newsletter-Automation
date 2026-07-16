"""FastAPI dependencies (auth) shared across routes."""

from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from app.config.settings import get_settings


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Validate the `X-API-Key` header against `API_AUTH_TOKEN`.

    Auth is enforced only when `APP_ENV=production` - local development,
    staging, CI, and Swagger's "Try it out" never need a secret configured,
    so an `API_AUTH_TOKEN` left over in `.env` from a previous environment
    can't accidentally 401 a dev/demo run. `Settings` refuses to load with an
    empty token when `APP_ENV=production` (see `Settings`'s model validator),
    so production always has a real token to check against here.
    """
    settings = get_settings()
    if settings.app_env != "production":
        return
    token = settings.api_auth_token.get_secret_value()
    if not secrets.compare_digest(x_api_key or "", token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header",
        )
