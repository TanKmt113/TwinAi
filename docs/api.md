# API Phase 1

## Health

```text
GET /
GET /health
GET /health/dependencies
```

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

