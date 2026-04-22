import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def uuid4() -> str:
    return str(uuid.uuid4())


JSONType = JSON().with_variant(JSONB, "postgresql")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(80), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    department_owner: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    components: Mapped[list["Component"]] = relationship(back_populates="asset")


class Component(Base):
    __tablename__ = "components"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    component_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    installed_at: Mapped[date | None] = mapped_column(Date)
    expected_lifetime_months: Mapped[int | None] = mapped_column(Integer)
    remaining_lifetime_months: Mapped[int | None] = mapped_column(Integer)
    last_inspection_at: Mapped[date | None] = mapped_column(Date)
    spare_part_code: Mapped[str | None] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    asset: Mapped[Asset] = relationship(back_populates="components")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    component_type: Mapped[str] = mapped_column(String(80), nullable=False)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    minimum_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lead_time_months: Mapped[int | None] = mapped_column(Integer)
    supplier_name: Mapped[str | None] = mapped_column(String(255))
    import_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Manual(Base):
    __tablename__ = "manuals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department_owner: Mapped[str | None] = mapped_column(String(120))
    file_object_key: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str | None] = mapped_column(String(40))
    version: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(120), nullable=False)
    condition_json: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    action_json: Mapped[list[str]] = mapped_column(JSONType, nullable=False)
    evidence_required_json: Mapped[list[str]] = mapped_column(JSONType, nullable=False, default=list)
    source_manual_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("manuals.id"))
    owner_department: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class InspectionTask(Base):
    __tablename__ = "inspection_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), nullable=False)
    component_id: Mapped[str] = mapped_column(String(36), ForeignKey("components.id"), nullable=False)
    rule_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("rules.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="open")
    assigned_to: Mapped[str | None] = mapped_column(String(120))
    evidence_required_json: Mapped[list[str]] = mapped_column(JSONType, nullable=False, default=list)
    evidence_result_json: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False, default=dict)
    created_by_agent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    component_id: Mapped[str] = mapped_column(String(36), ForeignKey("components.id"), nullable=False)
    inventory_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("inventory_items.id"), nullable=False)
    rule_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("rules.id"))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    quantity_requested: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft")
    approval_policy_code: Mapped[str | None] = mapped_column(String(80))
    final_approver: Mapped[str | None] = mapped_column(String(120))
    created_by_agent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    run_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False, default=dict)
    output_summary: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    actor_type: Mapped[str] = mapped_column(String(40), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(120))
    before_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    after_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
