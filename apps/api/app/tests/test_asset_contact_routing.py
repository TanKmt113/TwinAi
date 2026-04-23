import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["AUTO_SEED"] = "false"

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Asset, AssetContactAssignment, OrgUser, domain  # noqa: F401
from app.models.domain import uuid4
from app.services.routing_context import build_asset_contacts
from app.services.seed import (
    _get_or_create_assets_and_components,
    _seed_asset_contact_assignments,
    _seed_org_units,
    _seed_org_users,
)


def _sqlite_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def test_build_asset_contacts_prefers_per_asset_assignment() -> None:
    engine = _sqlite_engine()
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    with Session() as db:
        asset_mall = Asset(
            id=uuid4(),
            code="ELV-CALIDAS-01",
            name="Thang 1",
            asset_type="elevator",
            status="active",
        )
        asset_other = Asset(
            id=uuid4(),
            code="ELV-CALIDAS-02",
            name="Thang 2",
            asset_type="elevator",
            status="active",
        )
        db.add_all([asset_mall, asset_other])
        db.flush()
        _seed_org_units(db)
        _seed_org_users(db)
        lead = db.scalar(select(OrgUser).where(OrgUser.user_code == "USR-LEAD-MALL-001"))
        ktv = db.scalar(select(OrgUser).where(OrgUser.user_code == "USR-KTV-001"))
        tp = db.scalar(select(OrgUser).where(OrgUser.user_code == "USR-TP-OPS-001"))
        gd = db.scalar(select(OrgUser).where(OrgUser.user_code == "USR-GD-HN-001"))
        db.add_all(
            [
                AssetContactAssignment(asset_id=asset_mall.id, org_user_id=lead.id, contact_kind="primary", sort_order=0),
                AssetContactAssignment(asset_id=asset_mall.id, org_user_id=tp.id, contact_kind="backup", sort_order=0),
                AssetContactAssignment(asset_id=asset_other.id, org_user_id=ktv.id, contact_kind="primary", sort_order=0),
                AssetContactAssignment(asset_id=asset_other.id, org_user_id=gd.id, contact_kind="backup", sort_order=0),
            ]
        )
        db.commit()

        ctx_mall = build_asset_contacts(db, asset_mall)
        ctx_other = build_asset_contacts(db, asset_other)

    assert ctx_mall["primary_contact"]["user_code"] == "USR-LEAD-MALL-001"
    assert ctx_mall["backup_contact"]["user_code"] == "USR-TP-OPS-001"
    assert ctx_mall["contact_resolution"]["primary_source"] == "asset_assignment"

    assert ctx_other["primary_contact"]["user_code"] == "USR-KTV-001"
    assert ctx_other["backup_contact"]["user_code"] == "USR-GD-HN-001"


def test_seed_asset_assignments_idempotent() -> None:
    engine = _sqlite_engine()
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    with Session() as db:
        _get_or_create_assets_and_components(db)
        _seed_org_units(db)
        _seed_org_users(db)
        _seed_asset_contact_assignments(db)
        n1 = len(list(db.scalars(select(AssetContactAssignment))))
        _seed_asset_contact_assignments(db)
        n2 = len(list(db.scalars(select(AssetContactAssignment))))
        db.commit()
    assert n1 == n2 == 6
