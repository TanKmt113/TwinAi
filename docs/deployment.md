# Deployment Phase 1

Phase 1 chạy bằng Docker Compose trong thư mục `infra`.

## Chạy toàn bộ stack

```bash
cd infra
docker compose up --build
```

## Biến môi trường LLM (Docker)

Service `backend` trong `infra/docker-compose.yml` dùng `env_file: ../apps/api/.env` để nạp `GEMINI_*` / `OPENAI_*` / `LLM_PROVIDER` vào container. Không đặt `GEMINI_API_KEY: ${GEMINI_API_KEY:-}` trong `environment` với giá trị rỗng — sẽ ghi đè `env_file` và khiến API báo thiếu key.

## URL mặc định

- Frontend: `http://localhost:3000` nếu tự chạy `apps/web`; service frontend hiện chưa được bật mặc định trong `docker-compose.yml`.
- Backend API: `http://localhost:8000`
- Backend docs: `http://localhost:8000/docs`
- Neo4j Browser: `http://localhost:7474`
- MinIO Console: `http://localhost:9001`
- n8n: `http://localhost:5678`

## Tài khoản local

Neo4j:

```text
user: neo4j
password: twinai-neo4j-password
```

MinIO:

```text
user: twinai
password: twinai-minio-password
```

PostgreSQL:

```text
database: twinai
user: twinai
password: twinai
```

## Health checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/dependencies
curl http://localhost:8000/health/services
```

## Neo4j constraints

Sau khi Neo4j chạy, có thể apply constraints bằng Neo4j Browser hoặc `cypher-shell`:

```bash
cypher-shell -a bolt://localhost:7687 -u neo4j -p twinai-neo4j-password -f infra/neo4j/constraints.cypher
```

