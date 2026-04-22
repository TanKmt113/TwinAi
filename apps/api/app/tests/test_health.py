import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["AUTO_SEED"] = "false"
os.environ["ENABLE_NEO4J_SYNC"] = "false"

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
