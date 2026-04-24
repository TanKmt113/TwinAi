from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_phase5_write_access
from app.core.database import get_db
from app.models import OperationalIncident
from app.services.repositories import AssetRepository
from app.schemas.domain import CreateOperationalIncidentBody, OperationalIncidentRead, WorkflowActorBody
from app.services.operational_incidents import (
    OperationalIncidentError,
    acknowledge_operational_incident,
    create_operational_incident,
    incident_to_read,
    resolve_operational_incident,
)

router = APIRouter(prefix="/api/operational-incidents", tags=["operational-incidents"])


@router.get("", response_model=list[OperationalIncidentRead])
def list_operational_incidents(
    asset_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = select(OperationalIncident).order_by(OperationalIncident.created_at.desc()).limit(limit)
    if asset_id:
        repo = AssetRepository(db)
        asset = repo.get_by_id(asset_id) or repo.get_by_code(asset_id)
        stmt = stmt.where(OperationalIncident.asset_id == (asset.id if asset else asset_id))
    if status:
        stmt = stmt.where(OperationalIncident.status == status)
    rows = list(db.scalars(stmt))
    return [incident_to_read(db, r) for r in rows]


@router.get("/{incident_id}", response_model=OperationalIncidentRead)
def get_operational_incident(incident_id: str, db: Session = Depends(get_db)) -> dict:
    row = db.get(OperationalIncident, incident_id)
    if not row:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident_to_read(db, row)


@router.post("", response_model=OperationalIncidentRead, dependencies=[Depends(require_phase5_write_access)])
def post_operational_incident(body: CreateOperationalIncidentBody, db: Session = Depends(get_db)) -> dict:
    try:
        row = create_operational_incident(
            db,
            asset_id_or_code=body.asset_id,
            incident_kind=body.incident_kind,
            title=body.title,
            description=body.description,
            severity=body.severity,
            actor_type=body.actor_type,
            actor_id=body.actor_id,
        )
    except OperationalIncidentError as exc:
        detail = str(exc)
        code = 404 if detail == "asset_not_found" else 400
        raise HTTPException(status_code=code, detail=detail) from exc
    return incident_to_read(db, row)


@router.post("/{incident_id}/acknowledge", response_model=OperationalIncidentRead, dependencies=[Depends(require_phase5_write_access)])
def post_acknowledge(incident_id: str, body: WorkflowActorBody, db: Session = Depends(get_db)) -> dict:
    try:
        row = acknowledge_operational_incident(
            db,
            incident_id,
            actor_type=body.actor_type,
            actor_id=body.actor_id,
            note=body.note,
        )
    except OperationalIncidentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return incident_to_read(db, row)


@router.post("/{incident_id}/resolve", response_model=OperationalIncidentRead, dependencies=[Depends(require_phase5_write_access)])
def post_resolve(incident_id: str, body: WorkflowActorBody, db: Session = Depends(get_db)) -> dict:
    try:
        row = resolve_operational_incident(
            db,
            incident_id,
            actor_type=body.actor_type,
            actor_id=body.actor_id,
            note=body.note,
        )
    except OperationalIncidentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return incident_to_read(db, row)
