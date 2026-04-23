"""Lifecycle purchase request: submit / approve / reject + audit + n8n (Phase 05)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import Asset, Component, InventoryItem, PurchaseRequest
from app.services.neo4j_sync import Neo4jSyncService
from app.services.notification_flow import notify_workflow_event
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
        "first_approved_at": request.first_approved_at.isoformat() if request.first_approved_at else None,
        "first_approved_by": request.first_approved_by,
        "asset_code": asset.code if asset else None,
        "asset_name": asset.name if asset else None,
        "component_code": component.code if component else None,
        "component_name": component.name if component else None,
        "inventory_code": inventory.code if inventory else None,
    }


def _notify(event: str, db: Session, request: PurchaseRequest) -> None:
    payload = _purchase_payload(db, request)
    notify_workflow_event(
        event,
        payload,
        entity_type="purchase_request",
        entity_id=request.id,
    )


def _sync_neo4j(request: PurchaseRequest) -> None:
    Neo4jSyncService().sync_task_and_request(request=request)


def _approve_roles_allowed(
    *,
    needs_dual: bool,
    has_first_approval: bool,
    jwt_roles: set[str],
) -> bool:
    level1 = {"department_head", "team_lead", "approver", "branch_head"}
    level2 = {"final_approver", "executive"}
    if needs_dual and not has_first_approval:
        return bool(jwt_roles & level1)
    if needs_dual and has_first_approval:
        return bool(jwt_roles & level2)
    return bool(jwt_roles & (level1 | level2))


def _enforce_approve_rbac(
    request: PurchaseRequest,
    inventory: InventoryItem | None,
    jwt_roles: list[str] | None,
) -> None:
    if not jwt_roles:
        return
    needs_dual = bool(inventory and inventory.import_required)
    has_first = request.first_approved_at is not None
    roles = set(jwt_roles)
    if not _approve_roles_allowed(needs_dual=needs_dual, has_first_approval=has_first, jwt_roles=roles):
        raise PurchaseWorkflowError("approve_forbidden_role")


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
    jwt_role_tags: list[str] | None = None,
) -> PurchaseRequest:
    repo = ReasoningRepository(db)
    request = db.get(PurchaseRequest, request_id)
    if not request:
        raise PurchaseWorkflowError("purchase_request_not_found")
    if request.status != "waiting_for_approval":
        raise PurchaseWorkflowError(f"invalid_status_for_approve:{request.status}")

    inventory = db.get(InventoryItem, request.inventory_item_id)
    _enforce_approve_rbac(request, inventory, jwt_role_tags)

    needs_dual = bool(inventory and inventory.import_required)

    if needs_dual and request.first_approved_at is None:
        request.first_approved_at = datetime.now(UTC)
        request.first_approved_by = actor_id
        db.flush()
        repo.add_audit(
            action="user_approved_purchase_request_level1",
            entity_type="purchase_request",
            entity_id=request.id,
            reason=note or "Phê duyệt cấp 1 (trưởng bộ phận kỹ thuật).",
            after={"status": request.status, "first_approved_by": actor_id},
            actor_type=actor_type,
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(request)
        _sync_neo4j(request)
        _notify("purchase_request_level1_approved", db, request)
        return request

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
