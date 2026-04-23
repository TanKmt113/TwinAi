import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["AUTO_SEED"] = "false"
os.environ["ENABLE_NEO4J_SYNC"] = "false"
os.environ["GEMINI_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import domain  # noqa: F401
from app.services.rag import RagService


class FakeStorageService:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def upload_bytes(self, object_key: str, content: bytes, content_type: str | None = None) -> None:
        self.objects[object_key] = content

    def download_bytes(self, object_key: str) -> bytes:
        return self.objects[object_key]


class FakeEmbeddingClient:
    def is_configured(self) -> bool:
        return True

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [_vector_for_text(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return _vector_for_text(text)


def _vector_for_text(text: str) -> list[float]:
    lowered = text.lower()
    return [
        1.0 if "cáp" in lowered else 0.0,
        1.0 if "phê duyệt" in lowered or "approval" in lowered else 0.0,
        1.0 if "tồn kho" in lowered or "inventory" in lowered else 0.0,
    ]


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSession()


def test_rag_upload_parse_and_search(monkeypatch) -> None:
    fake_storage = FakeStorageService()

    monkeypatch.setattr("app.services.rag.MinioStorageService", lambda: fake_storage)
    monkeypatch.setattr("app.services.rag.EmbeddingClient", FakeEmbeddingClient)

    with _session() as db:
        service = RagService(db)
        manual = service.create_uploaded_manual(
            file_name="manual.txt",
            content=(
                "Kiểm tra cáp kéo định kỳ.\n\n"
                "Nếu cáp kéo còn dưới 6 tháng tuổi thọ thì tạo task kiểm tra.\n\n"
                "Đề xuất mua hàng cần người có thẩm quyền phê duyệt."
            ).encode("utf-8"),
            rule_code=None,
            content_type="text/plain",
        )

        assert manual.file_object_key in fake_storage.objects
        assert service.list_chunks(manual.id) == []

        chunks = service.parse_manual(manual)

        assert chunks
        assert all(chunk.embedding_json for chunk in chunks)
        assert service.get_manual(manual.id).status == "parsed"

        results = service.search_chunks("cáp kéo cần kiểm tra")

        assert results
        assert "cáp kéo" in results[0].chunk_text.lower()
