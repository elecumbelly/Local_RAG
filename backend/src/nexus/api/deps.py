from __future__ import annotations

from fastapi import Header, HTTPException, status

from nexus.config import get_settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """
    Simple API key gate for all routes.

    Rejects requests when the configured key is missing or does not match.
    """
    settings = get_settings()
    if not settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key not configured on server",
        )
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
