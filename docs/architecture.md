# Architecture

Phase 4 trong code hiện tại đã có dashboard vận hành (kèm panel **Trạng thái hạ tầng** từ `GET /health/services`), Ontology map MVP, upload/parse manual, Chat/RAG có citations và chat agent có tool context. PostgreSQL có thêm **`org_units`** / **`org_users`** (cây đơn vị + người dùng nội bộ, seed demo) và **`GET /api/org/units`**, **`GET /api/org/users`** — chưa nối vào luồng phê duyệt hay chat. RAG/pgvector: truy vấn vector chỉ trên chunk cùng số chiều với embedding query để tránh xung đột dữ liệu cũ. Các phần approval workflow đầy đủ, org routing/escalation tự động từ org tables, telemetry và 3D Twin trong sơ đồ bên dưới vẫn là kiến trúc mục tiêu cho các phase tiếp theo. Lớp Agentic AI phải được hiểu là workflow có guardrail, không phải một chatbot tự quyết định nghiệp vụ.

## Tổng quan hệ thống

```text
[Sơ đồ kiến trúc mục tiêu theo roadmap; repo hiện tại mới implement chủ yếu Phase 01-04]
┌─────────────────────────────────────────────────────────────┐
│                         Next.js UI                          │
│ Dashboard | Ontology Map | Chat | Task | Purchase | 3D Twin  │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST/JSON
┌──────────────────────────────▼──────────────────────────────┐
│                         FastAPI API                         │
│ Auth | Asset API | Manual API | Rule API | Chat | Telemetry   │
└──────────────────────────────┬──────────────────────────────┘
                               │ user request / scheduled job / data change
┌──────────────────────────────▼──────────────────────────────┐
│                    Agentic Workflow Layer                   │
│                                                             │
│  Chat Agent ───────────────▶ Agent Orchestrator             │
│  - hiểu câu hỏi              - chọn agent/tool cần gọi       │
│  - gọi LLM nếu có key         - kiểm soát guardrail           │
│  - trả JSON có citation       - ghi agent run/event           │
│                                                             │
│  Ontology Agent ───────────▶ Reasoning Agent                 │
│  - lấy graph Neo4j            - chạy rule deterministic       │
│  - asset context              - phát hiện rủi ro              │
│  - quan hệ nguồn              - tạo finding                   │
│                                                             │
│  RAG Agent ─────────────────▶ Action Agent                   │
│  - tìm manual chunk           - tạo inspection task           │
│  - citations                  - tạo purchase draft            │
│  - căn cứ kỹ thuật            - không auto approve            │
│                                                             │
│  Approval Agent ────────────▶ Notification Agent             │
│  - tìm policy/approver        - route theo contact/escalation  │
│  - human gate                 - gửi n8n webhook, ghi sent/failed│
└──────────────────────────────┬──────────────────────────────┘
                               │ tool calls / state / audit
┌──────────────────────────────▼──────────────────────────────┐
│                    Backend Domain Services                  │
│ Ontology Service | Rule Engine | RAG Service | Purchase API  │
│ Approval | Org Routing | Audit | Notification | Telemetry    │
│ Realtime Rules                                               │
└──────────────┬───────────────┬───────────────┬──────────────┘
               │               │               │
┌──────────────▼───┐   ┌───────▼────────┐  ┌───▼──────────────┐
│ PostgreSQL       │   │ MinIO          │  │ OpenAI/Gemini API │
│ business data    │   │ manual files   │  │ LLM + embedding   │
│ pgvector         │   │ originals      │  │ tool-call JSON    │
│ telemetry        │   └────────────────┘  └──────────────────┘
│ agent_runs       │
│ agent_events     │
│ audit_logs       │
└──────────────┬───┘
               │
┌──────────────▼───┐
│ Neo4j            │
│ Ontology graph   │
│ relationships    │
└──────────────┬───┘
               │
┌──────────────▼───────────────────────────────────────────────┐
│                         n8n Webhook                          │
│ Email | Slack/Teams/Zalo nội bộ | Ticket system | ERP bridge  │
└──────────────────────────────────────────────────────────────┘
```

## Agentic workflow

```text
Trigger
  │
  ├─ User hỏi chat: "ELV-CALIDAS-01 có cần thay cáp không?"
  ├─ User bấm "Chạy suy luận"
  └─ Scheduled job 07:00 hằng ngày
       │
       ▼
Agent Orchestrator
  -> tạo agent_run
  -> xác định intent/workflow
  -> chọn agent/tool cần gọi
  -> ghi agent_events
       │
       ▼
Ontology Agent
  -> tool: get_asset_ontology(asset_code)
  -> đọc Neo4j: Asset -> Component -> Rule -> Manual -> Inventory -> Approval -> Org Routing
       │
       ▼
RAG Agent
  -> tool: search_manual_chunks(query)
  -> tìm căn cứ manual, citation, rule source
       │
       ▼
Reasoning Agent
  -> tool: run_rule_engine(asset/component)
  -> kiểm tra component_type = cable và remaining_lifetime_months <= 6
  -> output: finding
       │
       ▼
Action Agent
  -> create_inspection_task
  -> check_inventory
  -> create_purchase_request_draft
  -> guardrail: không tạo đơn mua hàng thật, không approve thay người
       │
       ▼
Approval Agent
  -> tool: get_approval_policy(request_type)
  -> xác định approval_policy_code, final_approver, human approval required
       │
       ▼
Notification Agent
  -> tool: get_notification_targets(asset_code, severity, event_type)
  -> route theo primary_contact, backup_contact, notification_group, escalation_policy
  -> send_n8n_webhook(event)
  -> gửi email/chat/ticket/ERP bridge
  -> ghi notification_sent hoặc notification_failed
       │
       ▼
Response Agent
  -> LLM tổng hợp JSON: conclusion, evidence, recommended_actions, missing_data, citations
```

