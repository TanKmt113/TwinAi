"""Tiếp nhận telemetry IoT, đánh giá ngưỡng (demo), tạo operational incident khi cần."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import OperationalIncident
from app.schemas.domain import IoTTelemetryIngestBody
from app.services.operational_incidents import _resolve_asset, create_operational_incident

logger = logging.getLogger(__name__)

# Ngưỡng demo — production nên chuyển DB hoặc config có phiên bản.
_THRESHOLD_RULES: tuple[dict[str, Any], ...] = (
    {
        "id": "vibration_high",
        "metric": "vibration_mm_s2",
        "op": "gt",
        "threshold": 8.0,
        "incident_kind": "vibration",
        "severity": "critical",
        "title_template": "Rung {value:.1f} mm/s² (ngưỡng {threshold})",
        "description_template": "Cảm biến rung IoT vượt ngưỡng demo.",
    },
    {
        "id": "door_open_long",
        "metric": "door_open_seconds",
        "op": "gt",
        "threshold": 30.0,
        "incident_kind": "door_fault",
        "severity": "warning",
        "title_template": "Cửa mở bất thường {value:.0f}s (ngưỡng {threshold:.0f}s)",
        "description_template": "Thời gian cửa mở vượt ngưỡng từ cảm biến.",
    },
    {
        "id": "power_low",
        "metric": "power_voltage_v",
        "op": "lt",
        "threshold": 180.0,
        "incident_kind": "power_loss",
        "severity": "critical",
        "title_template": "Điện áp thấp {value:.1f}V (ngưỡng {threshold:.0f}V)",
        "description_template": "Đo nguồn từ IoT; có nguy cơ mất điện / UPS.",
    },
    {
        "id": "overspeed",
        "metric": "overspeed_pct",
        "op": "gt",
        "threshold": 10.0,
        "incident_kind": "overspeed",
        "severity": "critical",
        "title_template": "Quá tốc {value:.1f}% (ngưỡng {threshold:.0f}%)",
        "description_template": "Tín hiệu tốc độ từ bộ điều khiển / encoder.",
    },
    {
        "id": "controller_fault_code",
        "metric": "controller_error_code",
        "op": "ne",
        "threshold": 0.0,
        "incident_kind": "controller_fault",
        "severity": "warning",
        "title_template": "Mã lỗi controller {value:.0f}",
        "description_template": "Controller báo mã lỗi khác 0.",
    },
    {
        "id": "noise_high",
        "metric": "noise_db",
        "op": "gt",
        "threshold": 85.0,
        "incident_kind": "unusual_noise",
        "severity": "warning",
        "title_template": "Tiếng ồn {value:.0f} dB (ngưỡng {threshold:.0f})",
        "description_template": "Cảm biến âm thanh vượt ngưỡng demo.",
    },
)


def _eval_op(op: str, value: float, threshold: float) -> bool:
    if op == "gt":
        return value > threshold
    if op == "gte":
        return value >= threshold
    if op == "lt":
        return value < threshold
    if op == "lte":
        return value <= threshold
    if op == "ne":
        return value != threshold
    return False


def _find_rule(metric: str) -> dict[str, Any] | None:
    for rule in _THRESHOLD_RULES:
        if rule["metric"] == metric:
            return rule
    return None


def _supported_metrics() -> list[str]:
    return [r["metric"] for r in _THRESHOLD_RULES]


def process_iot_telemetry(db: Session, body: IoTTelemetryIngestBody, settings: Settings) -> dict[str, Any]:
    """Trả về dict chuẩn { success, decision, data, error } cho API."""
    metric = body.metric.strip().lower()
    rule = _find_rule(metric)
    if not rule:
        logger.info("iot_ingest: metric không có rule — %s", metric)
        return {
            "success": True,
            "decision": "no_matching_rule",
            "data": {"metric": metric, "supported_metrics": _supported_metrics()},
            "error": None,
        }

    asset = _resolve_asset(db, body.asset_id.strip())
    threshold = float(rule["threshold"])
    breached = _eval_op(rule["op"], body.value, threshold)

    if not breached:
        return {
            "success": True,
            "decision": "below_threshold",
            "data": {
                "metric": metric,
                "value": body.value,
                "op": rule["op"],
                "threshold": threshold,
                "asset_code": asset.code,
            },
            "error": None,
        }

    cutoff = datetime.now(UTC) - timedelta(seconds=settings.iot_incident_cooldown_seconds)
    recent = db.scalars(
        select(OperationalIncident)
        .where(
            OperationalIncident.asset_id == asset.id,
            OperationalIncident.incident_kind == rule["incident_kind"],
            OperationalIncident.source == "iot_ingest",
            OperationalIncident.created_at >= cutoff,
        )
        .order_by(OperationalIncident.created_at.desc())
        .limit(1),
    ).first()
    if recent:
        logger.info(
            "iot_ingest: cooldown asset=%s kind=%s recent=%s",
            asset.code,
            rule["incident_kind"],
            recent.id,
        )
        return {
            "success": True,
            "decision": "cooldown_skip",
            "data": {
                "metric": metric,
                "value": body.value,
                "existing_incident_id": recent.id,
                "cooldown_seconds": settings.iot_incident_cooldown_seconds,
            },
            "error": None,
        }

    title = rule["title_template"].format(value=body.value, threshold=threshold)
    description = rule["description_template"].format(value=body.value, threshold=threshold)
    extra = {
        "iot": True,
        "metric": body.metric,
        "value": body.value,
        "unit": body.unit,
        "observed_at": body.observed_at.isoformat() if body.observed_at else None,
        "device_id": body.device_id,
        "metadata": body.metadata,
        "rule_id": rule["id"],
    }

    incident = create_operational_incident(
        db,
        asset_id_or_code=asset.id,
        incident_kind=rule["incident_kind"],
        title=title,
        description=description,
        severity=rule["severity"],
        actor_type="device",
        actor_id=body.device_id.strip() or "unknown_device",
        source="iot_ingest",
        extra_json=extra,
    )
    logger.info("iot_ingest: incident_created id=%s asset=%s", incident.id, asset.code)

    return {
        "success": True,
        "decision": "incident_created",
        "data": {
            "incident_id": incident.id,
            "incident_kind": incident.incident_kind,
            "severity": incident.severity,
            "asset_code": asset.code,
            "metric": metric,
            "value": body.value,
            "rule_id": rule["id"],
        },
        "error": None,
    }
