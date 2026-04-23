"""Đăng nhập MVP: OrgUser + password_hash (seed), JWT khi AUTH_ENABLED."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models import OrgUser
from app.schemas.domain import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    if not settings.auth_enabled:
        raise HTTPException(status_code=503, detail="auth_disabled")
    user = db.scalar(select(OrgUser).where(OrgUser.user_code == body.user_code, OrgUser.is_active == True))  # noqa: E712
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    try:
        ok = bcrypt.checkpw(body.password.encode("utf-8"), user.password_hash.encode("utf-8"))
    except ValueError:
        ok = False
    if not ok:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    token = create_access_token(user.user_code, list(user.role_tags or []), settings)
    return TokenResponse(access_token=token, user_code=user.user_code, roles=list(user.role_tags or []))
