import os
from datetime import UTC, datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["AUTO_SEED"] = "false"
os.environ["ENABLE_NEO4J_SYNC"] = "false"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.database import Base
from app.models import EscalationPolicy, OrgUnit, OrgUser, domain  # noqa: F401
from app.models.domain import uuid4
from app.main import app


def test_escalation_check_exceeds_sla(monkeypatch) -> None:
    monkeypatch.delenv("PHASE5_WRITE_SECRET", raising=False)
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    with Session() as db:
        db.add(
            EscalationPolicy(
                id=uuid4(),
                code="ELV-CABLE-ESCALATION-01",
                name="Test",
                config_json={"acknowledge_minutes": 30, "escalate_to_roles": ["executive"]},
            )
        )
        db.add(OrgUnit(id=uuid4(), code="OU1", name="U", level_kind="branch", parent_id=None, sort_order=0))
        db.flush()
        unit = db.scalar(select(OrgUnit).limit(1))
        db.add(
            OrgUser(
                id=uuid4(),
                user_code="EXEC-1",
                full_name="Exec",
                email=None,
                job_title=None,
                org_unit_id=unit.id,
                manager_user_id=None,
                role_tags=["executive"],
                is_active=True,
            )
        )
        db.commit()

    from app.core import database as dbmod

    monkeypatch.setattr(dbmod, "engine", engine)
    monkeypatch.setattr(dbmod, "SessionLocal", Session)

    client = TestClient(app)
    opened = datetime.now(UTC) - timedelta(minutes=45)
    r = client.post(
        "/api/routing/escalation-check",
        json={
            "policy_code": "ELV-CABLE-ESCALATION-01",
            "opened_at": opened.isoformat(),
            "dry_run": True,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["should_escalate"] is True
    assert data["reason"] == "sla_exceeded"
