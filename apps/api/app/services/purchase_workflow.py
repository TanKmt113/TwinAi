"""Lifecycle purchase request: submit / approve / reject + audit + n8n (Phase 05)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Asset, Component, InventoryItem, PurchaseRequest
from app.services.neo4j_sync import Neo4jSyncService
from app.services.n8n_webhook import post_n8n_workflow_event
from app.services.repositories import ReasoningRepository


class PurchaseWorkflowError(ValueError):
    """Lỗi nghiệp vụ workflow (HTTP 400)."""


def _purchase_payload(db: Session, request: PurchaseRequest) -> dict[str, Any]:
    component = db.get(Component, request.component_id)
    asset = db.get(Asset, component.asset_id) if component else None
    inventory = db.get(InventoryItem, request.inventory_item_id)
    return {
        "request_id": request.id,
        "status": request.status,
        "reason": request.reason[:500],
        "quantity_requested": request.quantity_requested,
        "approval_policy_code": request.approval_policy_code,
        "final_approver": request.final_approver,
        "asset_code": asset.code if asset else None,
        "asset_name": asset.name if asset else None,
        "component_code": component.code if component else None,
        "component_name": component.name if component else None,
        "inventory_code": inventory.code if inventory else None,
    }


def _notify(event: str, db: Session, request: PurchaseRequest) -> None:
    payload = _purchase_payload(db, request)
    result = post_n8n_workflow_event(event, payload)
    if result.get("sent"):
        return
    with SessionLocal() as log_db:
        ReasoningRepository(log_db).add_audit(
            action="notification_failed",
            entity_type="purchase_request",
            entity_id=request.id,
            reason=f"n8n webhook: {event}",
            after={"webhook_result": result},
            actor_type="system",
            actor_id="n8n_webhook",
        )
        log_db.commit()


def _sync_neo4j(request: PurchaseRequest) -> None:
    Neo4jSyncService().sync_task_and_request(request=request)


def submit_purchase_request(
    db: Session,
    request_id: str,
    *,
    actor_type: str,
    actor_id: str,
    note: str | None = None,
) -> PurchaseRequest:
    repo = ReasoningRepository(db)
    request = db.get(PurchaseRequest, request_id)
    if not request:
        raise PurchaseWorkflowError("purchase_request_not_found")
    if request.status != "draft":
        raise PurchaseWorkflowError(f"invalid_status_for_submit:{request.status}")

    request.status = "waiting_for_approval"
    db.flush()
    repo.add_audit(
        action="user_submitted_purchase_request",
        entity_type="purchase_request",
        entity_id=request.id,
        reason=note or "Người dùng submit đề xuất mua hàng.",
        after={"status": request.status},
        actor_type=actor_type,
        actor_id=actor_id,
    )
    db.commit()
    db.refresh(request)
    _sync_neo4j(request)
    _notify("purchase_request_waiting_for_approval", db, request)
    return request


def approve_purchase_request(
    db: Session,
    request_id: str,
    *,
    actor_type: str,
    actor_id: str,
    note: str | None = None,
) -> PurchaseRequest:
    repo = ReasoningRepository(db)
    request = db.get(PurchaseRequest, request_id)
    if not request:
        raise PurchaseWorkflowError("purchase_request_not_found")
    if request.status != "waiting_for_approval":
        raise PurchaseWorkflowError(f"invalid_status_for_approve:{request.status}")

    request.status = "approved"
    db.flush()
    repo.add_audit(
        action="user_approved_purchase_request",
        entity_type="purchase_request",
        entity_id=request.id,
        reason=note or "Phê duyệt.",
        after={"status": request.status},
        actor_type=actor_type,
        actor_id=actor_id,
    )
    db.commit()
    db.refresh(request)
    _sync_neo4j(request)
    _notify("purchase_request_approved", db, request)
    return request


def reject_purchase_request(
    db: Session,
    request_id: str,
    *,
    actor_type: str,
    actor_id: str,
    note: str | None = None,
) -> PurchaseRequest:
    repo = ReasoningRepository(db)
    request = db.get(PurchaseRequest, request_id)
    if not request:
        raise PurchaseWorkflowError("purchase_request_not_found")
    if request.status != "waiting_for_approval":
        raise PurchaseWorkflowError(f"invalid_status_for_reject:{request.status}")

    request.status = "rejected"
    db.flush()
    repo.add_audit(
        action="user_rejected_purchase_request",
        entity_type="purchase_request",
        entity_id=request.id,
        reason=note or "Từ chối.",
        after={"status": request.status},
        actor_type=actor_type,
        actor_id=actor_id,
    )
    db.commit()
    db.refresh(request)
    _sync_neo4j(request)
    _notify("purchase_request_rejected", db, request)
    return request


def cancel_purchase_request(
    db: Session,
    request_id: str,
    *,
    actor_type: str,
    actor_id: str,
    note: str | None = None,
) -> PurchaseRequest:
    repo = ReasoningRepository(db)
    request = db.get(PurchaseRequest, request_id)
    if not request:
        raise PurchaseWorkflowError("purchase_request_not_found")
    if request.status not in ("draft", "waiting_for_approval"):
        raise PurchaseWorkflowError(f"invalid_status_for_cancel:{request.status}")

    request.status = "cancelled"
    db.flush()
    repo.add_audit(
        action="user_cancelled_purchase_request",
        entity_type="purchase_request",
        entity_id=request.id,
        reason=note or "Huỷ đề xuất.",
        after={"status": request.status},
        actor_type=actor_type,
        actor_id=actor_id,
    )
    db.commit()
    db.refresh(request)
    _sync_neo4j(request)
    _notify("purchase_request_cancelled", db, request)
    return request
