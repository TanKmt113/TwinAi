import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["AUTO_SEED"] = "false"
os.environ["ENABLE_NEO4J_SYNC"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dependency_health() -> None:
    response = client.get("/health/dependencies")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_services_health() -> None:
    try:
        response = client.get("/health/services")
    except Exception as exc:
        pytest.skip(f"dependency health check needs reachable infra: {exc}")
    assert response.status_code == 200
    body = response.json()
    assert body["overall"] in ("ok", "degraded", "critical")
    assert "checked_at" in body
    assert isinstance(body["services"], list)
    ids = {item["id"] for item in body["services"]}
    assert {"api", "postgresql", "neo4j", "minio", "llm", "n8n"}.issubset(ids)
    for item in body["services"]:
        assert "label" in item and "ok" in item and "detail" in item
