"""Gửi n8n + ghi audit notification_sent / notification_failed (Phase 05)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Asset, Component, InspectionTask, InventoryItem, PurchaseRequest
from app.services.n8n_webhook import post_n8n_workflow_event
from app.services.repositories import ReasoningRepository


def notify_workflow_event(
    event: str,
    payload: dict[str, Any],
    *,
    entity_type: str,
    entity_id: str,
    actor_type: str = "system",
    actor_id: str = "n8n_webhook",
) -> dict[str, Any]:
    """POST n8n rồi ghi audit; dùng SessionLocal để không phụ thuộc session caller đã commit."""
    result = post_n8n_workflow_event(event, payload)
    with SessionLocal() as db:
        repo = ReasoningRepository(db)
        if result.get("sent"):
            repo.add_audit(
                action="notification_sent",
                entity_type=entity_type,
                entity_id=entity_id,
                reason=f"n8n:{event}",
                after={"event": event, "webhook_result": result},
                actor_type=actor_type,
                actor_id=actor_id,
            )
        elif result.get("skipped"):
            repo.add_audit(
                action="notification_skipped",
                entity_type=entity_type,
                entity_id=entity_id,
                reason=f"n8n không cấu hình URL — bỏ qua {event}",
                after={"event": event, "webhook_result": result},
                actor_type=actor_type,
                actor_id=actor_id,
            )
        else:
            repo.add_audit(
                action="notification_failed",
                entity_type=entity_type,
                entity_id=entity_id,
                reason=f"n8n webhook: {event}",
                after={"webhook_result": result},
                actor_type=actor_type,
                actor_id=actor_id,
            )
        db.commit()
    return result


def dispatch_pending_notifications(pending: list[tuple[str, dict[str, Any], str, str]]) -> None:
    """Chạy sau commit DB: mỗi phần tử là (event, payload, entity_type, entity_id)."""
    for event, payload, entity_type, entity_id in pending:
        notify_workflow_event(event, payload, entity_type=entity_type, entity_id=entity_id)


def build_inspection_task_payload(db: Session, task: InspectionTask) -> dict[str, Any]:
    component = db.get(Component, task.component_id)
    asset = db.get(Asset, component.asset_id) if component else None
    return {
        "task_id": task.id,
        "title": task.title,
        "status": task.status,
        "component_id": task.component_id,
        "component_code": component.code if component else None,
        "asset_id": asset.id if asset else None,
        "asset_code": asset.code if asset else None,
        "asset_name": asset.name if asset else None,
        "rule_id": task.rule_id,
        "created_by_agent": task.created_by_agent,
    }


def build_purchase_request_draft_payload(db: Session, request: PurchaseRequest) -> dict[str, Any]:
    component = db.get(Component, request.component_id)
    asset = db.get(Asset, component.asset_id) if component else None
    inventory = db.get(InventoryItem, request.inventory_item_id)
    return {
        "request_id": request.id,
        "status": request.status,
        "reason": request.reason[:500],
        "approval_policy_code": request.approval_policy_code,
        "final_approver": request.final_approver,
        "asset_code": asset.code if asset else None,
        "asset_name": asset.name if asset else None,
        "component_code": component.code if component else None,
        "inventory_code": inventory.code if inventory else None,
        "created_by_agent": request.created_by_agent,
    }
