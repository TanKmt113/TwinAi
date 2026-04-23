from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ComponentRead(BaseModel):
    id: str
    code: str
    name: str
    component_type: str
    remaining_lifetime_months: int | None
    spare_part_code: str | None
    status: str

    model_config = {"from_attributes": True}


class AssetRead(BaseModel):
    id: str
    code: str
    name: str
    asset_type: str
    location: str | None
    department_owner: str | None
    status: str
    components: list[ComponentRead] = []

    model_config = {"from_attributes": True}


class InspectionTaskRead(BaseModel):
    id: str
    title: str
    description: str | None
    status: str
    assigned_to: str | None
    evidence_required_json: list[str]
    created_by_agent: bool

    model_config = {"from_attributes": True}


class PurchaseRequestRead(BaseModel):
    id: str
    component_id: str
    inventory_item_id: str
    rule_id: str | None = None
    reason: str
    quantity_requested: int
    status: str
    approval_policy_code: str | None
    final_approver: str | None
    first_approved_at: datetime | None = None
    first_approved_by: str | None = None
    created_by_agent: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PurchaseRequestDetailRead(PurchaseRequestRead):
    """Bổ sung asset/component để UI routing (contacts) không cần gọi thêm lookup."""

    asset_id: str | None = None
    asset_code: str | None = None
    component_code: str | None = None


class WorkflowActorBody(BaseModel):
    actor_type: str = "user"
    actor_id: str = "demo_user"
    note: str | None = None


class EscalationCheckBody(BaseModel):
    """Kiểm tra SLA acknowledge → có cần escalate (demo theo policy)."""

    asset_id: str | None = None
    policy_code: str = "ELV-CABLE-ESCALATION-01"
    opened_at: datetime
    acknowledged_at: datetime | None = None
    dry_run: bool = True


class EscalationCheckResponse(BaseModel):
    should_escalate: bool
    reason: str
    minutes_open: float
    acknowledge_sla_minutes: int
    suggested_escalation_contacts: list[dict[str, Any]] = Field(default_factory=list)
    audit_recorded: bool = False


class LoginRequest(BaseModel):
    user_code: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_code: str
    roles: list[str] = Field(default_factory=list)


class AuditLogRead(BaseModel):
    id: str
    actor_type: str
    actor_id: str | None
    action: str
    entity_type: str
    entity_id: str | None
    before_json: dict[str, Any] | None
    after_json: dict[str, Any] | None
    reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ManualRead(BaseModel):
    id: str
    code: str
    title: str
    department_owner: str | None
    file_name: str
    file_type: str | None
    version: str | None
    status: str
    linked_rule_code: str | None = None
    neo4j_sync: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class ManualChunkRead(BaseModel):
    id: str
    manual_id: str
    chunk_index: int
    heading: str | None
    page_number: int | None
    chunk_text: str
    metadata_json: dict[str, Any]

    model_config = {"from_attributes": True}


class AgentRunRead(BaseModel):
    id: str
    run_type: str
    status: str
    input_snapshot: dict[str, Any]
    output_summary: dict[str, Any]
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class ReasoningRunResponse(BaseModel):
    run_id: str
    status: str
    findings: list[dict[str, Any]]
    created_tasks: list[InspectionTaskRead]
    created_purchase_requests: list[PurchaseRequestRead]
    audit_events: list[dict[str, Any]]


class ChatQuery(BaseModel):
    question: str


class Citation(BaseModel):
    type: str
    code: str
    title: str


class ChatResponse(BaseModel):
    intent: str
    conclusion: str
    evidence: list[str]
    recommended_actions: list[str]
    missing_data: list[str]
    citations: list[Citation]
    agent_mode: str = "rule_fallback"
    tool_calls: list[str] = Field(default_factory=list)


class OrgUnitRead(BaseModel):
    id: str
    code: str
    name: str
    level_kind: str
    parent_id: str | None
    sort_order: int

    model_config = {"from_attributes": True}


class OrgUserRead(BaseModel):
    id: str
    user_code: str
    full_name: str
    email: str | None
    job_title: str | None
    org_unit_id: str | None
    org_unit_code: str | None = None
    org_unit_name: str | None = None
    manager_user_id: str | None
    manager_user_code: str | None = None
    role_tags: list[str]
    is_active: bool

    model_config = {"from_attributes": True}
