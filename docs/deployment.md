# Deployment Phase 1

Phase 1 chạy bằng Docker Compose trong thư mục `infra`.

## Chạy toàn bộ stack

```bash
cd infra
docker compose up --build
```

## URL mặc định

- Frontend: `http://localhost:3000`
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
```

## Neo4j constraints

Sau khi Neo4j chạy, có thể apply constraints bằng Neo4j Browser hoặc `cypher-shell`:

```bash
cypher-shell -a bolt://localhost:7687 -u neo4j -p twinai-neo4j-password -f infra/neo4j/constraints.cypher
```

