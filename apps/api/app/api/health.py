from fastapi import APIRouter

from app.core.config import get_settings
from app.services.health import check_dependencies

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/health/dependencies")
def dependency_health() -> dict:
    return check_dependencies()

