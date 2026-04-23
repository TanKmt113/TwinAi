"""Org routing MVP: liên hệ gợi ý theo asset/rule và escalation policy (đọc từ DB seed)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, AssetContactAssignment, EscalationPolicy, OrgUser, Rule


def _active_users_with_any_role(db: Session, roles: set[str]) -> list[OrgUser]:
    users = list(db.scalars(select(OrgUser).where(OrgUser.is_active == True).order_by(OrgUser.user_code)))  # noqa: E712
    picked: list[OrgUser] = []
    for user in users:
        tags = set(user.role_tags or [])
        if tags.intersection(roles):
            picked.append(user)
    return picked


def _first_assigned_contact(
    db: Session,
    asset_id: str,
    contact_kind: str,
    *,
    exclude_user_id: str | None,
) -> OrgUser | None:
    stmt = (
        select(OrgUser)
        .join(AssetContactAssignment, AssetContactAssignment.org_user_id == OrgUser.id)
        .where(
            AssetContactAssignment.asset_id == asset_id,
            AssetContactAssignment.contact_kind == contact_kind,
            OrgUser.is_active == True,  # noqa: E712
        )
        .order_by(AssetContactAssignment.sort_order, OrgUser.user_code)
    )
    for user in db.scalars(stmt):
        if exclude_user_id and user.id == exclude_user_id:
            continue
        return user
    return None


def build_asset_contacts(db: Session, asset: Asset) -> dict[str, Any]:
    primary_roles = {"technician", "field"}
    backup_roles = {"department_head", "team_lead", "branch_head"}

    primary = _first_assigned_contact(db, asset.id, "primary", exclude_user_id=None)
    primary_source = "asset_assignment" if primary else "role_fallback"
    if not primary:
        primary_candidates = _active_users_with_any_role(db, primary_roles)
        primary = primary_candidates[0] if primary_candidates else None
        primary_source = "role_fallback" if primary else "none"

    backup = _first_assigned_contact(db, asset.id, "backup", exclude_user_id=primary.id if primary else None)
    backup_source = "asset_assignment" if backup else "role_fallback"
    if not backup:
        backup_candidates = _active_users_with_any_role(db, backup_roles)
        backup = next((u for u in backup_candidates if primary is None or u.id != primary.id), None)
        backup_source = "role_fallback" if backup else "none"

    policy = db.scalar(select(EscalationPolicy).where(EscalationPolicy.code == "ELV-CABLE-ESCALATION-01"))
    missing_notification_routing = primary_source == "none" or backup_source == "none"

    return {
        "asset_id": asset.id,
        "asset_code": asset.code,
        "asset_name": asset.name,
        "department_owner": asset.department_owner,
        "primary_contact": _user_brief(primary),
        "backup_contact": _user_brief(backup),
        "escalation_policy_code": policy.code if policy else None,
        "escalation_policy_name": policy.name if policy else None,
        "contact_resolution": {
            "primary_source": primary_source,
            "backup_source": backup_source,
        },
        "missing_notification_routing": missing_notification_routing,
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


def evaluate_escalation_due(
    db: Session,
    policy: EscalationPolicy,
    *,
    opened_at: datetime,
    acknowledged_at: datetime | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """So sánh thời điểm mở alert/task với acknowledge_minutes trong policy (SLA MVP)."""
    now = now or datetime.now(UTC)
    opened_at = opened_at if opened_at.tzinfo else opened_at.replace(tzinfo=UTC)
    if acknowledged_at is not None:
        acknowledged_at = acknowledged_at if acknowledged_at.tzinfo else acknowledged_at.replace(tzinfo=UTC)

    cfg = policy.config_json or {}
    ack_min = int(cfg.get("acknowledge_minutes", 30))

    if acknowledged_at is not None:
        return {
            "should_escalate": False,
            "reason": "already_acknowledged",
            "minutes_open": round((acknowledged_at - opened_at).total_seconds() / 60, 2),
            "acknowledge_sla_minutes": ack_min,
            "suggested_escalation_contacts": [],
        }

    minutes_open = max(0.0, (now - opened_at).total_seconds() / 60)
    should = minutes_open >= ack_min
    esc_roles = {str(r) for r in (cfg.get("escalate_to_roles") or ["branch_head", "executive"])}
    escalate_users = _active_users_with_any_role(db, esc_roles)
    return {
        "should_escalate": should,
        "reason": "sla_exceeded" if should else "within_sla",
        "minutes_open": round(minutes_open, 2),
        "acknowledge_sla_minutes": ack_min,
        "suggested_escalation_contacts": [_user_brief(u) for u in escalate_users],
    }