## Tổ chức và escalation workflow

```text
Rule hoặc Alert được kích hoạt
  -> Ontology Agent lấy Asset owner, primary_contact, backup_contact
  -> Approval Agent xác định người có quyền phê duyệt nếu có purchase flow
  -> Notification Agent lấy escalation policy và notification group
  -> gửi thông báo cho người xử lý đầu tiên
  -> nếu quá SLA hoặc chưa acknowledge thì escalate lên cấp tiếp theo
  -> mọi bước gửi/escalate đều ghi audit log và notification event
```

## Digital Twin realtime workflow

```text
Sensor / Simulator / MQTT Gateway
  -> POST /api/telemetry/readings hoặc MQTT topic
  -> Telemetry Service validate sensor_code, metric, timestamp, quality
  -> lưu SensorReading vào PostgreSQL hoặc TimescaleDB
  -> Realtime Rule Engine kiểm tra threshold/window/min_samples
  -> Sensor Alert Service tạo hoặc update SensorAlert
  -> Ontology Sync Service upsert Sensor/SensorAlert vào Neo4j
  -> Realtime API push/polling cho dashboard và 3D Twin
  -> Action Agent tạo inspection task nếu rule cho phép
  -> Chat Agent dùng telemetry evidence khi trả lời
```

## Vai trò agent

| Agent | Có dùng LLM? | Vai trò |
|---|---|---|
| Chat Agent | Có | Hiểu câu hỏi, gọi tool context, trả JSON có citations |
| Response Agent | Có | Diễn giải kết quả thành câu trả lời có cấu trúc |
| Ontology Agent | Không bắt buộc | Query Neo4j graph và asset context |
| RAG Agent | Có thể | Search manual/embedding và trả citation |
| Reasoning Agent | Không | Chạy rule deterministic, không dựa vào suy đoán LLM |
| Action Agent | Không | Tạo task/purchase request draft theo rule được phép |
| Approval Agent | Không | Xác định policy, approver và human gate |
| Notification Agent | Không | Chọn người nhận theo contact/escalation, gửi n8n webhook và ghi trạng thái gửi |
| Telemetry Agent | Không | Nhận sensor reading, chuẩn hóa metric và lưu time-series |
| Realtime Rule Agent | Không | Chạy rule threshold/window từ sensor, tạo SensorAlert |

## Ranh giới quyết định

- LLM không phải bộ não quyết định nghiệp vụ.
- LLM là lớp giao tiếp, chọn tool có schema và tổng hợp kết quả.
- Rule Engine + Ontology + Domain Services là nơi quyết định nghiệp vụ.
- Action Agent chỉ thực thi hành động được phép.
- Human approval là chốt kiểm soát cuối cho mua hàng/phê duyệt.
- Mọi agent action phải ghi `agent_runs`, `agent_events` hoặc `audit_logs`.

## Vai trò service

- `frontend`: dashboard vận hành, nút chạy reasoning, bảng task/purchase request, Ontology map, manual upload, chat panel và 3D Twin.
- `backend`: FastAPI API, domain service, agent workflow entrypoint.
- `postgres`: dữ liệu giao dịch, audit, pgvector, agent runs/events, sensor readings MVP.
- `timescale`: lựa chọn nâng cấp cho sensor readings khi telemetry nhiều.
- `neo4j`: Ontology graph, quan hệ nghiệp vụ, Sensor/SensorAlert relationship.
- `org_routing`: lớp domain dùng ontology để chọn người nhận thông báo, owner tài sản và tuyến escalation.
- `minio`: lưu manual/file gốc.
- `manual_chunks`: nội dung đã parse/chunk trong PostgreSQL để phục vụ RAG.
- `llm_agent`: gọi Gemini/OpenAI khi có API key để tổng hợp JSON có guardrail.
- `n8n`: automation/notification ra hệ thống ngoài.
- `mqtt`: lựa chọn Phase 10 cho thiết bị thật hoặc simulator stream.
- `threejs`: mô phỏng 3D Digital Twin trên frontend.

## Ranh giới dữ liệu

- PostgreSQL là source of record cho dữ liệu giao dịch và telemetry MVP.
- Neo4j là source of truth cho quan hệ Ontology, không lưu từng sensor reading dày đặc.
- MinIO lưu file gốc.
- LLM chỉ nhận context đã được backend chuẩn bị từ tool/domain service.
- API key model chỉ nằm ở backend, không đưa xuống frontend.
- 3D Twin chỉ là view; trạng thái phải đến từ API telemetry/alert/ontology.
