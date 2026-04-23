from datetime import date

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Asset,
    AssetContactAssignment,
    AuditLog,
    Component,
    EscalationPolicy,
    InspectionTask,
    InventoryItem,
    Manual,
    OrgUnit,
    OrgUser,
    PurchaseRequest,
    Rule,
)

def seed_phase_two_data(db: Session) -> None:
    """Idempotent seed: MVP assets + optional fake org / ops rows for UI & chat."""
    manual = _get_or_create_manual(db)
    _get_or_create_assets_and_components(db)
    _get_or_create_inventory(db)
    _get_or_create_rule(db, manual)
    _seed_escalation_policies(db)
    _seed_fake_org_assets_and_components(db)
    _seed_fake_inventory_items(db)
    _seed_demo_open_task_and_purchase(db)
    _seed_demo_audit_org_context(db)
    _seed_org_units(db)
    _seed_org_users(db)
    _seed_asset_contact_assignments(db)
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


def _seed_escalation_policies(db: Session) -> None:
    if db.scalar(select(EscalationPolicy).where(EscalationPolicy.code == "ELV-CABLE-ESCALATION-01")):
        return
    db.add(
        EscalationPolicy(
            code="ELV-CABLE-ESCALATION-01",
            name="Cáp kéo — SLA acknowledge & escalate (demo HN)",
            config_json={
                "acknowledge_minutes": 30,
                "primary_contact_roles": ["technician", "field"],
                "backup_contact_roles": ["department_head", "team_lead"],
                "escalate_to_roles": ["branch_head", "executive"],
            },
        )
    )


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


def _seed_fake_org_assets_and_components(db: Session) -> None:
    """Thêm tài sản / đơn vị chủ quản (chuỗi) — linh kiện không kích hoạt rule cáp ≤6."""
    extras = [
        {
            "asset": {
                "code": "ELV-OFFICE-HN-01",
                "name": "Thang máy văn phòng Hà Nội — tầng hầm",
                "asset_type": "elevator",
                "location": "Tòa nhà A — B1",
                "department_owner": "Ban quản lý tòa nhà / Bộ phận vận hành",
            },
            "component": {
                "code": "CMP-CTRL-001",
                "name": "Bộ điều khiển tầng",
                "component_type": "controller",
                "installed_at": date(2023, 5, 1),
                "expected_lifetime_months": 120,
                "remaining_lifetime_months": 48,
                "last_inspection_at": date(2026, 3, 1),
                "spare_part_code": "SP-CTRL-GEN2",
            },
        },
        {
            "asset": {
                "code": "ELV-MALL-SG-02",
                "name": "Thang cuốn trung tâm thương mại",
                "asset_type": "elevator",
                "location": "SCM — Zone B",
                "department_owner": "Trung tâm thương mại — An toàn & kỹ thuật",
            },
            "component": {
                "code": "CMP-ESCALATOR-CHAIN-01",
                "name": "Xích bước thang cuốn (zone công cộng)",
                "component_type": "escalator_chain",
                "installed_at": date(2024, 1, 10),
                "expected_lifetime_months": 60,
                "remaining_lifetime_months": 36,
                "last_inspection_at": date(2026, 2, 10),
                "spare_part_code": "SP-CHAIN-STD",
            },
        },
    ]
    for row in extras:
        asset = db.scalar(select(Asset).where(Asset.code == row["asset"]["code"]))
        if not asset:
            asset = Asset(**row["asset"])
            db.add(asset)
            db.flush()
        comp = db.scalar(select(Component).where(Component.code == row["component"]["code"]))
        if not comp:
            db.add(Component(asset_id=asset.id, **row["component"]))


def _seed_fake_inventory_items(db: Session) -> None:
    extras = [
        {
            "code": "SP-CTRL-GEN2",
            "name": "Bộ điều khiển thế hệ 2",
            "component_type": "controller",
            "quantity_on_hand": 2,
            "minimum_quantity": 1,
            "lead_time_months": 3,
            "supplier_name": "Nhà cung cấp Singapore",
            "import_required": True,
        },
        {
            "code": "SP-CHAIN-STD",
            "name": "Xích bước tiêu chuẩn",
            "component_type": "escalator_chain",
            "quantity_on_hand": 4,
            "minimum_quantity": 2,
            "lead_time_months": 2,
            "supplier_name": "Nhà cung cấp nội địa",
            "import_required": False,
        },
    ]
    for row in extras:
        if not db.scalar(select(InventoryItem).where(InventoryItem.code == row["code"])):
            db.add(InventoryItem(**row))


