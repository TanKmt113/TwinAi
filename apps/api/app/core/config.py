from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


API_ROOT = Path(__file__).resolve().parents[2]


def find_repo_root(start: Path) -> Path:
    for path in (start, *start.parents):
        if (path / "infra" / "docker-compose.yml").exists() or (path / ".git").exists():
            return path
    return start


REPO_ROOT = find_repo_root(API_ROOT)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", API_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "TwinAI Agentic MVP API"
    app_version: str = "0.1.0"
    environment: str = "development"

    cors_origins_raw: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    database_url: str = Field(
        default="postgresql+psycopg://twinai:twinai@localhost:5432/twinai",
        alias="DATABASE_URL",
    )
    auto_seed: bool = Field(default=True, alias="AUTO_SEED")
    enable_neo4j_sync: bool = Field(default=True, alias="ENABLE_NEO4J_SYNC")
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="twinai-neo4j-password", alias="NEO4J_PASSWORD")

    minio_endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="twinai", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="twinai-minio-password", alias="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")

    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    gemini_embedding_model: str = Field(default="gemini-embedding-001", alias="GEMINI_EMBEDDING_MODEL")
    n8n_webhook_url: str = Field(default="", alias="N8N_WEBHOOK_URL")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
