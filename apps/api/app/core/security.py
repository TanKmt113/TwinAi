"""JWT helpers (MVP — bật khi AUTH_ENABLED)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config import Settings


def create_access_token(user_code: str, roles: list[str], settings: Settings) -> str:
    secret = (settings.jwt_secret or "").strip()
    if not secret:
        raise RuntimeError("JWT_SECRET is required when issuing tokens.")
    exp = datetime.now(UTC) + timedelta(hours=settings.jwt_expire_hours)
    payload: dict[str, Any] = {"sub": user_code, "roles": roles, "exp": exp}
    return jwt.encode(payload, secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> dict[str, Any] | None:
    secret = (settings.jwt_secret or "").strip()
    if not secret:
        return None
    try:
        return jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
