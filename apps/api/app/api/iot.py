"""API tiếp nhận telemetry IoT (Phase 5+)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_iot_ingest_secret
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.schemas.domain import IoTIngestResponse, IoTTelemetryIngestBody
from app.services.iot_ingest import process_iot_telemetry
from app.services.operational_incidents import OperationalIncidentError

router = APIRouter(prefix="/api/iot", tags=["iot"])


@router.post("/telemetry", response_model=IoTIngestResponse, dependencies=[Depends(require_iot_ingest_secret)])
def post_iot_telemetry(
    body: IoTTelemetryIngestBody,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> IoTIngestResponse:
    """Thiết bị gửi metric → đánh giá ngưỡng → có thể tạo operational_incident + n8n như luồng thủ công."""
    try:
        payload = process_iot_telemetry(db, body, settings)
        return IoTIngestResponse(**payload)
    except OperationalIncidentError as exc:
        detail = str(exc)
        status = 404 if detail == "asset_not_found" else 400
        raise HTTPException(status_code=status, detail=detail) from exc
