# TwinAI Agentic MVP

Codebase MVP cho hệ thống Agentic AI Ontology nội bộ.

Phase hiện tại: **Phase 04 - Manual + RAG + Chat**.

## Cấu trúc chính

```text
apps/
  api/        FastAPI backend
  web/        Next.js frontend
infra/        Docker Compose, PostgreSQL, Neo4j, MinIO, n8n
docs/         Tài liệu kỹ thuật triển khai
phase/        Kế hoạch phát triển theo phase
```

## Chạy Phase 1

```bash
cd infra
docker compose up --build
```

Sau khi chạy:

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Neo4j: `http://localhost:7474`
- MinIO: `http://localhost:9001`
- n8n: `http://localhost:5678`

## Health check

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/dependencies
```

## Phase 3 Dashboard

Frontend tại:

```text
http://localhost:3000
```

Dashboard hiện có:

- Số lượng tài sản, rủi ro, task mở, purchase request.
- Bảng thang máy và linh kiện.
- Nút `Chạy suy luận`.
- Danh sách agent runs.
- Task kiểm tra.
- Purchase request draft.
- Ontology map cho chuỗi thang máy -> linh kiện -> rule -> manual -> mua hàng -> phê duyệt.
- Khu upload/parse manual.
- Chat/RAG hỏi đáp có citations.

## Phase 2 API vẫn dùng

Sau khi stack chạy:

```bash
curl http://localhost:8000/api/assets
curl -X POST http://localhost:8000/api/reasoning/run
curl http://localhost:8000/api/inspection-tasks
curl http://localhost:8000/api/purchase-requests
```

## Phase 4 API

```bash
curl http://localhost:8000/api/manuals
curl -X POST http://localhost:8000/api/chat/query \
  -H "content-type: application/json" \
  -d '{"question":"Có thang máy nào sắp cần kiểm tra hoặc thay linh kiện không?"}'
```

Phase 2 đã thêm:

- PostgreSQL schema nghiệp vụ bằng SQLAlchemy.
- Seed data thang máy từ tài liệu 07.
- Neo4j Sync Service cho Ontology graph.
- Rule Engine `R-ELV-CABLE-001`.
- API `POST /api/reasoning/run`.

## Phase tiếp theo

Phase 05 sẽ thêm approval UI, notification qua n8n và audit log viewer.
