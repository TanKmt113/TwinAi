from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_jwt_role_tags_if_present, require_phase5_write_access
from app.core.database import get_db
from app.models import Asset, Component, PurchaseRequest
from app.schemas import PurchaseRequestDetailRead, PurchaseRequestRead, WorkflowActorBody
from app.services.purchase_workflow import (
    PurchaseWorkflowError,
    approve_purchase_request,
    cancel_purchase_request,
    reject_purchase_request,
    submit_purchase_request,
)

router = APIRouter(prefix="/api/purchase-requests", tags=["purchase-requests"])


def _to_detail_read(db: Session, row: PurchaseRequest) -> PurchaseRequestDetailRead:
    comp = db.get(Component, row.component_id)
    asset = db.get(Asset, comp.asset_id) if comp else None
    base = PurchaseRequestRead.model_validate(row)
    return PurchaseRequestDetailRead(
        **base.model_dump(mode="json"),
        asset_id=asset.id if asset else None,
        asset_code=asset.code if asset else None,
        component_code=comp.code if comp else None,
    )


@router.get("", response_model=list[PurchaseRequestRead])
def list_purchase_requests(db: Session = Depends(get_db)) -> list[PurchaseRequest]:
    return list(db.scalars(select(PurchaseRequest).order_by(PurchaseRequest.created_at.desc())))


@router.get("/{request_id}", response_model=PurchaseRequestDetailRead)
def get_purchase_request(request_id: str, db: Session = Depends(get_db)) -> PurchaseRequestDetailRead:
    row = db.get(PurchaseRequest, request_id)
    if not row:
        raise HTTPException(status_code=404, detail="Purchase request not found")
    return _to_detail_read(db, row)


@router.post("/{request_id}/submit", response_model=PurchaseRequestRead, dependencies=[Depends(require_phase5_write_access)])
def submit_request(request_id: str, body: WorkflowActorBody, db: Session = Depends(get_db)) -> PurchaseRequest:
    try:
        return submit_purchase_request(
            db,
            request_id,
            actor_type=body.actor_type,
            actor_id=body.actor_id,
            note=body.note,
        )
    except PurchaseWorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{request_id}/approve", response_model=PurchaseRequestRead, dependencies=[Depends(require_phase5_write_access)])
def approve_request(
    request_id: str,
    body: WorkflowActorBody,
    db: Session = Depends(get_db),
    jwt_roles: list[str] | None = Depends(get_jwt_role_tags_if_present),
) -> PurchaseRequest:
    try:
        return approve_purchase_request(
            db,
            request_id,
            actor_type=body.actor_type,
            actor_id=body.actor_id,
            note=body.note,
            jwt_role_tags=jwt_roles,
        )
    except PurchaseWorkflowError as exc:
        detail = str(exc)
        code = 403 if detail == "approve_forbidden_role" else 400
        raise HTTPException(status_code=code, detail=detail) from exc


@router.post("/{request_id}/reject", response_model=PurchaseRequestRead, dependencies=[Depends(require_phase5_write_access)])
def reject_request(request_id: str, body: WorkflowActorBody, db: Session = Depends(get_db)) -> PurchaseRequest:
    try:
        return reject_purchase_request(
            db,
            request_id,
            actor_type=body.actor_type,
            actor_id=body.actor_id,
            note=body.note,
        )
    except PurchaseWorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{request_id}/cancel", response_model=PurchaseRequestRead, dependencies=[Depends(require_phase5_write_access)])
def cancel_request(request_id: str, body: WorkflowActorBody, db: Session = Depends(get_db)) -> PurchaseRequest:
    try:
        return cancel_purchase_request(
            db,
            request_id,
            actor_type=body.actor_type,
            actor_id=body.actor_id,
            note=body.note,
        )
    except PurchaseWorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
