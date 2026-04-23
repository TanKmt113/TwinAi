"""Aggregate connectivity checks for dashboard / ops visibility."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from minio import Minio
from minio.error import MinioException
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings, get_settings
from app.core.database import engine
from app.services.llm_health import check_llm_health


def check_services_status() -> dict[str, Any]:
    """Return reachability of backing services (no secrets in detail strings)."""
    settings = get_settings()
    checked_at = datetime.now(tz=UTC).isoformat()
    services: list[dict[str, Any]] = [
        _service_api(settings),
        _service_postgresql(),
        _service_neo4j(settings),
        _service_minio(settings),
        _service_llm(),
        _service_n8n(settings),
    ]
    postgres_ok = next((s["ok"] for s in services if s["id"] == "postgresql"), False)
    all_ok = all(s["ok"] for s in services)
    if all_ok:
        overall = "ok"
    elif not postgres_ok:
        overall = "critical"
    else:
        overall = "degraded"
    return {
        "overall": overall,
        "checked_at": checked_at,
        "services": services,
    }


def _service_api(settings: Settings) -> dict[str, Any]:
    return {
        "id": "api",
        "label": "API (FastAPI)",
        "ok": True,
        "detail": f"{settings.app_name} · v{settings.app_version}",
    }


def _service_postgresql() -> dict[str, Any]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError) as exc:
        return {
            "id": "postgresql",
            "label": "PostgreSQL",
            "ok": False,
            "detail": str(exc)[:220],
        }
    return {"id": "postgresql", "label": "PostgreSQL", "ok": True, "detail": "Kết nối OK"}


def _service_neo4j(settings: Settings) -> dict[str, Any]:
    extra = "" if settings.enable_neo4j_sync else " Đồng bộ graph đang tắt (ENABLE_NEO4J_SYNC)."
    try:
        with GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        ) as driver:
            driver.verify_connectivity()
    except (Neo4jError, ServiceUnavailable, OSError, ValueError) as exc:
        return {
            "id": "neo4j",
            "label": "Neo4j",
            "ok": False,
            "detail": (str(exc)[:200] + extra).strip(),
        }
    return {
        "id": "neo4j",
        "label": "Neo4j",
        "ok": True,
        "detail": ("Bolt connectivity OK." + extra).strip(),
    }


def _service_minio(settings: Settings) -> dict[str, Any]:
    try:
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        client.bucket_exists(settings.minio_bucket)
    except MinioException as exc:
        return {
            "id": "minio",
            "label": "MinIO",
            "ok": False,
            "detail": str(exc)[:220],
        }
    except OSError as exc:
        return {"id": "minio", "label": "MinIO", "ok": False, "detail": str(exc)[:220]}
    return {
        "id": "minio",
        "label": "MinIO",
        "ok": True,
        "detail": f"Endpoint `{settings.minio_endpoint}`, bucket `{settings.minio_bucket}` OK",
    }


def _service_llm() -> dict[str, Any]:
    raw = check_llm_health()
    provider = str(raw.get("provider") or "unknown")
    configured = bool(raw.get("configured"))
    reachable = bool(raw.get("reachable"))
    detail = str(raw.get("detail") or raw.get("response_text") or "").strip()
    if not configured:
        return {
            "id": "llm",
            "label": f"LLM ({provider})",
            "ok": True,
            "detail": (detail or "Chưa cấu hình API key — chat vẫn chạy rule fallback.")[:280],
            "optional": True,
        }
    if reachable:
        msg = f"{provider}: phản hồi OK"
    else:
        msg = detail or "Không kết nối được tới LLM API."
    return {
        "id": "llm",
        "label": f"LLM ({provider})",
        "ok": reachable,
        "detail": msg[:280],
    }


def _service_n8n(settings: Settings) -> dict[str, Any]:
    url = (settings.n8n_webhook_url or "").strip()
    if not url:
        return {
            "id": "n8n",
            "label": "n8n",
            "ok": True,
            "detail": "Chưa cấu hình N8N_WEBHOOK_URL (tùy chọn).",
            "optional": True,
        }
    request = Request(url, method="GET")
    try:
        with urlopen(request, timeout=8) as response:
            code = response.status
            ok = code < 500
    except HTTPError as exc:
        # Webhook thường trả 404/405 cho GET nhưng instance vẫn sống
        ok = exc.code < 500
        code = exc.code
        return {
            "id": "n8n",
            "label": "n8n webhook",
            "ok": ok,
            "detail": f"HTTP {code}",
        }
    except (URLError, TimeoutError, OSError) as exc:
        return {"id": "n8n", "label": "n8n webhook", "ok": False, "detail": str(exc)[:220]}
    return {"id": "n8n", "label": "n8n webhook", "ok": ok, "detail": f"HTTP {code}"}
