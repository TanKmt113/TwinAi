"""FastAPI dependencies (Phase 05+)."""

from fastapi import Depends, Header, HTTPException

from app.core.config import Settings, get_settings
from app.core.security import decode_access_token


def require_phase5_write_secret(
    settings: Settings = Depends(get_settings),
    x_phase5_write_secret: str | None = Header(default=None, alias="X-Phase5-Write-Secret"),
) -> None:
    """Khi PHASE5_WRITE_SECRET được set, mọi POST workflow bắt buộc khớp header (tránh thao tác ẩn danh trên môi trường shared)."""
    expected = (settings.phase5_write_secret or "").strip()
    if not expected:
        return
    if (x_phase5_write_secret or "").strip() != expected:
        raise HTTPException(status_code=403, detail="phase5_write_forbidden")


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization.split(" ", 1)[1].strip() or None


def require_phase5_write_access(
    settings: Settings = Depends(get_settings),
    authorization: str | None = Header(default=None),
    x_phase5_write_secret: str | None = Header(default=None, alias="X-Phase5-Write-Secret"),
) -> None:
    """Cho phép ghi workflow: header secret khớp, hoặc JWT hợp lệ khi AUTH_ENABLED."""
    expected = (settings.phase5_write_secret or "").strip()
    if expected and (x_phase5_write_secret or "").strip() == expected:
        return
    if settings.auth_enabled:
        token = _bearer_token(authorization)
        if token and decode_access_token(token, settings):
            return
        raise HTTPException(status_code=403, detail="phase5_write_forbidden")
    if expected:
        raise HTTPException(status_code=403, detail="phase5_write_forbidden")


def require_iot_ingest_secret(
    settings: Settings = Depends(get_settings),
    x_iot_ingest_secret: str | None = Header(default=None, alias="X-IoT-Ingest-Secret"),
) -> None:
    """Thiết bị IoT gửi telemetry: bắt buộc header khớp IOT_INGEST_SECRET khi biến môi trường đã cấu hình."""
    expected = (settings.iot_ingest_secret or "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="iot_ingest_disabled")
    if (x_iot_ingest_secret or "").strip() != expected:
        raise HTTPException(status_code=403, detail="iot_ingest_forbidden")


def get_jwt_role_tags_if_present(
    settings: Settings = Depends(get_settings),
    authorization: str | None = Header(default=None),
) -> list[str] | None:
    """Trả về role_tags từ Bearer JWT nếu token hợp lệ; None nếu không gửi Bearer hoặc auth tắt."""
    token = _bearer_token(authorization)
    if not token:
        return None
    claims = decode_access_token(token, settings)
    if not claims:
        return None
    return list(claims.get("roles") or [])
