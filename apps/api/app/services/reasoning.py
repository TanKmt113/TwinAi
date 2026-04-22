from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import AgentRun, Component, InspectionTask, InventoryItem, PurchaseRequest, Rule
from app.schemas import InspectionTaskRead, PurchaseRequestRead, ReasoningRunResponse
from app.services.neo4j_sync import Neo4jSyncService
from app.services.repositories import ReasoningRepository


class ReasoningEngine:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ReasoningRepository(db)
        self.neo4j = Neo4jSyncService()

    def run(self) -> ReasoningRunResponse:
        run = self.repo.create_agent_run()
        findings: list[dict[str, Any]] = []
        created_tasks: list[InspectionTask] = []
        created_purchase_requests: list[PurchaseRequest] = []
        audit_events: list[dict[str, Any]] = []

        try:
            for component in self.repo.list_active_components():
                for rule in self.repo.list_approved_rules():
                    if not self._matches_rule(component, rule):
                        continue

                    finding = self._build_finding(component, rule)
                    findings.append(finding)

                    task = self._ensure_task(component, rule, audit_events)
                    if task and task not in created_tasks:
                        created_tasks.append(task)

                    inventory_item = self.repo.get_inventory_by_spare_part_code(component.spare_part_code)
                    if inventory_item and self._needs_purchase(component, inventory_item):
                        request = self._ensure_purchase_request(component, inventory_item, rule, audit_events)
                        if request and request not in created_purchase_requests:
                            created_purchase_requests.append(request)

            run.status = "completed"
            run.finished_at = datetime.now(UTC)
            run.output_summary = {
                "findings_count": len(findings),
                "created_tasks_count": len(created_tasks),
                "created_purchase_requests_count": len(created_purchase_requests),
            }
            self.db.commit()

            return ReasoningRunResponse(
                run_id=run.id,
                status=run.status,
                findings=findings,
                created_tasks=[InspectionTaskRead.model_validate(task) for task in created_tasks],
                created_purchase_requests=[PurchaseRequestRead.model_validate(request) for request in created_purchase_requests],
                audit_events=audit_events,
            )
        except Exception as exc:
            run.status = "failed"
            run.finished_at = datetime.now(UTC)
            run.error_message = str(exc)
            self.db.commit()
            raise

    def _matches_rule(self, component: Component, rule: Rule) -> bool:
        condition = rule.condition_json
        expected_type = condition.get("component_type")
        remaining_lte = condition.get("remaining_lifetime_months_lte")

        if expected_type and component.component_type != expected_type:
            return False
        if remaining_lte is None or component.remaining_lifetime_months is None:
            return False
        return component.remaining_lifetime_months <= remaining_lte

    def _build_finding(self, component: Component, rule: Rule) -> dict[str, Any]:
        return {
            "rule_code": rule.code,
            "component_code": component.code,
            "asset_id": component.asset_id,
            "reason": (
                f"{component.name} còn {component.remaining_lifetime_months} tháng tuổi thọ, "
                f"nhỏ hơn hoặc bằng ngưỡng {rule.condition_json.get('remaining_lifetime_months_lte')} tháng."
            ),
            "actions": rule.action_json,
        }

    def _ensure_task(self, component: Component, rule: Rule, audit_events: list[dict[str, Any]]) -> InspectionTask | None:
        existing = self.repo.get_open_task(component.id, rule.id)
        if existing:
            return existing

        task = self.repo.create_task(component, rule)
        sync_result = self.neo4j.sync_task_and_request(task=task)
        audit = self.repo.add_audit(
            action="agent_created_inspection_task",
            entity_type="inspection_task",
            entity_id=task.id,
            reason=f"Tạo task kiểm tra từ rule {rule.code} cho {component.code}.",
            after={"task_id": task.id, "neo4j_sync": sync_result},
        )
        audit_events.append({"action": audit.action, "entity_type": audit.entity_type, "entity_id": audit.entity_id})
        return task

    def _needs_purchase(self, component: Component, inventory_item: InventoryItem) -> bool:
        if component.remaining_lifetime_months is None or inventory_item.lead_time_months is None:
            return False
        return inventory_item.quantity_on_hand <= 0 and inventory_item.lead_time_months > component.remaining_lifetime_months

    def _ensure_purchase_request(
        self,
        component: Component,
        inventory_item: InventoryItem,
        rule: Rule,
        audit_events: list[dict[str, Any]],
    ) -> PurchaseRequest | None:
        existing = self.repo.get_open_purchase_request(component.id, inventory_item.id)
        if existing:
            return existing

        request = self.repo.create_purchase_request(component, inventory_item, rule)
        sync_result = self.neo4j.sync_task_and_request(request=request)
        audit = self.repo.add_audit(
            action="agent_created_purchase_request",
            entity_type="purchase_request",
            entity_id=request.id,
            reason=f"Tạo purchase request từ rule {rule.code} cho {inventory_item.code}.",
            after={"purchase_request_id": request.id, "neo4j_sync": sync_result},
        )
        audit_events.append({"action": audit.action, "entity_type": audit.entity_type, "entity_id": audit.entity_id})
        return request

