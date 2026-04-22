from dataclasses import asdict, dataclass

from app.core.config import get_settings


@dataclass(frozen=True)
class DependencyStatus:
    name: str
    configured: bool
    detail: str


def check_dependencies() -> dict:
    settings = get_settings()
    statuses = [
        DependencyStatus("postgresql", bool(settings.database_url), _mask_url(settings.database_url)),
        DependencyStatus("neo4j", bool(settings.neo4j_uri), settings.neo4j_uri),
        DependencyStatus("minio", bool(settings.minio_endpoint), settings.minio_endpoint),
        DependencyStatus("llm_provider", bool(settings.llm_provider), settings.llm_provider),
        DependencyStatus("openai", bool(settings.openai_api_key), "configured" if settings.openai_api_key else "missing"),
        DependencyStatus("gemini", bool(settings.gemini_api_key), "configured" if settings.gemini_api_key else "missing"),
        DependencyStatus("n8n", bool(settings.n8n_webhook_url), settings.n8n_webhook_url or "missing"),
    ]

    return {
        "status": "ok",
        "dependencies": [asdict(status) for status in statuses],
    }


def _mask_url(value: str) -> str:
    if "@" not in value:
        return value
    scheme, rest = value.split("://", 1)
    host = rest.split("@", 1)[1]
    return f"{scheme}://***:***@{host}"
