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
from app.models import Asset, Component, InventoryItem, PurchaseRequest, Rule, domain  # noqa: F401
from app.models.domain import uuid4
from app.main import app


def _sqlite_memory_engine():
    # StaticPool: FastAPI chạy endpoint trong thread pool; :memory: mặc định tách DB theo connection.
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _setup_pr(db) -> str:
    asset = Asset(
        id=uuid4(),
        code="A-T",
        name="Asset test",
        asset_type="elevator",
        status="active",
    )
    rule = Rule(
        id=uuid4(),
        code="R-TEST",
        name="Test",
        domain="elevator_maintenance",
        condition_json={"component_type": "cable", "remaining_lifetime_months_lte": 6},
        action_json=["x"],
        evidence_required_json=[],
        status="approved",
        version=1,
    )
    inv = InventoryItem(
        id=uuid4(),
        code="SP-T",
        name="Part",
        component_type="cable",
        quantity_on_hand=0,
        minimum_quantity=1,
        lead_time_months=8,
        import_required=True,
    )
    db.add(asset)
    db.add(rule)
    db.add(inv)
    db.flush()
    comp = Component(
        id=uuid4(),
        asset_id=asset.id,
        code="CMP-T",
        name="Comp",
        component_type="cable",
        remaining_lifetime_months=3,
        spare_part_code="SP-T",
    )
    db.add(comp)
    db.flush()
    pr = PurchaseRequest(
        id=uuid4(),
        component_id=comp.id,
        inventory_item_id=inv.id,
        rule_id=rule.id,
        reason="test",
        quantity_requested=1,
        status="draft",
        approval_policy_code="AP-X",
        final_approver="CEO",
        created_by_agent=False,
    )
    db.add(pr)
    db.commit()
    return pr.id


def test_single_approve_when_not_import(monkeypatch) -> None:
    monkeypatch.delenv("PHASE5_WRITE_SECRET", raising=False)
    get_settings.cache_clear()
    engine = _sqlite_memory_engine()
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr("app.services.notification_flow.post_n8n_workflow_event", lambda *a, **k: {"sent": True})
    monkeypatch.setattr("app.services.purchase_workflow.Neo4jSyncService.sync_task_and_request", lambda self, **_: {})

    with TestingSession() as db:
        pr_id = _setup_pr(db)
        inv = db.get(InventoryItem, db.get(PurchaseRequest, pr_id).inventory_item_id)
        inv.import_required = False
        db.commit()

    from app.core import database as dbmod

    monkeypatch.setattr(dbmod, "engine", engine)
    monkeypatch.setattr(dbmod, "SessionLocal", TestingSession)
    client = TestClient(app)
    assert client.post(f"/api/purchase-requests/{pr_id}/submit", json={"actor_type": "user", "actor_id": "u1"}).status_code == 200
    r = client.post(f"/api/purchase-requests/{pr_id}/approve", json={"actor_type": "user", "actor_id": "ops"})
    assert r.status_code == 200
    assert r.json()["status"] == "approved"


