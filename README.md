# TwinAI Agentic MVP

Codebase MVP cho hệ thống Agentic AI Ontology nội bộ.

Phase hiện tại: **Phase 01 - Nền tảng kiến trúc**.

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

## Phase tiếp theo

Phase 02 sẽ thêm:

- PostgreSQL schema nghiệp vụ.
- Seed data thang máy.
- Neo4j graph cho Ontology.
- Rule Engine `R-ELV-CABLE-001`.
- API `POST /api/reasoning/run`.

