from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    n8n_webhook_url: str = Field(default="", alias="N8N_WEBHOOK_URL")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
