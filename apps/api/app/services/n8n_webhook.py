"""Gửi payload tới n8n (best-effort; lỗi mạng không được làm hỏng transaction nghiệp vụ)."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings


def post_n8n_workflow_event(event: str, payload: dict[str, Any]) -> dict[str, Any]:
    """POST JSON tới N8N_WEBHOOK_URL. Trả dict có sent: bool để caller ghi audit notification_failed."""
    settings = get_settings()
    url = (settings.n8n_webhook_url or "").strip()
    if not url:
        return {"sent": False, "skipped": True, "detail": "N8N_WEBHOOK_URL empty"}

    body = json.dumps({"event": event, "payload": payload}, ensure_ascii=False).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=12) as response:
            return {"sent": True, "http_status": response.status}
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        return {"sent": False, "http_status": exc.code, "detail": detail}
    except (URLError, TimeoutError, OSError) as exc:
        return {"sent": False, "detail": str(exc)[:400]}
