import hashlib
import re

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.models import Manual, ManualChunk, Rule
from app.services.neo4j_sync import Neo4jSyncService


DEFAULT_MANUAL_TEXT = """
Manual bảo trì thang máy Calidas.
Kiểm tra cáp kéo định kỳ. Khi cáp kéo còn dưới hoặc bằng 6 tháng tuổi thọ, bộ phận kỹ thuật phải tạo task kiểm tra.
Kỹ thuật viên cần đo đường kính cáp, đo độ rung khi vận hành, kiểm tra ngày bảo trì gần nhất và ghi nhận đánh giá thực tế.
Nếu phụ tùng thay thế không có trong kho và lead time mua hàng dài hơn thời gian còn lại của linh kiện, hệ thống được phép tạo đề xuất mua hàng.
Đề xuất mua hàng không phải đơn mua hàng chính thức và cần người có thẩm quyền phê duyệt.
"""


class RagService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_manuals(self) -> list[Manual]:
        return list(self.db.scalars(select(Manual).order_by(Manual.created_at.desc())))

    def get_manual(self, manual_id: str) -> Manual | None:
        return self.db.get(Manual, manual_id)

    def create_uploaded_manual(
        self,
        file_name: str,
        content: bytes,
        code: str | None = None,
        title: str | None = None,
        rule_code: str | None = "R-ELV-CABLE-001",
    ) -> Manual:
        manual_code = code or self._code_from_file(file_name)
        manual = self.db.scalar(select(Manual).where(Manual.code == manual_code))
        if not manual:
            manual = Manual(
                code=manual_code,
                title=title or file_name,
                department_owner="Kỹ thuật",
                file_object_key=f"manuals/{manual_code}/{file_name}",
                file_name=file_name,
                file_type=file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "txt",
                version="uploaded",
                status="uploaded",
            )
            self.db.add(manual)
            self.db.flush()

        text = self._decode_content(content)
        if text.strip():
            self.create_chunks(manual, text)
        if rule_code:
            self.link_manual_to_rule(manual, rule_code)
        self.db.commit()
        return manual

    def link_manual_to_rule(self, manual: Manual, rule_code: str) -> dict:
        rule = self.db.scalar(select(Rule).where(Rule.code == rule_code))
        if not rule:
            manual.linked_rule_code = None
            manual.neo4j_sync = {"enabled": False, "synced": False, "reason": "rule_not_found"}
            return {"linked": False, "reason": "rule_not_found", "rule_code": rule_code}

        rule.source_manual_id = manual.id
        self.db.flush()
        sync_result = Neo4jSyncService().sync_manual_rule_link(manual, rule)
        manual.linked_rule_code = rule.code
        manual.neo4j_sync = sync_result
        self.db.commit()
        return {
            "linked": True,
            "rule_code": rule.code,
            "manual_code": manual.code,
            "neo4j_sync": sync_result,
        }

    def parse_manual(self, manual: Manual) -> list[ManualChunk]:
        existing = self.list_chunks(manual.id)
        if existing:
            return existing
        return self.create_chunks(manual, DEFAULT_MANUAL_TEXT)

    def create_chunks(self, manual: Manual, text: str) -> list[ManualChunk]:
        self.db.execute(delete(ManualChunk).where(ManualChunk.manual_id == manual.id))
        chunks = []
        for index, chunk_text in enumerate(_chunk_text(text), start=1):
            chunk = ManualChunk(
                manual_id=manual.id,
                chunk_index=index,
                heading=manual.title,
                page_number=None,
                chunk_text=chunk_text,
                embedding_json=_fake_embedding(chunk_text),
                metadata_json={
                    "manual_code": manual.code,
                    "manual_title": manual.title,
                    "source": "uploaded_or_seed_manual",
                },
            )
            self.db.add(chunk)
            chunks.append(chunk)
        manual.status = "parsed"
        self.db.flush()
        self.db.commit()
        return chunks

    def list_chunks(self, manual_id: str) -> list[ManualChunk]:
        return list(
            self.db.scalars(
                select(ManualChunk)
                .where(ManualChunk.manual_id == manual_id)
                .order_by(ManualChunk.chunk_index)
            )
        )

    def search_chunks(self, query: str, limit: int = 5) -> list[ManualChunk]:
        terms = [term for term in re.split(r"\W+", query.lower()) if len(term) >= 3]
        if not terms:
            return list(self.db.scalars(select(ManualChunk).order_by(ManualChunk.chunk_index).limit(limit)))

        filters = [ManualChunk.chunk_text.ilike(f"%{term}%") for term in terms[:6]]
        rows = list(self.db.scalars(select(ManualChunk).where(or_(*filters)).limit(limit)))
        if rows:
            return rows
        return list(self.db.scalars(select(ManualChunk).order_by(ManualChunk.chunk_index).limit(limit)))

    @staticmethod
    def _decode_content(content: bytes) -> str:
        for encoding in ("utf-8", "utf-16", "latin-1"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return ""

    @staticmethod
    def _code_from_file(file_name: str) -> str:
        base = re.sub(r"[^A-Za-z0-9]+", "-", file_name.rsplit(".", 1)[0]).strip("-").upper()
        return f"MAN-{base[:40] or 'UPLOAD'}"


def _chunk_text(text: str, max_chars: int = 700) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n+", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 1 > max_chars and current:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks or [text[:max_chars]]


def _fake_embedding(text: str, dimensions: int = 8) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [round(byte / 255, 4) for byte in digest[:dimensions]]
