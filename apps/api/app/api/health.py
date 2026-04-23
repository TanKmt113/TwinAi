from fastapi import APIRouter

from app.core.config import get_settings
from app.services.health import check_dependencies
from app.services.system_health import check_services_status

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


@router.get("/health/services")
def services_health() -> dict:
    """Live checks (TCP/HTTP) so the dashboard can show which backends are reachable."""
    return check_services_status()

