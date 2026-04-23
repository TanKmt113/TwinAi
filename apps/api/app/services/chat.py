import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AgentRun, Asset, Component, InspectionTask, InventoryItem, Manual, PurchaseRequest, Rule
from app.schemas import ChatResponse, Citation
from app.services.llm_agent import LlmAgentClient, LlmAgentError
from app.services.neo4j_sync import Neo4jSyncService
from app.services.rag import RagService
from app.services.routing_context import build_asset_contacts


class ChatService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.rag = RagService(db)

    def answer(self, question: str) -> ChatResponse:
        intent = self._classify(question)
        tool_context = self._build_tool_context(question, intent)

        if intent == "out_of_scope":
            response = ChatResponse(
                intent=intent,
                conclusion="Không đủ dữ liệu để trả lời câu hỏi này trong Ontology MVP hiện tại.",
                evidence=[],
                recommended_actions=["Bổ sung domain dữ liệu/rule liên quan nếu câu hỏi này là nhu cầu nghiệp vụ thật."],
                missing_data=["Không có thực thể, rule hoặc manual liên quan trong phạm vi thang máy."],
                citations=[],
                agent_mode="guardrail_out_of_scope",
                tool_calls=tool_context["tool_calls"],
            )
            self._record_agent_run(question, intent, tool_context, response, llm_used=False)
            return response

        llm_client = LlmAgentClient()
        if llm_client.is_configured():
            try:
                agent_payload = llm_client.generate_chat_response(
                    question=question,
                    intent=intent,
                    tool_context=self._serializable_context(tool_context),
                )
                response = self._response_from_agent_payload(
                    intent=intent,
                    payload=agent_payload,
                    fallback_citations=tool_context["citations"],
                    tool_calls=tool_context["tool_calls"],
                    agent_mode=f"llm_tool_agent:{llm_client.provider_name()}",
                )
                self._record_agent_run(question, intent, tool_context, response, llm_used=True)
                return response
            except LlmAgentError as exc:
                response = self._build_rule_response(
                    intent=intent,
                    tool_context=tool_context,
                    agent_mode="rule_fallback_after_llm_error",
                    extra_missing_data=[f"LLM agent không chạy được: {exc}"],
                )
                self._record_agent_run(question, intent, tool_context, response, llm_used=False, error=str(exc))
                return response

        response = self._build_rule_response(
            intent=intent,
            tool_context=tool_context,
            agent_mode="rule_fallback_no_llm_key",
        )
        self._record_agent_run(question, intent, tool_context, response, llm_used=False)
        return response

    def _build_tool_context(self, question: str, intent: str) -> dict[str, Any]:
        requested_asset_code = self._extract_asset_code(question)
        ontology_context = self._get_ontology_context(requested_asset_code)
        all_assets = list(self.db.scalars(select(Asset).order_by(Asset.code)))

        asset_component_counts = []
        for asset in all_assets:
            components = list(self.db.scalars(select(Component).where(Component.asset_id == asset.id).order_by(Component.code)))
            asset_component_counts.append(
                {
                    "asset_code": asset.code,
                    "asset_name": asset.name,
                    "component_count": len(components),
                    "component_codes": [component.code for component in components],
                    "component_names": [component.name for component in components],
                }
            )

        if intent == "asset_component_count_query":
            return {
                "intent": intent,
                "requested_asset_code": requested_asset_code,
                "asset_risks": [],
                "asset_component_counts": asset_component_counts,
                "ontology_context": ontology_context,
                "rule": None,
                "manual_chunks": [],
                "open_tasks": [],
                "purchase_requests": [],
                "approval_policy": [],
                "citations": [],
                "tool_calls": [
                    "classify_intent",
                    "get_asset_component_counts",
                    "get_asset_ontology",
                ],
            }

        tool_calls = [
            "classify_intent",
            "get_asset_risks",
            "get_asset_ontology",
            "get_rule",
            "search_manual_chunks",
            "get_purchase_request_reason",
            "get_approval_policy",
        ]

        risky_components = list(
            self.db.scalars(
                select(Component).where(
                    Component.component_type == "cable",
                    Component.remaining_lifetime_months <= 6,
                )
            )
        )
        rule = self.db.scalar(select(Rule).where(Rule.code == "R-ELV-CABLE-001"))
        manual = self.db.get(Manual, rule.source_manual_id) if rule and rule.source_manual_id else None
        if not manual:
            manual = self.db.scalar(select(Manual).where(Manual.code == "MAN-ELV-001"))
        chunks = self.rag.search_chunks(question)
        tasks = list(self.db.scalars(select(InspectionTask).where(InspectionTask.status == "open")))
        purchase_requests = list(
            self.db.scalars(select(PurchaseRequest).where(PurchaseRequest.status.in_(["draft", "waiting_for_approval"])))
        )
        inventory_items = list(self.db.scalars(select(InventoryItem).order_by(InventoryItem.code)))

        risk_rows = []
        for component in risky_components:
            asset = self.db.get(Asset, component.asset_id)
            inventory = next((item for item in inventory_items if item.code == component.spare_part_code), None)
            risk_rows.append(
                {
                    "asset_code": asset.code if asset else None,
                    "asset_name": asset.name if asset else None,
                    "component_code": component.code,
                    "component_name": component.name,
                    "component_type": component.component_type,
                    "remaining_lifetime_months": component.remaining_lifetime_months,
                    "spare_part_code": component.spare_part_code,
                    "inventory_quantity_on_hand": inventory.quantity_on_hand if inventory else None,
                    "inventory_lead_time_months": inventory.lead_time_months if inventory else None,
                }
            )

        citations = []
        if rule:
            citations.append(Citation(type="rule", code=rule.code, title=rule.name))
        if manual:
            citations.append(Citation(type="manual", code=manual.code, title=manual.title))
        citations.extend(
            [
                Citation(type="manual_chunk", code=f"chunk-{chunk.chunk_index}", title=chunk.heading or "Manual chunk")
                for chunk in chunks[:2]
            ]
        )

        asset_routing_contacts: list[dict[str, Any]] = []
        seen_asset_ids: set[str] = set()
        for component in risky_components:
            if component.asset_id in seen_asset_ids:
                continue
            seen_asset_ids.add(component.asset_id)
            asset_row = self.db.get(Asset, component.asset_id)
            if asset_row:
                asset_routing_contacts.append(build_asset_contacts(self.db, asset_row))
        if requested_asset_code:
            focus_asset = self.db.scalar(select(Asset).where(Asset.code == requested_asset_code))
            if focus_asset and focus_asset.id not in seen_asset_ids:
                asset_routing_contacts.append(build_asset_contacts(self.db, focus_asset))

        routing_guardrails = {
            "missing_notification_routing": any(row.get("missing_notification_routing") for row in asset_routing_contacts),
        }

        return {
            "intent": intent,
            "requested_asset_code": requested_asset_code,
            "asset_risks": risk_rows,
            "asset_component_counts": asset_component_counts,
            "ontology_context": ontology_context,
            "rule": {
                "code": rule.code,
                "name": rule.name,
                "condition_json": rule.condition_json,
                "action_json": rule.action_json,
                "evidence_required_json": rule.evidence_required_json,
            }
            if rule
            else None,
            "manual_chunks": [
                {
                    "code": f"chunk-{chunk.chunk_index}",
                    "heading": chunk.heading,
                    "text": chunk.chunk_text[:900],
                    "metadata": chunk.metadata_json,
                }
                for chunk in chunks[:5]
            ],
            "open_tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "assigned_to": task.assigned_to,
                    "created_by_agent": task.created_by_agent,
                }
                for task in tasks
            ],
            "purchase_requests": [
                {
                    "id": request.id,
                    "reason": request.reason,
                    "status": request.status,
                    "approval_policy_code": request.approval_policy_code,
                    "final_approver": request.final_approver,
                    "created_by_agent": request.created_by_agent,
                }
                for request in purchase_requests
            ],
            "approval_policy": self._approval_policy_from_requests(purchase_requests),
            "asset_routing_contacts": asset_routing_contacts,
            "routing_guardrails": routing_guardrails,
            "citations": citations,
            "tool_calls": tool_calls + ["get_asset_notification_routing"],
        }

    def _build_rule_response(
        self,
        intent: str,
        tool_context: dict[str, Any],
        agent_mode: str,
        extra_missing_data: list[str] | None = None,
    ) -> ChatResponse:
        evidence = []
        asset_risks = tool_context["asset_risks"]
        asset_component_counts = tool_context["asset_component_counts"]
        if intent == "asset_component_count_query":
            target_row = self._pick_asset_component_count(
                rows=asset_component_counts,
                requested_asset_code=tool_context["requested_asset_code"],
            )
            if target_row:
                evidence.append(
                    f"{target_row['asset_name']} ({target_row['asset_code']}) hiện có {target_row['component_count']} linh kiện theo dõi."
                )
                if target_row["component_names"]:
                    evidence.append("Danh sách linh kiện: " + ", ".join(target_row["component_names"]) + ".")
            elif asset_component_counts:
                total_components = sum(item["component_count"] for item in asset_component_counts)
                evidence.append(f"Hệ thống đang theo dõi {len(asset_component_counts)} tài sản và tổng {total_components} linh kiện.")
                for item in asset_component_counts:
                    evidence.append(f"{item['asset_code']}: {item['component_count']} linh kiện.")
        elif asset_risks:
            evidence.extend(
                [
                    f"{risk['component_name']} còn {risk['remaining_lifetime_months']} tháng tuổi thọ."
                    for risk in asset_risks
                ]
            )
        if intent != "asset_component_count_query" and tool_context["open_tasks"]:
            evidence.append(f"Hệ thống có {len(tool_context['open_tasks'])} task kiểm tra đang mở.")
        if intent != "asset_component_count_query" and tool_context["purchase_requests"]:
            evidence.extend([f"Purchase request: {request['reason']}" for request in tool_context["purchase_requests"]])
        if intent != "asset_component_count_query" and tool_context["manual_chunks"]:
            evidence.append(f"Tìm thấy {len(tool_context['manual_chunks'])} đoạn manual liên quan.")

        conclusion = self._build_conclusion(
            intent,
            asset_risks,
            tool_context["purchase_requests"],
            asset_component_counts,
            tool_context["requested_asset_code"],
        )
        missing_data = [] if tool_context["citations"] else ["Chưa có manual chunk/citation liên quan."]
        if intent == "asset_component_count_query":
            missing_data = []
        if extra_missing_data:
            missing_data.extend(extra_missing_data)
        if intent != "asset_component_count_query" and tool_context.get("routing_guardrails", {}).get(
            "missing_notification_routing"
        ):
            missing_data.append(
                "Thiếu cấu hình primary/backup contact (org routing) cho ít nhất một tài sản liên quan."
            )

        recommended_actions = [
            "Kiểm tra task kỹ thuật đã tạo.",
            "Xác nhận tồn kho phụ tùng.",
            "Trình phê duyệt purchase request nếu dữ liệu đúng.",
        ]
        if intent == "asset_component_count_query":
            recommended_actions = ["Xem chi tiết asset để kiểm tra danh sách linh kiện và trạng thái hiện tại nếu cần."]

        return ChatResponse(
            intent=intent,
            conclusion=conclusion,
            evidence=evidence,
            recommended_actions=recommended_actions,
            missing_data=missing_data,
            citations=tool_context["citations"],
            agent_mode=agent_mode,
            tool_calls=tool_context["tool_calls"],
        )

    def _response_from_agent_payload(
        self,
        intent: str,
        payload: dict[str, Any],
        fallback_citations: list[Citation],
        tool_calls: list[str],
        agent_mode: str,
    ) -> ChatResponse:
        citations = []
        for item in payload.get("citations") or []:
            if isinstance(item, dict):
                citations.append(
                    Citation(
                        type=str(item.get("type") or "source"),
                        code=str(item.get("code") or "unknown"),
                        title=str(item.get("title") or "Untitled"),
                    )
                )
        return ChatResponse(
            intent=intent,
            conclusion=str(payload.get("conclusion") or "Không đủ dữ liệu để kết luận."),
            evidence=[str(item) for item in payload.get("evidence") or []],
            recommended_actions=[str(item) for item in payload.get("recommended_actions") or []],
            missing_data=[str(item) for item in payload.get("missing_data") or []],
            citations=citations or fallback_citations,
            agent_mode=agent_mode,
            tool_calls=tool_calls,
        )

    def _record_agent_run(
        self,
        question: str,
        intent: str,
        tool_context: dict[str, Any],
        response: ChatResponse,
        llm_used: bool,
        error: str | None = None,
    ) -> None:
        run = AgentRun(
            run_type="chat_tool_calling_agent",
            status="failed" if error else "completed",
            input_snapshot={
                "question": question,
                "intent": intent,
                "tool_calls": tool_context["tool_calls"],
                "llm_used": llm_used,
            },
            output_summary={
                "agent_mode": response.agent_mode,
                "conclusion": response.conclusion,
                "citations_count": len(response.citations),
                "error": error,
            },
            error_message=error,
            finished_at=datetime.now(UTC),
        )
        self.db.add(run)
        self.db.commit()

    @staticmethod
    def _classify(question: str) -> str:
        normalized = question.lower()
        if (
            ("bao nhiêu" in normalized or "có mấy" in normalized or "số lượng" in normalized)
            and any(keyword in normalized for keyword in ["linh kiện", "component"])
        ):
            return "asset_component_count_query"
        if any(keyword in normalized for keyword in ["doanh thu", "revenue", "marketing", "lương", "nhân sự"]):
            return "out_of_scope"
        if any(keyword in normalized for keyword in ["phê duyệt", "duyệt", "ceo", "approver"]):
            return "approval_query"
        if any(keyword in normalized for keyword in ["mua", "purchase", "tồn kho", "lead time", "phụ tùng"]):
            return "purchase_reason"
        if any(keyword in normalized for keyword in ["manual", "căn cứ", "nguồn", "citation"]):
            return "manual_source_query"
        if any(keyword in normalized for keyword in ["rule", "quy tắc", "vì sao"]):
            return "rule_explanation"
        return "asset_risk_query"

    @staticmethod
    def _build_conclusion(
        intent: str,
        asset_risks: list[dict[str, Any]],
        purchase_requests: list[dict[str, Any]],
        asset_component_counts: list[dict[str, Any]],
        requested_asset_code: str | None,
    ) -> str:
        if intent == "asset_component_count_query":
            target_row = ChatService._pick_asset_component_count(asset_component_counts, requested_asset_code)
            if target_row:
                return (
                    f"{target_row['asset_name']} ({target_row['asset_code']}) hiện có "
                    f"{target_row['component_count']} linh kiện theo dõi."
                )
            if asset_component_counts:
                total_components = sum(item["component_count"] for item in asset_component_counts)
                return f"Hệ thống hiện có {len(asset_component_counts)} tài sản với tổng {total_components} linh kiện theo dõi."
            return "Chưa có dữ liệu linh kiện trong hệ thống."
        if not asset_risks:
            return "Chưa phát hiện linh kiện thang máy nào trong phạm vi rule MVP cần cảnh báo."
        component_names = ", ".join(str(risk["component_name"]) for risk in asset_risks)
        if intent == "purchase_reason" and purchase_requests:
            return f"Cần theo dõi mua hàng cho {component_names} vì có rủi ro tuổi thọ và purchase request draft."
        if intent == "approval_query" and purchase_requests:
            approvers = ", ".join(sorted({request["final_approver"] or "chưa xác định" for request in purchase_requests}))
            return f"Các đề xuất mua hàng hiện cần người phê duyệt: {approvers}."
        return f"Có {len(asset_risks)} linh kiện cần chú ý: {component_names}."

    @staticmethod
    def _extract_asset_code(question: str) -> str | None:
        match = re.search(r"\bELV-[A-Z0-9-]+\b", question.upper())
        return match.group(0) if match else None

    @staticmethod
    def _pick_asset_component_count(
        rows: list[dict[str, Any]],
        requested_asset_code: str | None,
    ) -> dict[str, Any] | None:
        if not rows:
            return None
        if requested_asset_code:
            for row in rows:
                if row["asset_code"] == requested_asset_code:
                    return row
        return None

    def _get_ontology_context(self, asset_code: str | None) -> dict[str, Any]:
        if not asset_code:
            return {}
        context = Neo4jSyncService().get_asset_context(asset_code)
        if context:
            return {"source": "neo4j", **context}

        asset = self.db.scalar(select(Asset).where(Asset.code == asset_code))
        if not asset:
            return {}
        components = list(self.db.scalars(select(Component).where(Component.asset_id == asset.id)))
        return {
            "source": "postgresql_fallback",
            "asset": {"code": asset.code, "name": asset.name},
            "components": [
                {
                    "code": component.code,
                    "name": component.name,
                    "component_type": component.component_type,
                    "remaining_lifetime_months": component.remaining_lifetime_months,
                    "spare_part_code": component.spare_part_code,
                }
                for component in components
            ],
        }

    @staticmethod
    def _approval_policy_from_requests(purchase_requests: list[PurchaseRequest]) -> list[dict[str, Any]]:
        policies = []
        seen = set()
        for request in purchase_requests:
            key = (request.approval_policy_code, request.final_approver)
            if key in seen:
                continue
            seen.add(key)
            policies.append(
                {
                    "approval_policy_code": request.approval_policy_code,
                    "final_approver": request.final_approver,
                    "source": "purchase_request",
                }
            )
        return policies

    @staticmethod
    def _serializable_context(tool_context: dict[str, Any]) -> dict[str, Any]:
        return {
            key: [
                item.model_dump() if hasattr(item, "model_dump") else item
                for item in value
            ]
            if key == "citations"
            else value
            for key, value in tool_context.items()
        }
