from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AgentRun,
    Asset,
    AuditLog,
    Component,
    InspectionTask,
    InventoryItem,
    PurchaseRequest,
    Rule,
)


class AssetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_assets(self) -> list[Asset]:
        return list(self.db.scalars(select(Asset).options(selectinload(Asset.components)).order_by(Asset.code)))

    def get_by_id(self, asset_id: str) -> Asset | None:
        return self.db.get(Asset, asset_id)

    def get_by_code(self, code: str) -> Asset | None:
        return self.db.scalar(select(Asset).where(Asset.code == code))


class ReasoningRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_active_components(self) -> list[Component]:
        return list(self.db.scalars(select(Component).where(Component.status == "active").order_by(Component.code)))

    def list_approved_rules(self) -> list[Rule]:
        return list(self.db.scalars(select(Rule).where(Rule.status == "approved").order_by(Rule.code)))

    def get_inventory_by_spare_part_code(self, code: str | None) -> InventoryItem | None:
        if not code:
            return None
        return self.db.scalar(select(InventoryItem).where(InventoryItem.code == code))

    def get_open_task(self, component_id: str, rule_id: str) -> InspectionTask | None:
        return self.db.scalar(
            select(InspectionTask).where(
                InspectionTask.component_id == component_id,
                InspectionTask.rule_id == rule_id,
                InspectionTask.status == "open",
            )
        )

    def get_open_purchase_request(self, component_id: str, inventory_item_id: str) -> PurchaseRequest | None:
        return self.db.scalar(
            select(PurchaseRequest).where(
                PurchaseRequest.component_id == component_id,
                PurchaseRequest.inventory_item_id == inventory_item_id,
                PurchaseRequest.status.in_(["draft", "waiting_for_approval"]),
            )
        )

    def create_agent_run(self) -> AgentRun:
        run = AgentRun(run_type="elevator_cable_reasoning", status="running", input_snapshot={}, output_summary={})
        self.db.add(run)
        self.db.flush()
        return run

    def create_task(self, component: Component, rule: Rule) -> InspectionTask:
        task = InspectionTask(
            asset_id=component.asset_id,
            component_id=component.id,
            rule_id=rule.id,
            title=f"Kiểm tra {component.name}",
            description=f"{component.name} còn {component.remaining_lifetime_months} tháng tuổi thọ. Cần kiểm tra theo rule {rule.code}.",
            assigned_to="technical_team",
            evidence_required_json=rule.evidence_required_json,
            created_by_agent=True,
        )
        self.db.add(task)
        self.db.flush()
        return task

    def create_purchase_request(
        self,
        component: Component,
        inventory_item: InventoryItem,
        rule: Rule,
    ) -> PurchaseRequest:
        reason = (
            f"{component.name} còn {component.remaining_lifetime_months} tháng tuổi thọ, "
            f"tồn kho {inventory_item.name} = {inventory_item.quantity_on_hand}, "
            f"lead time = {inventory_item.lead_time_months} tháng."
        )
        request = PurchaseRequest(
            component_id=component.id,
            inventory_item_id=inventory_item.id,
            rule_id=rule.id,
            reason=reason,
            quantity_requested=1,
            status="draft",
            approval_policy_code="AP-ELV-IMPORT-CEO" if inventory_item.import_required else "AP-ELV-LOCAL-OPS",
            final_approver="CEO" if inventory_item.import_required else "Giám đốc vận hành",
            created_by_agent=True,
        )
        self.db.add(request)
        self.db.flush()
        return request

    def add_audit(self, action: str, entity_type: str, entity_id: str, reason: str, after: dict | None = None) -> AuditLog:
        audit = AuditLog(
            actor_type="agent",
            actor_id="reasoning_engine",
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            after_json=after,
            reason=reason,
        )
        self.db.add(audit)
        self.db.flush()
        return audit

