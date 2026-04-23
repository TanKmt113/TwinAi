# Phase 01: Nền tảng kiến trúc

## Mục tiêu

Dựng nền kỹ thuật ban đầu để các phase sau có thể phát triển trên cùng một cấu trúc chuẩn.

## Phạm vi

Phase này chưa cần build đầy đủ business logic. Mục tiêu là có hệ thống chạy được với các service nền:

- Next.js frontend.
- FastAPI backend.
- PostgreSQL + pgvector.
- Neo4j.
- MinIO.
- Worker placeholder.
- n8n placeholder/webhook.
- Docker Compose nội bộ.

## Tech stack

```text
Frontend: Next.js + React
Backend: Python FastAPI
Database: PostgreSQL + pgvector
Ontology graph: Neo4j
Storage: MinIO
Automation: n8n
Deploy: Docker Compose
```

## Cấu trúc repo cần tạo

```text
twinai-agentic-mvp/
  apps/
    web/
      app/
      components/
      lib/
      package.json
    api/
      app/
        main.py
        api/
        core/
        models/
        schemas/
        services/
        workers/
        tests/
      pyproject.toml
  infra/
    docker-compose.yml
    postgres/
      init.sql
    neo4j/
      constraints.cypher
      seed.cypher
    minio/
  docs/
    architecture.md
    ontology.md
    api.md
    deployment.md
```

## Công việc chi tiết

### Backend

- Tạo FastAPI app.
- Tạo health check endpoint:

```text
GET /health
```

- Tạo cấu hình environment:

```text
DATABASE_URL
NEO4J_URI
NEO4J_USER
NEO4J_PASSWORD
MINIO_ENDPOINT
OPENAI_API_KEY
N8N_WEBHOOK_URL
```

- Tạo database connection cho PostgreSQL.
- Tạo Neo4j driver connection.
- Tạo MinIO client placeholder.

### Frontend

- Tạo Next.js app.
- Tạo layout dashboard cơ bản.
- Tạo trang health/status gọi backend.

### Infrastructure

Docker Compose cần có service:

```text
frontend
backend
postgres
neo4j
minio
n8n
```

Ghi chú trạng thái hiện tại:

- Backend, Postgres, Neo4j, MinIO, n8n đã có trong `docker-compose.yml`.
- Frontend hiện có code Next.js nhưng service frontend chưa được bật mặc định trong `docker-compose.yml`.
- Worker mới ở mức placeholder, chưa có workflow background riêng.
- MinIO ở phase này mới là placeholder cho storage; luồng upload object thật sẽ hoàn thiện ở phase sau.

## Deliverables

- Repo scaffold đầy đủ.
- `docker-compose.yml` chạy được.
- Backend trả `GET /health`.
- Frontend gọi được backend health.
- PostgreSQL chạy được.
- Neo4j Browser mở được.
- MinIO console mở được.

## Tiêu chí hoàn thành

Phase 01 đạt khi:

1. Chạy được toàn bộ stack bằng Docker Compose.
2. Backend kết nối được PostgreSQL.
3. Backend kết nối được Neo4j.
4. Frontend hiển thị trạng thái hệ thống khi chạy riêng hoặc được bật thêm trong compose.
5. Neo4j đã có constraints cơ bản nhưng chưa cần seed graph đầy đủ.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Stack quá nặng cho máy dev | Cho phép tắt n8n/MinIO khi dev local |
| Neo4j chưa quen vận hành | Tạo script constraints và seed mẫu ngay từ đầu |
| Config rối | Dùng `.env.example` rõ ràng |

