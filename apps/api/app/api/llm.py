from fastapi import APIRouter

from app.services.llm_health import check_llm_health

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/health")
def llm_health() -> dict:
    return check_llm_health()

