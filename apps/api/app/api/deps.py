"""FastAPI dependencies (Phase 05+)."""

from fastapi import Depends, Header, HTTPException

from app.core.config import Settings, get_settings


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