def test_purchase_submit_approve_reject(monkeypatch) -> None:
    monkeypatch.delenv("PHASE5_WRITE_SECRET", raising=False)
    get_settings.cache_clear()
    engine = _sqlite_memory_engine()
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    calls: list[str] = []

    def fake_post(event: str, payload: dict) -> dict:
        calls.append(event)
        return {"sent": True, "http_status": 200}

    monkeypatch.setattr("app.services.notification_flow.post_n8n_workflow_event", fake_post)
    monkeypatch.setattr("app.services.purchase_workflow.Neo4jSyncService.sync_task_and_request", lambda self, **_: {})

    with TestingSession() as db:
        pr_id = _setup_pr(db)

    from app.core import database as dbmod

    monkeypatch.setattr(dbmod, "engine", engine)
    monkeypatch.setattr(dbmod, "SessionLocal", TestingSession)

    client = TestClient(app)

    r = client.post(
        f"/api/purchase-requests/{pr_id}/submit",
        json={"actor_type": "user", "actor_id": "u1", "note": "gửi duyệt"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "waiting_for_approval"
    assert "purchase_request_waiting_for_approval" in calls

    r2 = client.post(
        f"/api/purchase-requests/{pr_id}/approve",
        json={"actor_type": "user", "actor_id": "tp_ops", "note": "cấp 1"},
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "waiting_for_approval"
    assert r2.json()["first_approved_by"] == "tp_ops"
    assert "purchase_request_level1_approved" in calls

    r3 = client.post(
        f"/api/purchase-requests/{pr_id}/approve",
        json={"actor_type": "user", "actor_id": "ceo", "note": "ok"},
    )
    assert r3.status_code == 200
    assert r3.json()["status"] == "approved"
    assert "purchase_request_approved" in calls

    logs = client.get("/api/audit-logs", params={"entity_type": "purchase_request", "entity_id": pr_id})
    assert logs.status_code == 200
    actions = {item["action"] for item in logs.json()}
    assert "user_submitted_purchase_request" in actions
    assert "user_approved_purchase_request_level1" in actions
    assert "user_approved_purchase_request" in actions


def test_purchase_reject_flow(monkeypatch) -> None:
    monkeypatch.delenv("PHASE5_WRITE_SECRET", raising=False)
    get_settings.cache_clear()
    engine = _sqlite_memory_engine()
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr("app.services.notification_flow.post_n8n_workflow_event", lambda *a, **k: {"sent": True})
    monkeypatch.setattr("app.services.purchase_workflow.Neo4jSyncService.sync_task_and_request", lambda self, **_: {})

    with TestingSession() as db:
        pr_id = _setup_pr(db)
        pr = db.get(PurchaseRequest, pr_id)
        pr.status = "waiting_for_approval"
        db.commit()

    from app.core import database as dbmod

    monkeypatch.setattr(dbmod, "engine", engine)
    monkeypatch.setattr(dbmod, "SessionLocal", TestingSession)

    client = TestClient(app)
    r = client.post(
        f"/api/purchase-requests/{pr_id}/reject",
        json={"actor_type": "user", "actor_id": "ceo"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_purchase_get_detail_has_asset_fields(monkeypatch) -> None:
    monkeypatch.delenv("PHASE5_WRITE_SECRET", raising=False)
    get_settings.cache_clear()
    engine = _sqlite_memory_engine()
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestingSession() as db:
        pr_id = _setup_pr(db)
    from app.core import database as dbmod

    monkeypatch.setattr(dbmod, "engine", engine)
    monkeypatch.setattr(dbmod, "SessionLocal", TestingSession)
    client = TestClient(app)
    r = client.get(f"/api/purchase-requests/{pr_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["asset_code"] == "A-T"
    assert data["component_code"] == "CMP-T"
    assert data["asset_id"]


def test_purchase_cancel_draft(monkeypatch) -> None:
    monkeypatch.delenv("PHASE5_WRITE_SECRET", raising=False)
    get_settings.cache_clear()
    engine = _sqlite_memory_engine()
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr("app.services.notification_flow.post_n8n_workflow_event", lambda *a, **k: {"sent": True})
    monkeypatch.setattr("app.services.purchase_workflow.Neo4jSyncService.sync_task_and_request", lambda self, **_: {})
    with TestingSession() as db:
        pr_id = _setup_pr(db)
    from app.core import database as dbmod

    monkeypatch.setattr(dbmod, "engine", engine)
    monkeypatch.setattr(dbmod, "SessionLocal", TestingSession)
    client = TestClient(app)
    r = client.post(f"/api/purchase-requests/{pr_id}/cancel", json={"actor_type": "user", "actor_id": "u1"})
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"


def test_phase5_write_secret_enforced(monkeypatch) -> None:
    engine = _sqlite_memory_engine()
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr("app.services.notification_flow.post_n8n_workflow_event", lambda *a, **k: {"sent": True})
    monkeypatch.setattr("app.services.purchase_workflow.Neo4jSyncService.sync_task_and_request", lambda self, **_: {})
    with TestingSession() as db:
        pr_id = _setup_pr(db)
    from app.core import database as dbmod

    monkeypatch.setattr(dbmod, "engine", engine)
    monkeypatch.setattr(dbmod, "SessionLocal", TestingSession)
    monkeypatch.setenv("PHASE5_WRITE_SECRET", "only-test")
    get_settings.cache_clear()
    try:
        client = TestClient(app)
        denied = client.post(f"/api/purchase-requests/{pr_id}/submit", json={"actor_type": "user", "actor_id": "u1"})
        assert denied.status_code == 403
        ok = client.post(
            f"/api/purchase-requests/{pr_id}/submit",
            json={"actor_type": "user", "actor_id": "u1"},
            headers={"X-Phase5-Write-Secret": "only-test"},
        )
        assert ok.status_code == 200
    finally:
        monkeypatch.delenv("PHASE5_WRITE_SECRET", raising=False)
        get_settings.cache_clear()
