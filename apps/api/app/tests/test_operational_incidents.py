import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["AUTO_SEED"] = "false"
os.environ["ENABLE_NEO4J_SYNC"] = "false"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.database import Base
from app.models import Asset, domain  # noqa: F401
from app.models.domain import uuid4
from app.main import app


def _sqlite_memory_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _seed_asset(db) -> str:
    aid = uuid4()
    db.add(
        Asset(
            id=aid,
            code="ELV-T-OP",
            name="Test lift",
            asset_type="elevator",
            status="active",
        ),
    )
    db.commit()
    return aid


def test_operational_incident_create_ack_resolve(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.delenv("PHASE5_WRITE_SECRET", raising=False)
    get_settings.cache_clear()
    engine = _sqlite_memory_engine()
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    events: list[str] = []

    def fake_notify(event: str, *_a, **_k) -> None:
        events.append(event)

    monkeypatch.setattr("app.services.operational_incidents.notify_workflow_event", fake_notify)

    with TestingSession() as db:
        asset_id = _seed_asset(db)

    from app.core import database as dbmod

    monkeypatch.setattr(dbmod, "engine", engine)
    monkeypatch.setattr(dbmod, "SessionLocal", TestingSession)

    client = TestClient(app)
    r = client.post(
        "/api/operational-incidents",
        json={
            "asset_id": asset_id,
            "incident_kind": "vibration",
            "title": "Rung tại tầng 3",
            "description": "demo",
            "severity": "warning",
            "actor_type": "user",
            "actor_id": "tester",
        },
    )
    assert r.status_code == 200
    body = r.json()
    inc_id = body["id"]
    assert body["status"] == "open"
    assert body["asset_code"] == "ELV-T-OP"
    assert "operational_incident_reported" in events

    r2 = client.post(
        f"/api/operational-incidents/{inc_id}/acknowledge",
        json={"actor_type": "user", "actor_id": "ops"},
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "acknowledged"

    r3 = client.post(
        f"/api/operational-incidents/{inc_id}/resolve",
        json={"actor_type": "user", "actor_id": "ops"},
    )
    assert r3.status_code == 200
    assert r3.json()["status"] == "resolved"

    listed = client.get("/api/operational-incidents", params={"limit": 10})
    assert listed.status_code == 200
    assert any(row["id"] == inc_id for row in listed.json())


def test_operational_incident_invalid_kind(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.delenv("PHASE5_WRITE_SECRET", raising=False)
    get_settings.cache_clear()
    engine = _sqlite_memory_engine()
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr("app.services.operational_incidents.notify_workflow_event", lambda *a, **k: None)

    with TestingSession() as db:
        asset_id = _seed_asset(db)

    from app.core import database as dbmod

    monkeypatch.setattr(dbmod, "engine", engine)
    monkeypatch.setattr(dbmod, "SessionLocal", TestingSession)

    client = TestClient(app)
    r = client.post(
        "/api/operational-incidents",
        json={
            "asset_id": asset_id,
            "incident_kind": "not_a_real_kind",
            "title": "Invalid kind case",
            "severity": "warning",
        },
    )
    assert r.status_code == 400
