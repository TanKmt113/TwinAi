import json
from collections.abc import Iterable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings


class EmbeddingError(RuntimeError):
    pass


class EmbeddingClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        provider = self.settings.llm_provider.lower()
        if provider == "gemini":
            return bool(self.settings.gemini_api_key)
        if provider == "openai":
            return bool(self.settings.openai_api_key)
        return False

    def embed_documents(self, texts: Iterable[str]) -> list[list[float]]:
        text_list = [text.strip() for text in texts if text.strip()]
        if not text_list:
            return []
        provider = self.settings.llm_provider.lower()
        if provider == "gemini":
            return [self._embed_gemini(text, task_type="RETRIEVAL_DOCUMENT") for text in text_list]
        if provider == "openai":
            return self._embed_openai(text_list)
        raise EmbeddingError(f"Unsupported embedding provider: {provider}")

    def embed_query(self, text: str) -> list[float]:
        normalized = text.strip()
        if not normalized:
            raise EmbeddingError("Query text is empty.")
        provider = self.settings.llm_provider.lower()
        if provider == "gemini":
            return self._embed_gemini(normalized, task_type="RETRIEVAL_QUERY")
        if provider == "openai":
            return self._embed_openai([normalized])[0]
        raise EmbeddingError(f"Unsupported embedding provider: {provider}")

    def _embed_gemini(self, text: str, task_type: str) -> list[float]:
        if not self.settings.gemini_api_key:
            raise EmbeddingError("GEMINI_API_KEY is missing.")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.gemini_embedding_model}:embedContent"
        )
        payload = {
            "content": {"parts": [{"text": text}]},
            "taskType": task_type,
        }
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.settings.gemini_api_key},
            method="POST",
        )
        body = self._send_json_request(request)
        values = body.get("embedding", {}).get("values") or []
        if not values:
            raise EmbeddingError("Gemini returned an empty embedding.")
        return [float(value) for value in values]

    def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        if not self.settings.openai_api_key:
            raise EmbeddingError("OPENAI_API_KEY is missing.")
        base_url = self.settings.openai_base_url.rstrip("/") or "https://api.openai.com/v1"
        request = Request(
            f"{base_url}/embeddings",
            data=json.dumps(
                {
                    "model": self.settings.openai_embedding_model,
                    "input": texts,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.settings.openai_api_key}"},
            method="POST",
        )
        body = self._send_json_request(request)
        data = body.get("data") or []
        if not data:
            raise EmbeddingError("OpenAI returned an empty embedding response.")
        return [[float(value) for value in item.get("embedding") or []] for item in data]

    @staticmethod
    def _send_json_request(request: Request) -> dict[str, Any]:
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise EmbeddingError(f"Embedding HTTP {exc.code}: {detail[:500]}") from exc
        except (TimeoutError, URLError, OSError, json.JSONDecodeError) as exc:
            raise EmbeddingError(f"Embedding request failed: {exc}") from exc
