from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Component, InspectionTask, InventoryItem, Manual, PurchaseRequest, Rule
from app.schemas import ChatResponse, Citation
from app.services.rag import RagService


class ChatService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.rag = RagService(db)

    def answer(self, question: str) -> ChatResponse:
        intent = self._classify(question)
        if intent == "out_of_scope":
            return ChatResponse(
                intent=intent,
                conclusion="Không đủ dữ liệu để trả lời câu hỏi này trong Ontology MVP hiện tại.",
                evidence=[],
                recommended_actions=["Bổ sung domain dữ liệu/rule liên quan nếu câu hỏi này là nhu cầu nghiệp vụ thật."],
                missing_data=["Không có thực thể, rule hoặc manual liên quan trong phạm vi thang máy."],
                citations=[],
            )

        risky_components = list(
            self.db.scalars(
                select(Component).where(
                    Component.component_type == "cable",
                    Component.remaining_lifetime_months <= 6,
                )
            )
        )
        rule = self.db.scalar(select(Rule).where(Rule.code == "R-ELV-CABLE-001"))
        manual = self.db.scalar(select(Manual).where(Manual.code == "MAN-ELV-001"))
        chunks = self.rag.search_chunks(question)
        tasks = list(self.db.scalars(select(InspectionTask).where(InspectionTask.status == "open")))
        purchase_requests = list(
            self.db.scalars(select(PurchaseRequest).where(PurchaseRequest.status.in_(["draft", "waiting_for_approval"])))
        )

        evidence = []
        if risky_components:
            evidence.extend(
                [
                    f"{component.name} còn {component.remaining_lifetime_months} tháng tuổi thọ."
                    for component in risky_components
                ]
            )
        if tasks:
            evidence.append(f"Hệ thống có {len(tasks)} task kiểm tra đang mở.")
        if purchase_requests:
            evidence.extend([f"Purchase request: {request.reason}" for request in purchase_requests])
        if chunks:
            evidence.append(f"Tìm thấy {len(chunks)} đoạn manual liên quan.")

        citations = []
        if rule:
            citations.append(Citation(type="rule", code=rule.code, title=rule.name))
        if manual:
            citations.append(Citation(type="manual", code=manual.code, title=manual.title))
        citations.extend(
            [
                Citation(
                    type="manual_chunk",
                    code=f"chunk-{chunk.chunk_index}",
                    title=chunk.heading or "Manual chunk",
                )
                for chunk in chunks[:2]
            ]
        )

        conclusion = self._build_conclusion(intent, risky_components, purchase_requests)
        return ChatResponse(
            intent=intent,
            conclusion=conclusion,
            evidence=evidence,
            recommended_actions=[
                "Kiểm tra task kỹ thuật đã tạo.",
                "Xác nhận tồn kho phụ tùng.",
                "Trình phê duyệt purchase request nếu dữ liệu đúng.",
            ],
            missing_data=[] if citations else ["Chưa có manual chunk/citation liên quan."],
            citations=citations,
        )

    @staticmethod
    def _classify(question: str) -> str:
        normalized = question.lower()
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
    def _build_conclusion(intent: str, risky_components: list[Component], purchase_requests: list[PurchaseRequest]) -> str:
        if not risky_components:
            return "Chưa phát hiện linh kiện thang máy nào trong phạm vi rule MVP cần cảnh báo."
        component_names = ", ".join(component.name for component in risky_components)
        if intent == "purchase_reason" and purchase_requests:
            return f"Cần theo dõi mua hàng cho {component_names} vì có rủi ro tuổi thọ và purchase request draft."
        if intent == "approval_query" and purchase_requests:
            approvers = ", ".join(sorted({request.final_approver or "chưa xác định" for request in purchase_requests}))
            return f"Các đề xuất mua hàng hiện cần người phê duyệt: {approvers}."
        return f"Có {len(risky_components)} linh kiện cần chú ý: {component_names}."

