# Kế hoạch phát triển theo phase

Thư mục này tách kế hoạch triển khai từ tài liệu `08-thiet-ke-he-thong-mvp-agentic-ai.md` thành từng giai đoạn phát triển cụ thể.

## Danh sách phase

- `00-tong-quan-phase.md`: tổng quan roadmap, nguyên tắc triển khai và thứ tự phụ thuộc.
- `01-nen-tang-kien-truc.md`: dựng nền tảng repo, Docker Compose, PostgreSQL, Neo4j, MinIO, FastAPI.
- `02-data-neo4j-rule-engine.md`: tạo schema dữ liệu, seed data, Neo4j graph, Rule Engine và API reasoning.
- `03-dashboard-ontology-map.md`: xây giao diện dashboard, danh sách thang máy, agent run và ontology map.
- `04-manual-rag-chat.md`: upload manual, parse/chunk, embedding, pgvector, chat có citations.
- `05-approval-notification-audit.md`: phê duyệt purchase request, notification qua n8n và audit log viewer.
- `06-nghiem-thu-mvp.md`: kịch bản nghiệm thu cuối cùng cho MVP.

## Thứ tự triển khai

```text
Phase 01
  -> Phase 02
  -> Phase 03
  -> Phase 04
  -> Phase 05
  -> Phase 06
```

Phase 02 là lõi quan trọng nhất vì chứa dữ liệu, Neo4j Ontology graph và Rule Engine. Không nên build Chat/RAG trước khi Phase 02 chạy đúng.

