import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings


def check_llm_health() -> dict:
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider != "gemini":
        return {
            "provider": provider,
            "configured": bool(settings.openai_api_key),
            "reachable": False,
            "model": settings.openai_model,
            "detail": "Only Gemini health check is implemented in this phase.",
        }

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


def _extract_text(body: dict) -> str:
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