def _seed_demo_open_task_and_purchase(db: Session) -> None:
    """Task mở + PR chờ duyệt (demo) — không tạo thêm component khớp rule cáp ≤6."""
    rule = db.scalar(select(Rule).where(Rule.code == "R-ELV-CABLE-001"))
    comp = db.scalar(select(Component).where(Component.code == "CMP-CABLE-001"))
    inv = db.scalar(select(InventoryItem).where(InventoryItem.code == "SP-CABLE-CALIDAS"))
    if not rule or not comp or not inv:
        return

    has_open_task = db.scalar(
        select(InspectionTask).where(
            InspectionTask.component_id == comp.id,
            InspectionTask.rule_id == rule.id,
            InspectionTask.status == "open",
        )
    )
    if not has_open_task:
        db.add(
            InspectionTask(
                asset_id=comp.asset_id,
                component_id=comp.id,
                rule_id=rule.id,
                title="Kiểm tra định kỳ Cáp kéo Calidas 1 (seed demo)",
                description="Task mở giả lập từ seed — phân công đội bảo trì.",
                status="open",
                assigned_to="Đội bảo trì — Nguyễn Văn A (Kỹ thuật)",
                evidence_required_json=rule.evidence_required_json,
                created_by_agent=False,
            )
        )

    has_open_pr = db.scalar(
        select(PurchaseRequest).where(
            PurchaseRequest.component_id == comp.id,
            PurchaseRequest.inventory_item_id == inv.id,
            PurchaseRequest.status.in_(["draft", "waiting_for_approval"]),
        )
    )
    if not has_open_pr:
        db.add(
            PurchaseRequest(
                component_id=comp.id,
                inventory_item_id=inv.id,
                rule_id=rule.id,
                reason=(
                    "Seed demo: cáp Calidas 1 còn 5 tháng tuổi thọ, tồn kho SP-CABLE-CALIDAS = 0, "
                    "lead time nhập khẩu 7 tháng — cần phê duyệt mua thay thế."
                ),
                quantity_requested=1,
                status="waiting_for_approval",
                approval_policy_code="AP-ELV-IMPORT-CEO",
                final_approver="CEO / Ban đầu tư",
                created_by_agent=False,
            )
        )


def _seed_demo_audit_org_context(db: Session) -> None:
    """Một bản ghi audit cố định để minh họa ngữ cảnh org (idempotent theo action)."""
    if db.scalar(select(AuditLog).where(AuditLog.action == "seed_fake_org_bootstrap")):
        return
    db.add(
        AuditLog(
            actor_type="system",
            actor_id="seed_bootstrap",
            action="seed_fake_org_bootstrap",
            entity_type="organization_context",
            entity_id="demo",
            after_json={
                "note": "Dữ liệu giả cho phòng ban / phê duyệt; không thay ontology Neo4j đầy đủ.",
                "departments_in_assets": [
                    "Kỹ thuật",
                    "Ban quản lý tòa nhà / Bộ phận vận hành",
                    "Trung tâm thương mại — An toàn & kỹ thuật",
                ],
            },
            reason="Khởi tạo demo cơ cấu tổ chức (chuỗi department_owner + approver) cho MVP UI.",
        )
    )


def _seed_org_units(db: Session) -> None:
    """Cây đơn vị: holding → branch → department → team (idempotent theo code)."""
    specs: list[tuple[str, str, str, str | None, int]] = [
        ("ORG-HOLDING", "Tập đoàn TwinAI (demo)", "holding", None, 0),
        ("ORG-BR-HN", "Chi nhánh Hà Nội", "branch", "ORG-HOLDING", 10),
        ("ORG-DEPT-OPS-HN", "Phòng Vận hành & bảo trì Hà Nội", "department", "ORG-BR-HN", 20),
        ("ORG-DEPT-SAFE-HN", "Bộ phận An toàn — Hà Nội", "department", "ORG-BR-HN", 30),
        ("ORG-TEAM-MALL", "Đội bảo trì khu Trung tâm thương mại", "team", "ORG-DEPT-OPS-HN", 40),
    ]
    for code, name, kind, parent_code, order in specs:
        if db.scalar(select(OrgUnit).where(OrgUnit.code == code)):
            continue
        parent_id = None
        if parent_code:
            parent = db.scalar(select(OrgUnit).where(OrgUnit.code == parent_code))
            parent_id = parent.id if parent else None
        db.add(OrgUnit(code=code, name=name, level_kind=kind, parent_id=parent_id, sort_order=order))
        db.flush()


