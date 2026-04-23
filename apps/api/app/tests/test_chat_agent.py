import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["AUTO_SEED"] = "false"
os.environ["ENABLE_NEO4J_SYNC"] = "false"
os.environ["GEMINI_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.database import Base
from app.models import AgentRun
from app.models import domain  # noqa: F401
from app.services.chat import ChatService
from app.services.seed import seed_phase_two_data


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSession()


def test_chat_agent_falls_back_when_llm_is_not_configured(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()
    with _session() as db:
        seed_phase_two_data(db)

        response = ChatService(db).answer("Thang máy ELV-CALIDAS-01 có cần thay cáp không?")

        assert response.intent == "asset_risk_query"
        assert response.agent_mode == "rule_fallback_no_llm_key"
        assert "get_asset_ontology" in response.tool_calls
        assert "get_asset_notification_routing" in response.tool_calls
        assert "Cáp kéo Calidas 1" in response.conclusion

        runs = list(db.scalars(select(AgentRun)))
        assert len(runs) == 1
        assert runs[0].run_type == "chat_tool_calling_agent"
        assert runs[0].input_snapshot["llm_used"] is False


def test_chat_agent_uses_llm_payload_when_configured(monkeypatch) -> None:
    class FakeLlmClient:
        def is_configured(self) -> bool:
            return True

        def provider_name(self) -> str:
            return "fake"

        def generate_chat_response(self, question, intent, tool_context):
            assert question
            assert intent == "asset_risk_query"
            assert "asset_risks" in tool_context
            assert "asset_routing_contacts" in tool_context
            return {
                "conclusion": "Agent đã kiểm tra ontology, rule và manual.",
                "evidence": ["CMP-CABLE-001 còn 5 tháng tuổi thọ."],
                "recommended_actions": ["Chạy reasoning nếu cần tạo task/purchase request."],
                "missing_data": [],
                "citations": [{"type": "rule", "code": "R-ELV-CABLE-001", "title": "Rule test"}],
            }

    monkeypatch.setattr("app.services.chat.LlmAgentClient", FakeLlmClient)

    with _session() as db:
        seed_phase_two_data(db)

        response = ChatService(db).answer("Thang máy ELV-CALIDAS-01 có cần thay cáp không?")

        assert response.agent_mode == "llm_tool_agent:fake"
        assert response.conclusion == "Agent đã kiểm tra ontology, rule và manual."
        assert response.citations[0].code == "R-ELV-CABLE-001"


def test_chat_agent_blocks_out_of_scope_questions() -> None:
    with _session() as db:
        seed_phase_two_data(db)

        response = ChatService(db).answer("Dự báo doanh thu tháng sau là bao nhiêu?")

        assert response.intent == "out_of_scope"
        assert response.agent_mode == "guardrail_out_of_scope"
        assert response.citations == []
        assert "Không đủ dữ liệu" in response.conclusion


def test_chat_agent_counts_components_instead_of_falling_back_to_risk_query(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()
    with _session() as db:
        seed_phase_two_data(db)

        response = ChatService(db).answer("Thang máy ELV-CALIDAS-01 có bao nhiêu linh kiện?")

        assert response.intent == "asset_component_count_query"
        assert response.agent_mode == "rule_fallback_no_llm_key"
        assert "1 linh kiện" in response.conclusion
        assert "ELV-CALIDAS-01" in response.conclusion
        assert any("Danh sách linh kiện" in item for item in response.evidence)
        assert response.citations == []
        assert response.tool_calls == [
            "classify_intent",
            "get_asset_component_counts",
            "get_asset_ontology",
        ]
        assert response.recommended_actions == [
            "Xem chi tiết asset để kiểm tra danh sách linh kiện và trạng thái hiện tại nếu cần."
        ]
