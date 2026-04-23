# API Phase 1

## Health

```text
GET /
GET /health
GET /health/dependencies
GET /health/services
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

## Organization (đọc — bổ sung trước Phase 05 đầy đủ)

```text
GET  /api/org/units
GET  /api/org/users
```

- `OrgUnitRead`: `id`, `code`, `name`, `level_kind` (`holding` | `branch` | `department` | `team`), `parent_id`, `sort_order`.
- `OrgUserRead`: `user_code`, `full_name`, `email`, `job_title`, `org_unit_id`, `org_unit_code`, `org_unit_name`, `manager_user_id`, `manager_user_code`, `role_tags`, `is_active`.

Dữ liệu demo từ `seed_phase_two_data` (idempotent). Chat/reasoning **chưa** tự resolve approver/contact từ các bảng này.

## Phase 05 Approval + Org Routing + Notification + Audit

Backend đã có các endpoint sau. Web gọi qua proxy `POST /api/backend/api/...` (xem mục Frontend proxy).

- Sau khi commit transaction chính (submit/approve/reject), backend gọi webhook n8n (`N8N_WEBHOOK_URL`); lỗi gửi webhook không rollback DB và được ghi audit `notification_failed` khi áp dụng.

```text
GET  /api/purchase-requests
GET  /api/purchase-requests/{request_id}
POST /api/purchase-requests/{request_id}/submit
POST /api/purchase-requests/{request_id}/approve
POST /api/purchase-requests/{request_id}/reject
POST /api/purchase-requests/{request_id}/cancel

GET  /api/assets/{asset_id}/contacts
GET  /api/rules/{rule_id}/notification-targets
GET  /api/escalation-policies/{policy_id}

GET  /api/audit-logs
GET  /api/audit-logs?entity_type=purchase_request&entity_id={id}
```

- `GET /api/assets/{asset_id}/contacts`: ưu tiên `asset_contact_assignments` (`contact_kind` `primary` | `backup`, `sort_order`); không có bản ghi thì fallback `role_tags`. Trả thêm `contact_resolution.primary_source` / `backup_source`: `asset_assignment` | `role_fallback` | `none`.

`GET /api/purchase-requests/{request_id}` trả `PurchaseRequestDetailRead` (thêm `asset_id`, `asset_code`, `component_code` cho UI routing).

Body workflow (submit/approve/reject/cancel): `WorkflowActorBody` — `actor_type` (mặc định `user`), `actor_id`, `note` tuỳ chọn.

**PHASE5_WRITE_SECRET (tuỳ chọn):** nếu biến môi trường được set, mọi POST submit/approve/reject/cancel bắt buộc header `X-Phase5-Write-Secret` trùng giá trị. Frontend Next có thể set cùng secret để proxy `/api/backend/...` tự gắn header.

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

Kiểm tra LLM theo `LLM_PROVIDER`: với `gemini` gọi thử `generateContent`; với `openai` gọi thử `GET /v1/models?limit=1`.

Response ví dụ (Gemini):

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
  "citations": [],
  "agent_mode": "llm_tool_agent:gemini",
  "tool_calls": ["classify_intent", "get_asset_risks", "get_asset_ontology"]
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

## `GET /health/services`

Kiểm tra **kết nối thực** tới PostgreSQL, Neo4j, MinIO, LLM (theo `LLM_PROVIDER`), và webhook n8n (nếu có). Dùng cho dashboard trạng thái hạ tầng.

Response (rút gọn):

```json
{
  "overall": "ok",
  "checked_at": "2026-04-23T12:00:00+00:00",
  "services": [
    { "id": "api", "label": "API (FastAPI)", "ok": true, "detail": "…" },
    { "id": "postgresql", "label": "PostgreSQL", "ok": true, "detail": "Kết nối OK" }
  ]
}
```

`overall`: `ok` (tất cả dịch vụ `ok`), `degraded` (DB sống nhưng có dịch vụ phụ lỗi), `critical` (PostgreSQL không kết nối được).
