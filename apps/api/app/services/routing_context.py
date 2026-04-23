"""Org routing MVP: liên hệ gợi ý theo asset/rule và escalation policy (đọc từ DB seed)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, EscalationPolicy, OrgUser, Rule


def _active_users_with_any_role(db: Session, roles: set[str]) -> list[OrgUser]:
    users = list(db.scalars(select(OrgUser).where(OrgUser.is_active == True).order_by(OrgUser.user_code)))  # noqa: E712
    picked: list[OrgUser] = []
    for user in users:
        tags = set(user.role_tags or [])
        if tags.intersection(roles):
            picked.append(user)
    return picked


def build_asset_contacts(db: Session, asset: Asset) -> dict[str, Any]:
    primary_roles = {"technician", "field"}
    backup_roles = {"department_head", "team_lead", "branch_head"}
    primary_candidates = _active_users_with_any_role(db, primary_roles)
    backup_candidates = _active_users_with_any_role(db, backup_roles)

    primary = primary_candidates[0] if primary_candidates else None
    backup = next((u for u in backup_candidates if primary is None or u.id != primary.id), None)

    policy = db.scalar(select(EscalationPolicy).where(EscalationPolicy.code == "ELV-CABLE-ESCALATION-01"))

    return {
        "asset_id": asset.id,
        "asset_code": asset.code,
        "asset_name": asset.name,
        "department_owner": asset.department_owner,
        "primary_contact": _user_brief(primary),
        "backup_contact": _user_brief(backup),
        "escalation_policy_code": policy.code if policy else None,
        "escalation_policy_name": policy.name if policy else None,
    }


def _user_brief(user: OrgUser | None) -> dict[str, Any] | None:
    if not user:
        return None
    return {
        "user_code": user.user_code,
        "full_name": user.full_name,
        "email": user.email,
        "job_title": user.job_title,
        "role_tags": user.role_tags or [],
    }


def build_rule_notification_targets(db: Session, rule: Rule) -> dict[str, Any]:
    approvers = _active_users_with_any_role(db, {"final_approver", "approver", "executive"})
    field_team = _active_users_with_any_role(db, {"technician", "team_lead", "field"})
    policy = db.scalar(select(EscalationPolicy).where(EscalationPolicy.code == "ELV-CABLE-ESCALATION-01"))

    return {
        "rule_id": rule.id,
        "rule_code": rule.code,
        "rule_name": rule.name,
        "suggested_approvers": [_user_brief(u) for u in approvers],
        "suggested_operational_contacts": [_user_brief(u) for u in field_team],
        "escalation_policy": (
            {"code": policy.code, "name": policy.name, "config": policy.config_json}
            if policy
            else None
        ),
    }


def get_escalation_policy_by_id_or_code(db: Session, policy_id: str) -> EscalationPolicy | None:
    row = db.get(EscalationPolicy, policy_id)
    if row:
        return row
    return db.scalar(select(EscalationPolicy).where(EscalationPolicy.code == policy_id))
