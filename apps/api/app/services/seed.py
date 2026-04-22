from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, Component, InventoryItem, Manual, Rule


def seed_phase_two_data(db: Session) -> None:
    manual = _get_or_create_manual(db)
    _get_or_create_assets_and_components(db)
    _get_or_create_inventory(db)
    _get_or_create_rule(db, manual)
    db.commit()


def _get_or_create_manual(db: Session) -> Manual:
    manual = db.scalar(select(Manual).where(Manual.code == "MAN-ELV-001"))
    if manual:
        return manual

    manual = Manual(
        code="MAN-ELV-001",
        title="Manual bảo trì thang máy Calidas",
        department_owner="Kỹ thuật",
        file_object_key="manuals/MAN-ELV-001.pdf",
        file_name="Manual bảo trì thang máy Calidas.pdf",
        file_type="pdf",
        version="draft",
        status="uploaded",
    )
    db.add(manual)
    db.flush()
    return manual


def _get_or_create_assets_and_components(db: Session) -> None:
    rows = [
        {
            "asset": {
                "code": "ELV-CALIDAS-01",
                "name": "Thang máy Calidas 1",
                "asset_type": "elevator",
                "location": "Sảnh khách sạn - trục A",
                "department_owner": "Kỹ thuật",
            },
            "component": {
                "code": "CMP-CABLE-001",
                "name": "Cáp kéo Calidas 1",
                "component_type": "cable",
                "installed_at": date(2020, 11, 15),
                "expected_lifetime_months": 72,
                "remaining_lifetime_months": 5,
                "last_inspection_at": date(2026, 1, 20),
                "spare_part_code": "SP-CABLE-CALIDAS",
            },
        },
        {
            "asset": {
                "code": "ELV-CALIDAS-02",
                "name": "Thang máy Calidas 2",
                "asset_type": "elevator",
                "location": "Sảnh khách sạn - trục B",
                "department_owner": "Kỹ thuật",
            },
            "component": {
                "code": "CMP-CABLE-002",
                "name": "Cáp kéo Calidas 2",
                "component_type": "cable",
                "installed_at": date(2022, 2, 10),
                "expected_lifetime_months": 72,
                "remaining_lifetime_months": 22,
                "last_inspection_at": date(2026, 1, 22),
                "spare_part_code": "SP-CABLE-CALIDAS",
            },
        },
        {
            "asset": {
                "code": "ELV-SERVICE-01",
                "name": "Thang máy dịch vụ 1",
                "asset_type": "elevator",
                "location": "Khu hậu cần",
                "department_owner": "Kỹ thuật",
            },
            "component": {
                "code": "CMP-CABLE-003",
                "name": "Cáp kéo thang dịch vụ 1",
                "component_type": "cable",
                "installed_at": date(2021, 8, 1),
                "expected_lifetime_months": 72,
                "remaining_lifetime_months": 15,
                "last_inspection_at": date(2026, 2, 5),
                "spare_part_code": "SP-CABLE-SERVICE",
            },
        },
    ]

    for row in rows:
        asset = db.scalar(select(Asset).where(Asset.code == row["asset"]["code"]))
        if not asset:
            asset = Asset(**row["asset"])
            db.add(asset)
            db.flush()

        component = db.scalar(select(Component).where(Component.code == row["component"]["code"]))
        if not component:
            db.add(Component(asset_id=asset.id, **row["component"]))


def _get_or_create_inventory(db: Session) -> None:
    rows = [
        {
            "code": "SP-CABLE-CALIDAS",
            "name": "Bộ cáp kéo Calidas",
            "component_type": "cable",
            "quantity_on_hand": 0,
            "minimum_quantity": 1,
            "lead_time_months": 7,
            "supplier_name": "Nhà cung cấp Đức",
            "import_required": True,
        },
        {
            "code": "SP-CABLE-SERVICE",
            "name": "Bộ cáp kéo thang dịch vụ",
            "component_type": "cable",
            "quantity_on_hand": 1,
            "minimum_quantity": 1,
            "lead_time_months": 4,
            "supplier_name": "Nhà cung cấp nội địa",
            "import_required": False,
        },
    ]

    for row in rows:
        item = db.scalar(select(InventoryItem).where(InventoryItem.code == row["code"]))
        if not item:
            db.add(InventoryItem(**row))


def _get_or_create_rule(db: Session, manual: Manual) -> None:
    rule = db.scalar(select(Rule).where(Rule.code == "R-ELV-CABLE-001"))
    if rule:
        return

    db.add(
        Rule(
            code="R-ELV-CABLE-001",
            name="Cảnh báo cáp kéo thang máy còn dưới hoặc bằng 6 tháng tuổi thọ",
            domain="elevator_maintenance",
            condition_json={
                "component_type": "cable",
                "remaining_lifetime_months_lte": 6,
            },
            action_json=[
                "create_technical_alert",
                "create_inspection_task",
                "check_spare_part_inventory",
                "evaluate_purchase_need",
                "identify_approval_flow",
            ],
            evidence_required_json=[
                "cable_diameter_measurement",
                "vibration_measurement",
                "last_inspection_date",
                "technician_assessment",
            ],
            source_manual_id=manual.id,
            owner_department="Kỹ thuật",
            status="approved",
            version=1,
        )
    )

