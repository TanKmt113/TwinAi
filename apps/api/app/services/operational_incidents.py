"""Sự cố vận hành: tạo bản ghi + audit + n8n kèm routing liên hệ theo asset."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import Asset, OperationalIncident
from app.schemas.domain import OperationalIncidentRead
from app.services.notification_flow import notify_workflow_event
from app.services.repositories import AssetRepository, ReasoningRepository
from app.services.routing_context import build_asset_contacts

_ALLOWED_KINDS = frozenset(
    {
        "door_fault",
        "elevator_trap",
        "vibration",
        "power_loss",
        "unusual_noise",
        "overspeed",
        "controller_fault",
        "other",
    }
)
_ALLOWED_SEVERITY = frozenset({"info", "warning", "critical"})
_ALLOWED_INCIDENT_SOURCES = frozenset({"operator_ui", "iot_ingest"})


class OperationalIncidentError(ValueError):
    pass


def _resolve_asset(db: Session, asset_id_or_code: str) -> Asset:
    repo = AssetRepository(db)
    asset = repo.get_by_id(asset_id_or_code) or repo.get_by_code(asset_id_or_code)
    if not asset:
        raise OperationalIncidentError("asset_not_found")
    return asset


def build_incident_notification_payload(db: Session, incident: OperationalIncident, asset: Asset) -> dict[str, Any]:
    contacts = build_asset_contacts(db, asset)
    return {
        "incident_id": incident.id,
        "incident_kind": incident.incident_kind,
        "title": incident.title,
        "description": (incident.description or "")[:2000],
        "severity": incident.severity,
        "status": incident.status,
        "asset_id": asset.id,
        "asset_code": asset.code,
        "asset_name": asset.name,
        "location": asset.location,
        "notification_routing": contacts,
        "missing_notification_routing": contacts.get("missing_notification_routing"),
    }


def create_operational_incident(
    db: Session,
    *,
    asset_id_or_code: str,
    incident_kind: str,
    title: str,
    description: str | None,
    severity: str,
    actor_type: str,
    actor_id: str,
    source: str = "operator_ui",
    extra_json: dict[str, Any] | None = None,
) -> OperationalIncident:
    kind = incident_kind.strip().lower()
    if kind not in _ALLOWED_KINDS:
        raise OperationalIncidentError(f"invalid_incident_kind:{incident_kind}")
    sev = severity.strip().lower()
    if sev not in _ALLOWED_SEVERITY:
        raise OperationalIncidentError(f"invalid_severity:{severity}")
    src = source.strip().lower()
    if src not in _ALLOWED_INCIDENT_SOURCES:
        raise OperationalIncidentError(f"invalid_source:{source}")

    asset = _resolve_asset(db, asset_id_or_code.strip())
    extra = extra_json if extra_json is not None else {}
    incident = OperationalIncident(
        asset_id=asset.id,
        incident_kind=kind,
        title=title.strip(),
        description=description.strip() if description else None,
        severity=sev,
        status="open",
        source=src,
        reported_by_actor_type=actor_type,
        reported_by_actor_id=actor_id,
        extra_json=extra,
    )
    db.add(incident)
    db.flush()
    repo = ReasoningRepository(db)
    repo.add_audit(
        action="operational_incident_reported",
        entity_type="operational_incident",
        entity_id=incident.id,
        reason=f"Sự cố vận hành ({kind}) trên {asset.code}: {title.strip()[:200]}",
        after={"asset_code": asset.code, "severity": sev, "source": src},
        actor_type=actor_type,
        actor_id=actor_id,
    )
    db.commit()
    db.refresh(incident)

    payload = build_incident_notification_payload(db, incident, asset)
    notify_workflow_event(
        "operational_incident_reported",
        payload,
        entity_type="operational_incident",
        entity_id=incident.id,
        actor_type="system",
        actor_id="operational_incidents",
    )
    return incident


def acknowledge_operational_incident(
    db: Session,
    incident_id: str,
    *,
    actor_type: str,
    actor_id: str,
    note: str | None = None,
) -> OperationalIncident:
    incident = db.get(OperationalIncident, incident_id)
    if not incident:
        raise OperationalIncidentError("incident_not_found")
    if incident.status != "open":
        raise OperationalIncidentError(f"invalid_status_for_ack:{incident.status}")

    incident.status = "acknowledged"
    incident.acknowledged_at = datetime.now(UTC)
    db.flush()
    ReasoningRepository(db).add_audit(
        action="operational_incident_acknowledged",
        entity_type="operational_incident",
        entity_id=incident.id,
        reason=note or "Đã tiếp nhận / đang xử lý sự cố.",
        after={"status": incident.status},
        actor_type=actor_type,
        actor_id=actor_id,
    )
    db.commit()
    db.refresh(incident)
    return incident


def resolve_operational_incident(
    db: Session,
    incident_id: str,
    *,
    actor_type: str,
    actor_id: str,
    note: str | None = None,
) -> OperationalIncident:
    incident = db.get(OperationalIncident, incident_id)
    if not incident:
        raise OperationalIncidentError("incident_not_found")
    if incident.status not in ("open", "acknowledged"):
        raise OperationalIncidentError(f"invalid_status_for_resolve:{incident.status}")

    incident.status = "resolved"
    incident.resolved_at = datetime.now(UTC)
    db.flush()
    ReasoningRepository(db).add_audit(
        action="operational_incident_resolved",
        entity_type="operational_incident",
        entity_id=incident.id,
        reason=note or "Đã xử lý xong sự cố.",
        after={"status": incident.status},
        actor_type=actor_type,
        actor_id=actor_id,
    )
    db.commit()
    db.refresh(incident)
    return incident


def incident_to_read(db: Session, row: OperationalIncident) -> dict[str, Any]:
    asset = db.get(Asset, row.asset_id)
    data = OperationalIncidentRead.model_validate(row).model_dump(mode="json")
    data["asset_code"] = asset.code if asset else None
    return data
