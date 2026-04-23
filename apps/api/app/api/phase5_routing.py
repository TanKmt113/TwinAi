from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Rule
from app.services.routing_context import build_rule_notification_targets, get_escalation_policy_by_id_or_code

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
