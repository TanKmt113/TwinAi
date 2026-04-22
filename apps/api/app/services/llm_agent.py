import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings


class LlmAgentError(RuntimeError):
    pass


class LlmAgentClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        provider = self.settings.llm_provider.lower()
        if provider == "gemini":
            return bool(self.settings.gemini_api_key)
        if provider == "openai":
            return bool(self.settings.openai_api_key)
        return False

    def provider_name(self) -> str:
        return self.settings.llm_provider.lower()

    def generate_chat_response(self, question: str, intent: str, tool_context: dict[str, Any]) -> dict[str, Any]:
        prompt = _build_prompt(question=question, intent=intent, tool_context=tool_context)
        provider = self.provider_name()
        if provider == "gemini":
            return self._call_gemini(prompt)
        if provider == "openai":
            return self._call_openai(prompt)
        raise LlmAgentError(f"Unsupported LLM provider: {provider}")

    def _call_gemini(self, prompt: str) -> dict[str, Any]:
        if not self.settings.gemini_api_key:
            raise LlmAgentError("GEMINI_API_KEY is missing.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.settings.gemini_model}:generateContent"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1},
        }
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.settings.gemini_api_key},
            method="POST",
        )
        body = self._send_json_request(request)
        text = _extract_gemini_text(body)
        return _parse_agent_json(text)

    def _call_openai(self, prompt: str) -> dict[str, Any]:
        if not self.settings.openai_api_key:
            raise LlmAgentError("OPENAI_API_KEY is missing.")

        base_url = self.settings.openai_base_url.rstrip("/") or "https://api.openai.com/v1"
        url = f"{base_url}/chat/completions"
        payload = {
            "model": self.settings.openai_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You return only valid JSON for a constrained ontology operations assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.settings.openai_api_key}"},
            method="POST",
        )
        body = self._send_json_request(request)
        text = body["choices"][0]["message"]["content"]
        return _parse_agent_json(text)

    @staticmethod
    def _send_json_request(request: Request) -> dict[str, Any]:
        try:
            with urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LlmAgentError(f"LLM HTTP {exc.code}: {detail[:500]}") from exc
        except (TimeoutError, URLError, OSError, json.JSONDecodeError) as exc:
            raise LlmAgentError(f"LLM request failed: {exc}") from exc


def _build_prompt(question: str, intent: str, tool_context: dict[str, Any]) -> str:
    context_json = json.dumps(tool_context, ensure_ascii=False, default=str)
    return f"""
Bạn là agent diễn giải cho hệ thống Ontology bảo trì thang máy.

Nguyên tắc bắt buộc:
- Chỉ dùng dữ liệu trong TOOL_CONTEXT.
- Không tự tạo rule, số liệu, task, purchase request hoặc người phê duyệt.
- Không tự quyết định mua hàng.
- Nếu thiếu dữ liệu, nói rõ "không đủ dữ liệu" trong missing_data.
- Mỗi kết luận quan trọng phải bám vào evidence/citations có trong TOOL_CONTEXT.
- Trả về JSON hợp lệ, không markdown.

QUESTION:
{question}

INTENT:
{intent}

TOOL_CONTEXT:
{context_json}

JSON schema cần trả:
{{
  "conclusion": "string",
  "evidence": ["string"],
  "recommended_actions": ["string"],
  "missing_data": ["string"],
  "citations": [{{"type": "string", "code": "string", "title": "string"}}]
}}
""".strip()


def _extract_gemini_text(body: dict[str, Any]) -> str:
    candidates = body.get("candidates") or []
    if not candidates:
        raise LlmAgentError("Gemini returned no candidates.")
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(part.get("text", "") for part in parts).strip()


def _parse_agent_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        raise LlmAgentError(f"LLM returned invalid JSON: {text[:500]}") from exc
