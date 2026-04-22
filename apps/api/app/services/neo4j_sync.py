from contextlib import suppress
from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Asset, Component, InspectionTask, InventoryItem, Manual, PurchaseRequest, Rule


class Neo4jSyncService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def is_enabled(self) -> bool:
        return self.settings.enable_neo4j_sync

    def sync_seed_graph(self, db: Session) -> dict[str, Any]:
        if not self.is_enabled():
            return {"enabled": False, "synced": False}

        try:
            with self._driver() as driver:
                with driver.session() as session:
                    self._ensure_constraints(session)
                    for asset in db.query(Asset).all():
                        session.execute_write(self._upsert_asset, asset)
                    for manual in db.query(Manual).all():
                        session.execute_write(self._upsert_manual, manual)
                    for rule in db.query(Rule).all():
                        session.execute_write(self._upsert_rule, rule)
                    for item in db.query(InventoryItem).all():
                        session.execute_write(self._upsert_inventory, item)
                    for component in db.query(Component).all():
                        session.execute_write(self._upsert_component, component)
                    for request in db.query(PurchaseRequest).all():
                        session.execute_write(self._upsert_purchase_request, request)
            return {"enabled": True, "synced": True}
        except (Neo4jError, ServiceUnavailable, OSError) as exc:
            return {"enabled": True, "synced": False, "error": str(exc)}

    def sync_task_and_request(
        self,
        task: InspectionTask | None = None,
        request: PurchaseRequest | None = None,
    ) -> dict[str, Any]:
        if not self.is_enabled():
            return {"enabled": False, "synced": False}

        try:
            with self._driver() as driver:
                with driver.session() as session:
                    if task:
                        session.execute_write(self._upsert_task, task)
                    if request:
                        session.execute_write(self._upsert_purchase_request, request)
            return {"enabled": True, "synced": True}
        except (Neo4jError, ServiceUnavailable, OSError) as exc:
            return {"enabled": True, "synced": False, "error": str(exc)}

    def get_asset_context(self, asset_code: str) -> dict[str, Any]:
        if not self.is_enabled():
            return {}

        query = """
        MATCH (a:Asset {code: $asset_code})-[:HAS_COMPONENT]->(c:Component)
        OPTIONAL MATCH (c)-[:APPLIES_RULE]->(r:Rule)
        OPTIONAL MATCH (r)-[:BASED_ON]->(m:Manual)
        OPTIONAL MATCH (c)-[:REQUIRES_SPARE_PART]->(sp:SparePart)-[:STORED_AS]->(inv:InventoryItem)
        OPTIONAL MATCH (pr:PurchaseRequest)-[:FOR_COMPONENT]->(c)
        OPTIONAL MATCH (pr)-[:REQUIRES_APPROVAL]->(ap:ApprovalPolicy)-[:FINAL_APPROVER]->(u:User)
        RETURN a, collect(DISTINCT c) AS components, collect(DISTINCT r) AS rules,
               collect(DISTINCT m) AS manuals, collect(DISTINCT sp) AS spare_parts,
               collect(DISTINCT inv) AS inventory_items, collect(DISTINCT pr) AS purchase_requests,
               collect(DISTINCT ap) AS approval_policies, collect(DISTINCT u) AS approvers
        """

        try:
            with self._driver() as driver:
                with driver.session() as session:
                    record = session.run(query, asset_code=asset_code).single()
                    if not record:
                        return {}
                    return {key: _node_data(record[key]) for key in record.keys()}
        except (Neo4jError, ServiceUnavailable, OSError):
            return {}

    def _driver(self):
        return GraphDatabase.driver(
            self.settings.neo4j_uri,
            auth=(self.settings.neo4j_user, self.settings.neo4j_password),
        )

    @staticmethod
    def _ensure_constraints(tx) -> None:
        constraints = [
            "CREATE CONSTRAINT asset_code IF NOT EXISTS FOR (n:Asset) REQUIRE n.code IS UNIQUE",
            "CREATE CONSTRAINT component_code IF NOT EXISTS FOR (n:Component) REQUIRE n.code IS UNIQUE",
            "CREATE CONSTRAINT rule_code IF NOT EXISTS FOR (n:Rule) REQUIRE n.code IS UNIQUE",
            "CREATE CONSTRAINT manual_code IF NOT EXISTS FOR (n:Manual) REQUIRE n.code IS UNIQUE",
            "CREATE CONSTRAINT inventory_code IF NOT EXISTS FOR (n:InventoryItem) REQUIRE n.code IS UNIQUE",
            "CREATE CONSTRAINT purchase_request_id IF NOT EXISTS FOR (n:PurchaseRequest) REQUIRE n.id IS UNIQUE",
        ]
        for constraint in constraints:
            with suppress(Neo4jError):
                tx.run(constraint)

    @staticmethod
    def _upsert_asset(tx, asset: Asset) -> None:
        tx.run(
            """
            MERGE (a:Asset {code: $code})
            SET a.id = $id, a.name = $name, a.asset_type = $asset_type,
                a.location = $location, a.department_owner = $department_owner, a.status = $status
            MERGE (d:Department {name: $department_owner})
            MERGE (a)-[:OWNED_BY]->(d)
            """,
            id=asset.id,
            code=asset.code,
            name=asset.name,
            asset_type=asset.asset_type,
            location=asset.location,
            department_owner=asset.department_owner or "Unknown",
            status=asset.status,
        )

    @staticmethod
    def _upsert_component(tx, component: Component) -> None:
        tx.run(
            """
            MATCH (a:Asset {id: $asset_id})
            MERGE (c:Component {code: $code})
            SET c.id = $id, c.name = $name, c.component_type = $component_type,
                c.remaining_lifetime_months = $remaining_lifetime_months,
                c.spare_part_code = $spare_part_code, c.status = $status
            MERGE (ct:ComponentType {name: $component_type})
            MERGE (a)-[:HAS_COMPONENT]->(c)
            MERGE (c)-[:HAS_TYPE]->(ct)
            WITH c
            MATCH (r:Rule {code: "R-ELV-CABLE-001"})
            WHERE $component_type = "cable"
            MERGE (c)-[:APPLIES_RULE]->(r)
            WITH c
            MATCH (inv:InventoryItem {code: $spare_part_code})
            MERGE (sp:SparePart {code: $spare_part_code})
            SET sp.name = inv.name
            MERGE (c)-[:REQUIRES_SPARE_PART]->(sp)
            MERGE (sp)-[:STORED_AS]->(inv)
            """,
            id=component.id,
            asset_id=component.asset_id,
            code=component.code,
            name=component.name,
            component_type=component.component_type,
            remaining_lifetime_months=component.remaining_lifetime_months,
            spare_part_code=component.spare_part_code,
            status=component.status,
        )

    @staticmethod
    def _upsert_manual(tx, manual: Manual) -> None:
        tx.run(
            "MERGE (m:Manual {code: $code}) SET m.id = $id, m.title = $title, m.status = $status",
            id=manual.id,
            code=manual.code,
            title=manual.title,
            status=manual.status,
        )

    @staticmethod
    def _upsert_rule(tx, rule: Rule) -> None:
        tx.run(
            """
            MERGE (r:Rule {code: $code})
            SET r.id = $id, r.name = $name, r.domain = $domain, r.status = $status
            WITH r
            MATCH (m:Manual {id: $manual_id})
            MERGE (r)-[:BASED_ON]->(m)
            """,
            id=rule.id,
            code=rule.code,
            name=rule.name,
            domain=rule.domain,
            status=rule.status,
            manual_id=rule.source_manual_id,
        )

    @staticmethod
    def _upsert_inventory(tx, item: InventoryItem) -> None:
        tx.run(
            """
            MERGE (inv:InventoryItem {code: $code})
            SET inv.id = $id, inv.name = $name, inv.component_type = $component_type,
                inv.quantity_on_hand = $quantity_on_hand, inv.minimum_quantity = $minimum_quantity,
                inv.lead_time_months = $lead_time_months, inv.supplier_name = $supplier_name,
                inv.import_required = $import_required
            """,
            id=item.id,
            code=item.code,
            name=item.name,
            component_type=item.component_type,
            quantity_on_hand=item.quantity_on_hand,
            minimum_quantity=item.minimum_quantity,
            lead_time_months=item.lead_time_months,
            supplier_name=item.supplier_name,
            import_required=item.import_required,
        )

    @staticmethod
    def _upsert_task(tx, task: InspectionTask) -> None:
        tx.run(
            """
            MATCH (c:Component {id: $component_id})
            MERGE (t:InspectionTask {id: $id})
            SET t.title = $title, t.status = $status, t.created_by_agent = $created_by_agent
            MERGE (c)-[:HAS_INSPECTION_TASK]->(t)
            """,
            id=task.id,
            component_id=task.component_id,
            title=task.title,
            status=task.status,
            created_by_agent=task.created_by_agent,
        )

    @staticmethod
    def _upsert_purchase_request(tx, request: PurchaseRequest) -> None:
        tx.run(
            """
            MATCH (c:Component {id: $component_id})
            MERGE (pr:PurchaseRequest {id: $id})
            SET pr.reason = $reason, pr.status = $status, pr.final_approver = $final_approver
            MERGE (pr)-[:FOR_COMPONENT]->(c)
            MERGE (ap:ApprovalPolicy {code: $approval_policy_code})
            SET ap.name = $approval_policy_code
            MERGE (u:User {id: $final_approver})
            SET u.name = $final_approver
            MERGE (pr)-[:REQUIRES_APPROVAL]->(ap)
            MERGE (ap)-[:FINAL_APPROVER]->(u)
            """,
            id=request.id,
            component_id=request.component_id,
            reason=request.reason,
            status=request.status,
            approval_policy_code=request.approval_policy_code or "UNKNOWN",
            final_approver=request.final_approver or "UNKNOWN",
        )


def _node_data(value: Any) -> Any:
    if isinstance(value, list):
        return [dict(item) for item in value if item is not None]
    if value is None:
        return None
    return dict(value)

