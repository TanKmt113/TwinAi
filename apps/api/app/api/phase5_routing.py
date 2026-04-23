from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Rule
from app.schemas.domain import EscalationCheckBody, EscalationCheckResponse
from app.services.repositories import ReasoningRepository
from app.services.routing_context import (
    build_rule_notification_targets,
    evaluate_escalation_due,
    get_escalation_policy_by_id_or_code,
)

router = APIRouter(prefix="/api", tags=["routing"])


@router.get("/rules/{rule_id}/notification-targets")
def rule_notification_targets(rule_id: str, db: Session = Depends(get_db)) -> dict:
    rule = db.get(Rule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return build_rule_notification_targets(db, rule)


@router.get("/escalation-policies/{policy_id}")
def get_escalation_policy(policy_id: str, db: Session = Depends(get_db)) -> dict:
    policy = get_escalation_policy_by_id_or_code(db, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Escalation policy not found")
    return {
        "id": policy.id,
        "code": policy.code,
        "name": policy.name,
        "config": policy.config_json,
    }


@router.post("/routing/escalation-check", response_model=EscalationCheckResponse)
def check_escalation(body: EscalationCheckBody, db: Session = Depends(get_db)) -> EscalationCheckResponse:
    policy = get_escalation_policy_by_id_or_code(db, body.policy_code)
    if not policy:
        raise HTTPException(status_code=404, detail="Escalation policy not found")
    evaluated = evaluate_escalation_due(
        db,
        policy,
        opened_at=body.opened_at,
        acknowledged_at=body.acknowledged_at,
    )
    audit_recorded = False
    if not body.dry_run and evaluated["should_escalate"]:
        repo = ReasoningRepository(db)
        repo.add_audit(
            action="escalation_triggered",
            entity_type="asset" if body.asset_id else "escalation_check",
            entity_id=body.asset_id or policy.id,
            reason="SLA acknowledge vượt ngưỡng — kiểm tra escalate.",
            after=evaluated,
            actor_type="system",
            actor_id="escalation_check",
        )
        db.commit()
        audit_recorded = True
    return EscalationCheckResponse(
        should_escalate=evaluated["should_escalate"],
        reason=str(evaluated["reason"]),
        minutes_open=float(evaluated["minutes_open"]),
        acknowledge_sla_minutes=int(evaluated["acknowledge_sla_minutes"]),
        suggested_escalation_contacts=list(evaluated.get("suggested_escalation_contacts") or []),
        audit_recorded=audit_recorded,
    )
