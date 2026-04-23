import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["AUTO_SEED"] = "false"
os.environ["ENABLE_NEO4J_SYNC"] = "false"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import domain  # noqa: F401
from app.services.reasoning import ReasoningEngine
from app.services.seed import seed_phase_two_data


def test_reasoning_creates_task_and_purchase_request(monkeypatch) -> None:
    monkeypatch.setattr("app.services.reasoning.dispatch_pending_notifications", lambda *_a, **_k: None)
    engine = create_engine("sqlite+pysqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSession() as db:
        seed_phase_two_data(db)
        response = ReasoningEngine(db).run()

        assert response.status == "completed"
        assert len(response.findings) == 1
        assert response.findings[0]["component_code"] == "CMP-CABLE-001"
        assert len(response.created_tasks) == 1
        assert len(response.created_purchase_requests) == 1
        pr0 = response.created_purchase_requests[0]
        assert pr0.approval_policy_code == "AP-ELV-IMPORT-CEO"
        assert pr0.final_approver in ("CEO", "CEO / Ban đầu tư")


def test_reasoning_is_idempotent_for_open_records(monkeypatch) -> None:
    monkeypatch.setattr("app.services.reasoning.dispatch_pending_notifications", lambda *_a, **_k: None)
    engine = create_engine("sqlite+pysqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSession() as db:
        seed_phase_two_data(db)
        first = ReasoningEngine(db).run()
        second = ReasoningEngine(db).run()

        assert len(first.created_tasks) == 1
        assert len(first.created_purchase_requests) == 1
        assert len(second.created_tasks) == 1
        assert len(second.created_purchase_requests) == 1
        assert second.created_tasks[0].id == first.created_tasks[0].id
        assert second.created_purchase_requests[0].id == first.created_purchase_requests[0].id

