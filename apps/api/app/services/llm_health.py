import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings


def check_llm_health() -> dict[str, Any]:
    """Provider-aware LLM reachability (used by /api/llm/health and system health)."""
    settings = get_settings()
    provider = settings.llm_provider.lower()
    if provider == "gemini":
        return _check_gemini_health()
    if provider == "openai":
        return _check_openai_health()
    return {
        "provider": provider,
        "configured": False,
        "reachable": False,
        "model": "",
        "detail": f"Unsupported LLM provider for health: {provider}",
    }


def _check_gemini_health() -> dict[str, Any]:
    settings = get_settings()
    if not settings.gemini_api_key:
        return {
            "provider": "gemini",
            "configured": False,
            "reachable": False,
            "model": settings.gemini_model,
            "detail": "GEMINI_API_KEY is missing.",
        }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": 'Reply with exactly: "ok"'}],
            }
        ]
    }
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.gemini_api_key,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
            text = _extract_text(body)
            return {
                "provider": "gemini",
                "configured": True,
                "reachable": True,
                "model": settings.gemini_model,
                "response_text": text,
            }
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return {
            "provider": "gemini",
            "configured": True,
            "reachable": False,
            "model": settings.gemini_model,
            "status_code": exc.code,
            "detail": _redact(detail),
        }
    except (TimeoutError, URLError, OSError) as exc:
        return {
            "provider": "gemini",
            "configured": True,
            "reachable": False,
            "model": settings.gemini_model,
            "detail": str(exc),
        }


def _check_openai_health() -> dict[str, Any]:
    settings = get_settings()
    if not settings.openai_api_key:
        return {
            "provider": "openai",
            "configured": False,
            "reachable": False,
            "model": settings.openai_model,
            "detail": "OPENAI_API_KEY is missing.",
        }
    base_url = settings.openai_base_url.rstrip("/") or "https://api.openai.com/v1"
    url = f"{base_url}/models?limit=1"
    request = Request(
        url,
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=15) as response:
            _ = json.loads(response.read().decode("utf-8"))
        return {
            "provider": "openai",
            "configured": True,
            "reachable": True,
            "model": settings.openai_model,
            "detail": "OpenAI API reachable.",
        }
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return {
            "provider": "openai",
            "configured": True,
            "reachable": False,
            "model": settings.openai_model,
            "status_code": exc.code,
            "detail": _redact_openai(detail),
        }
    except (TimeoutError, URLError, OSError, json.JSONDecodeError) as exc:
        return {
            "provider": "openai",
            "configured": True,
            "reachable": False,
            "model": settings.openai_model,
            "detail": str(exc),
        }


def _extract_text(body: dict[str, Any]) -> str:
    candidates = body.get("candidates") or []
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(part.get("text", "") for part in parts).strip()


def _redact(value: str) -> str:
    settings = get_settings()
    if settings.gemini_api_key:
        return value.replace(settings.gemini_api_key, "<redacted>")
    return value


def _redact_openai(value: str) -> str:
    settings = get_settings()
    if settings.openai_api_key and len(settings.openai_api_key) > 8:
        key = settings.openai_api_key
        return value.replace(key, "<redacted>")
    return value
