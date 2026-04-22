# Architecture Phase 1

Phase 4 đã có dashboard vận hành, Ontology map, upload/parse manual và Chat/RAG có citations.

```text
Next.js Web
  -> FastAPI Backend
      -> PostgreSQL + pgvector
      -> Neo4j
      -> MinIO
      -> n8n
```

## Vai trò service

- `frontend`: dashboard vận hành, nút chạy reasoning, bảng task/purchase request, Ontology map, manual upload và chat panel.
- `backend`: API health, cấu hình môi trường và entrypoint cho service sau này.
- `postgres`: dữ liệu giao dịch, audit, pgvector.
- `neo4j`: Ontology graph.
- `minio`: lưu manual/file gốc.
- `manual_chunks`: lưu nội dung đã parse/chunk trong PostgreSQL để phục vụ RAG.
- `n8n`: automation/notification.

## Ranh giới dữ liệu

- PostgreSQL là source of record cho dữ liệu giao dịch.
- Neo4j là source of truth cho quan hệ Ontology.
- MinIO lưu file gốc.
- LLM chưa được kích hoạt ở Phase 1.
