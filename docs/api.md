# API Phase 1

## Health

```text
GET /
GET /health
GET /health/dependencies
```

## Phase 2

```text
GET  /api/assets
GET  /api/assets/{asset_id}
GET  /api/assets/{asset_id}/ontology
POST /api/reasoning/run
GET  /api/agent-runs
GET  /api/agent-runs/{run_id}
GET  /api/inspection-tasks
GET  /api/purchase-requests
```

## `POST /api/reasoning/run`

Chạy rule `R-ELV-CABLE-001` trên dữ liệu thang máy.

Kết quả mong muốn:

- 1 finding cho `CMP-CABLE-001`.
- 1 task kiểm tra.
- 1 purchase request draft.
- Audit log cho hành động agent.

## `GET /health`

Response:

```json
{
  "status": "ok",
  "service": "TwinAI Agentic MVP API",
  "version": "0.1.0"
}
```

## `GET /health/dependencies`

Response:

```json
{
  "status": "ok",
  "dependencies": [
    {
      "name": "postgresql",
      "configured": true,
      "detail": "postgresql+psycopg://***:***@postgres:5432/twinai"
    }
  ]
}
```
