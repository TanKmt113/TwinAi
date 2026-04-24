import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["AUTO_SEED"] = "false"
os.environ["ENABLE_NEO4J_SYNC"] = "false"
os.environ["IOT_INGEST_SECRET"] = "test-iot-secret-for-ci"
os.environ["IOT_INCIDENT_COOLDOWN_SECONDS"] = "3600"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.database import Base
from app.models import Asset, OperationalIncident  # noqa: F401
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
            code="ELV-IOT-TEST",
            name="Lift IoT test",
            asset_type="elevator",
            status="active",
        ),
    )
    db.commit()
    return aid


def test_iot_telemetry_below_threshold(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv("IOT_INGEST_SECRET", "test-iot-secret-for-ci")
    get_settings.cache_clear()
    engine = _sqlite_memory_engine()
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr("app.services.operational_incidents.notify_workflow_event", lambda *a, **k: {})

    with TestingSession() as db:
        asset_id = _seed_asset(db)

    from app.core import database as dbmod

    monkeypatch.setattr(dbmod, "engine", engine)
    monkeypatch.setattr(dbmod, "SessionLocal", TestingSession)

    client = TestClient(app)
    r = client.post(
        "/api/iot/telemetry",
        headers={"X-IoT-Ingest-Secret": "test-iot-secret-for-ci"},
        json={
            "asset_id": asset_id,
            "device_id": "vib-01",
            "metric": "vibration_mm_s2",
            "value": 3.0,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["decision"] == "below_threshold"


def test_iot_telemetry_creates_incident(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv("IOT_INGEST_SECRET", "test-iot-secret-for-ci")
    get_settings.cache_clear()
    engine = _sqlite_memory_engine()
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr("app.services.operational_incidents.notify_workflow_event", lambda *a, **k: {})

    with TestingSession() as db:
        asset_id = _seed_asset(db)

    from app.core import database as dbmod

    monkeypatch.setattr(dbmod, "engine", engine)
    monkeypatch.setattr(dbmod, "SessionLocal", TestingSession)

    client = TestClient(app)
    r = client.post(
        "/api/iot/telemetry",
        headers={"X-IoT-Ingest-Secret": "test-iot-secret-for-ci"},
        json={
            "asset_id": asset_id,
            "device_id": "vib-01",
            "metric": "vibration_mm_s2",
            "value": 12.0,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "incident_created"
    assert body["data"]["incident_kind"] == "vibration"

    r2 = client.post(
        "/api/iot/telemetry",
        headers={"X-IoT-Ingest-Secret": "test-iot-secret-for-ci"},
        json={
            "asset_id": asset_id,
            "device_id": "vib-01",
            "metric": "vibration_mm_s2",
            "value": 15.0,
        },
    )
    assert r2.status_code == 200
    assert r2.json()["decision"] == "cooldown_skip"


def test_iot_ingest_forbidden_and_disabled(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv("IOT_INGEST_SECRET", "only-this")
    get_settings.cache_clear()
    engine = _sqlite_memory_engine()
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    from app.core import database as dbmod

    monkeypatch.setattr(dbmod, "engine", engine)
    monkeypatch.setattr(dbmod, "SessionLocal", TestingSession)

    client = TestClient(app)
    bad = client.post(
        "/api/iot/telemetry",
        headers={"X-IoT-Ingest-Secret": "wrong"},
        json={"asset_id": "x", "metric": "vibration_mm_s2", "value": 1},
    )
    assert bad.status_code == 403

    monkeypatch.delenv("IOT_INGEST_SECRET", raising=False)
    get_settings.cache_clear()
    dis = client.post(
        "/api/iot/telemetry",
        headers={"X-IoT-Ingest-Secret": "x"},
        json={"asset_id": "x", "metric": "vibration_mm_s2", "value": 1},
    )
    assert dis.status_code == 503
