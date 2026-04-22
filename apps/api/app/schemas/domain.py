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
    reason: str
    quantity_requested: int
    status: str
    approval_policy_code: str | None
    final_approver: str | None
    created_by_agent: bool

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
