import re
from math import sqrt

from sqlalchemy import delete, or_, select, text
from sqlalchemy.exc import DataError
from sqlalchemy.orm import Session

from app.models import Manual, ManualChunk, Rule
from app.services.document_parser import DocumentParseError, parse_document
from app.services.embeddings import EmbeddingClient, EmbeddingError
from app.services.neo4j_sync import Neo4jSyncService
from app.services.object_storage import MinioStorageService


class RagService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding_client = EmbeddingClient()
        self.storage = MinioStorageService()

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
        content_type: str | None = None,
    ) -> Manual:
        manual_code = code or self._code_from_file(file_name)
        file_object_key = f"manuals/{manual_code}/{file_name}"
        self.storage.upload_bytes(file_object_key, content, content_type=content_type)
        manual = self.db.scalar(select(Manual).where(Manual.code == manual_code))
        if not manual:
            manual = Manual(
                code=manual_code,
                title=title or file_name,
                department_owner="Kỹ thuật",
                file_object_key=file_object_key,
                file_name=file_name,
                file_type=file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "txt",
                version="uploaded",
                status="uploaded",
            )
            self.db.add(manual)
            self.db.flush()
        else:
            manual.title = title or file_name
            manual.file_object_key = file_object_key
            manual.file_name = file_name
            manual.file_type = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "txt"
            manual.version = "uploaded"
            manual.status = "uploaded"
            self.db.execute(delete(ManualChunk).where(ManualChunk.manual_id == manual.id))

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
        raw_content = self.storage.download_bytes(manual.file_object_key)
        parsed_text = parse_document(raw_content, file_name=manual.file_name, file_type=manual.file_type)
        if not parsed_text.strip():
            raise DocumentParseError("Manual không có nội dung text để parse.")
        return self.create_chunks(manual, parsed_text)

    def create_chunks(self, manual: Manual, text: str) -> list[ManualChunk]:
        if not self.embedding_client.is_configured():
            raise EmbeddingError("Cần cấu hình GEMINI_API_KEY hoặc OPENAI_API_KEY để tạo embedding thật cho manual.")

        self.db.execute(delete(ManualChunk).where(ManualChunk.manual_id == manual.id))
        chunk_texts = _chunk_text(text)
        embeddings = self.embedding_client.embed_documents(chunk_texts)
        chunks = []
        for index, (chunk_text, embedding) in enumerate(zip(chunk_texts, embeddings, strict=True), start=1):
            chunk = ManualChunk(
                manual_id=manual.id,
                chunk_index=index,
                heading=manual.title,
                page_number=None,
                chunk_text=chunk_text,
                embedding_json=embedding,
                metadata_json={
                    "manual_code": manual.code,
                    "manual_title": manual.title,
                    "source": "minio_uploaded_manual",
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
        chunks = list(self.db.scalars(select(ManualChunk).order_by(ManualChunk.chunk_index)))
        if not chunks:
            return []

        if self.embedding_client.is_configured():
            try:
                query_embedding = self.embedding_client.embed_query(query)
                if self.db.bind and self.db.bind.dialect.name == "postgresql":
                    rows = self._search_chunks_postgres(query_embedding=query_embedding, limit=limit)
                    if rows:
                        return rows
                return self._search_chunks_python(
                    chunks=chunks, query_embedding=query_embedding, limit=limit
                )
            except EmbeddingError:
                pass

        terms = [term for term in re.split(r"\W+", query.lower()) if len(term) >= 3]
        if not terms:
            return chunks[:limit]

        filters = [ManualChunk.chunk_text.ilike(f"%{term}%") for term in terms[:6]]
        rows = list(self.db.scalars(select(ManualChunk).where(or_(*filters)).limit(limit)))
        if rows:
            return rows
        return chunks[:limit]

    @staticmethod
    def _code_from_file(file_name: str) -> str:
        base = re.sub(r"[^A-Za-z0-9]+", "-", file_name.rsplit(".", 1)[0]).strip("-").upper()
        return f"MAN-{base[:40] or 'UPLOAD'}"

    def _search_chunks_postgres(self, query_embedding: list[float], limit: int) -> list[ManualChunk]:
        """pgvector distance requires query and row vectors to share the same dimension (legacy seed used 8-dim)."""
        dim = len(query_embedding)
        if dim == 0:
            return []
        embedding_literal = _vector_literal(query_embedding)
        try:
            rows = self.db.execute(
                text(
                    """
                    SELECT id
                    FROM manual_chunks
                    WHERE embedding_json IS NOT NULL
                      AND jsonb_array_length(embedding_json::jsonb) = :embedding_dim
                    ORDER BY CAST(embedding_json::text AS vector) <=> CAST(:query_embedding AS vector)
                    LIMIT :limit
                    """
                ),
                {"query_embedding": embedding_literal, "limit": limit, "embedding_dim": dim},
            ).fetchall()
        except DataError:
            return []
        chunk_ids = [row[0] for row in rows]
        if not chunk_ids:
            return []
        by_id = {
            chunk.id: chunk
            for chunk in self.db.scalars(select(ManualChunk).where(ManualChunk.id.in_(chunk_ids)))
        }
        return [by_id[chunk_id] for chunk_id in chunk_ids if chunk_id in by_id]

    @staticmethod
    def _search_chunks_python(chunks: list[ManualChunk], query_embedding: list[float], limit: int) -> list[ManualChunk]:
        dim = len(query_embedding)
        ranked = sorted(
            (
                (chunk, _cosine_similarity(chunk.embedding_json, query_embedding))
                for chunk in chunks
                if chunk.embedding_json
                and isinstance(chunk.embedding_json, list)
                and len(chunk.embedding_json) == dim
            ),
            key=lambda item: item[1],
            reverse=True,
        )
        return [chunk for chunk, _ in ranked[:limit]]


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


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