def _seed_org_users(db: Session) -> None:
    """Người dùng gắn đơn vị + cấp trên trực tiếp (thứ tự tạo theo cây quản lý)."""
    rows: list[tuple[str, str, str, str, str, str | None, list[str]]] = [
        (
            "USR-CEO-001",
            "Trần Thị An",
            "ceo@demo.twinai.local",
            "Tổng Giám đốc",
            "ORG-HOLDING",
            None,
            ["executive", "final_approver"],
        ),
        (
            "USR-GD-HN-001",
            "Lê Văn Bình",
            "gd.hn@demo.twinai.local",
            "Giám đốc Chi nhánh HN",
            "ORG-BR-HN",
            "USR-CEO-001",
            ["branch_head", "final_approver"],
        ),
        (
            "USR-TP-OPS-001",
            "Phạm Minh Chi",
            "tp.ops@demo.twinai.local",
            "Trưởng phòng Vận hành & bảo trì",
            "ORG-DEPT-OPS-HN",
            "USR-GD-HN-001",
            ["department_head", "approver"],
        ),
        (
            "USR-KTV-001",
            "Hoàng Quốc Dũng",
            "ktv01@demo.twinai.local",
            "Kỹ thuật viên hiện trường",
            "ORG-DEPT-OPS-HN",
            "USR-TP-OPS-001",
            ["technician", "field"],
        ),
        (
            "USR-LEAD-MALL-001",
            "Đỗ Thùy Giang",
            "lead.mall@demo.twinai.local",
            "Trưởng đội TT thương mại",
            "ORG-TEAM-MALL",
            "USR-TP-OPS-001",
            ["team_lead", "field"],
        ),
        (
            "USR-SAFE-001",
            "Ngô An Toàn",
            "safe.hn@demo.twinai.local",
            "Chuyên viên an toàn",
            "ORG-DEPT-SAFE-HN",
            "USR-GD-HN-001",
            ["safety_officer", "compliance"],
        ),
    ]
    for ucode, fname, email, title, ou_code, mgr_code, tags in rows:
        if db.scalar(select(OrgUser).where(OrgUser.user_code == ucode)):
            continue
        unit = db.scalar(select(OrgUnit).where(OrgUnit.code == ou_code))
        manager = db.scalar(select(OrgUser).where(OrgUser.user_code == mgr_code)) if mgr_code else None
        db.add(
            OrgUser(
                user_code=ucode,
                full_name=fname,
                email=email,
                job_title=title,
                org_unit_id=unit.id if unit else None,
                manager_user_id=manager.id if manager else None,
                role_tags=tags,
                password_hash=bcrypt.hashpw(b"demo", bcrypt.gensalt()).decode("utf-8"),
                is_active=True,
            )
        )
        db.flush()


def _seed_asset_contact_assignments(db: Session) -> None:
    """Gán primary/backup theo từng asset (ưu tiên trước fallback role_tags trong build_asset_contacts)."""
    specs: list[tuple[str, str, str, int]] = [
        ("ELV-CALIDAS-01", "USR-LEAD-MALL-001", "primary", 0),
        ("ELV-CALIDAS-01", "USR-TP-OPS-001", "backup", 0),
        ("ELV-CALIDAS-02", "USR-KTV-001", "primary", 0),
        ("ELV-CALIDAS-02", "USR-GD-HN-001", "backup", 0),
        ("ELV-SERVICE-01", "USR-KTV-001", "primary", 0),
        ("ELV-SERVICE-01", "USR-SAFE-001", "backup", 0),
    ]
    for asset_code, user_code, kind, order in specs:
        asset = db.scalar(select(Asset).where(Asset.code == asset_code))
        user = db.scalar(select(OrgUser).where(OrgUser.user_code == user_code))
        if not asset or not user:
            continue
        exists = db.scalar(
            select(AssetContactAssignment).where(
                AssetContactAssignment.asset_id == asset.id,
                AssetContactAssignment.contact_kind == kind,
                AssetContactAssignment.org_user_id == user.id,
            )
        )
        if exists:
            continue
        db.add(
            AssetContactAssignment(
                asset_id=asset.id,
                org_user_id=user.id,
                contact_kind=kind,
                sort_order=order,
            )
        )
        db.flush()
