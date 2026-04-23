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

## Frontend proxy Phase 3

Next.js frontend có proxy route:

```text
/api/backend/{backend_path}
```

Ví dụ browser gọi:

```text
POST /api/backend/api/reasoning/run
```

Proxy sẽ chuyển tiếp tới backend:

```text
POST http://backend:8000/api/reasoning/run
```

Lý do: trong Docker, hostname `backend` chỉ truy cập được từ server/container, không truy cập trực tiếp được từ browser.

## Phase 4 Manual + RAG + Chat

```text
POST /api/manuals/upload
GET  /api/manuals
GET  /api/manuals/{manual_id}
POST /api/manuals/{manual_id}/parse
GET  /api/manuals/{manual_id}/chunks
POST /api/chat/query
GET  /api/llm/health
```

## Phase 07 Realtime Sensor + Telemetry

```text
GET  /api/sensors
GET  /api/assets/{asset_id}/sensors
POST /api/telemetry/readings
POST /api/telemetry/readings/batch
GET  /api/assets/{asset_id}/telemetry/latest
GET  /api/assets/{asset_id}/telemetry/history?sensor_code={code}&from={iso}&to={iso}
```

Payload `POST /api/telemetry/readings`:

```json
{
  "sensor_code": "SNS-CABLE-VIB-001",
  "measured_at": "2026-04-23T10:30:00Z",
  "value": 6.8,
  "quality": "good",
  "metadata": {
    "source": "simulator"
  }
}
```

## Phase 08 Realtime Rule Engine

```text
GET  /api/sensor-alerts
GET  /api/sensor-alerts/{alert_id}
POST /api/sensor-alerts/{alert_id}/acknowledge
POST /api/sensor-alerts/{alert_id}/resolve
POST /api/realtime-rules/evaluate
```

## Phase 09 3D Digital Twin

Frontend dùng các API hiện có và API telemetry:

```text
GET /api/assets/{asset_id}
GET /api/assets/{asset_id}/ontology
GET /api/assets/{asset_id}/telemetry/latest
GET /api/sensor-alerts?asset_id={asset_id}&status=open
```

Realtime nâng cấp:

```text
GET /api/realtime/assets/{asset_id}/events
```

## `GET /api/llm/health`

Kiểm tra backend có gọi được Gemini API thật bằng `GEMINI_API_KEY` hay không.

Response thành công:

```json
{
  "provider": "gemini",
  "configured": true,
  "reachable": true,
  "model": "gemini-2.5-flash",
  "response_text": "ok"
}
```

## `POST /api/chat/query`

Request:

```json
{
  "question": "Có thang máy nào sắp cần kiểm tra hoặc thay linh kiện không?"
}
```

Response:

```json
{
  "intent": "asset_risk_query",
  "conclusion": "Có 1 linh kiện cần chú ý: Cáp kéo Calidas 1.",
  "evidence": [],
  "recommended_actions": [],
  "missing_data": [],
  "citations": []
}
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
