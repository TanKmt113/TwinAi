# Architecture

Phase 4 có dashboard vận hành, Ontology map, upload/parse manual, Chat/RAG có citations và chat agent có tool context. Lớp Agentic AI phải được hiểu là workflow có guardrail, không phải một chatbot tự quyết định nghiệp vụ.

## Tổng quan hệ thống

```text
┌─────────────────────────────────────────────────────────────┐
│                         Next.js UI                          │
│ Dashboard | Ontology Map | Chat | Task | Purchase | Admin    │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST/JSON
┌──────────────────────────────▼──────────────────────────────┐
│                         FastAPI API                         │
│ Auth | Asset API | Manual API | Rule API | Chat API          │
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
│  - tìm policy/approver        - gửi n8n webhook               │
│  - human gate                 - ghi sent/failed               │
└──────────────────────────────┬──────────────────────────────┘
                               │ tool calls / state / audit
┌──────────────────────────────▼──────────────────────────────┐
│                    Backend Domain Services                  │
│ Ontology Service | Rule Engine | RAG Service | Purchase API  │
│ Approval Service | Audit Service | Notification Service      │
└──────────────┬───────────────┬───────────────┬──────────────┘
               │               │               │
┌──────────────▼───┐   ┌───────▼────────┐  ┌───▼──────────────┐
│ PostgreSQL       │   │ MinIO          │  │ OpenAI/Gemini API │
│ business data    │   │ manual files   │  │ LLM + embedding   │
│ pgvector         │   │ originals      │  │ tool-call JSON    │
│ agent_runs       │   └────────────────┘  └──────────────────┘
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
  -> đọc Neo4j: Asset -> Component -> Rule -> Manual -> Inventory -> Approval
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
  -> tool: send_n8n_webhook(event)
  -> gửi email/chat/ticket/ERP bridge
  -> ghi notification_sent hoặc notification_failed
       │
       ▼
Response Agent
  -> LLM tổng hợp JSON: conclusion, evidence, recommended_actions, missing_data, citations
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
| Notification Agent | Không | Gửi n8n webhook và ghi trạng thái gửi |

## Ranh giới quyết định

- LLM không phải bộ não quyết định nghiệp vụ.
- LLM là lớp giao tiếp, chọn tool có schema và tổng hợp kết quả.
- Rule Engine + Ontology + Domain Services là nơi quyết định nghiệp vụ.
- Action Agent chỉ thực thi hành động được phép.
- Human approval là chốt kiểm soát cuối cho mua hàng/phê duyệt.
- Mọi agent action phải ghi `agent_runs`, `agent_events` hoặc `audit_logs`.

## Vai trò service

- `frontend`: dashboard vận hành, nút chạy reasoning, bảng task/purchase request, Ontology map, manual upload và chat panel.
- `backend`: FastAPI API, domain service, agent workflow entrypoint.
- `postgres`: dữ liệu giao dịch, audit, pgvector, agent runs/events.
- `neo4j`: Ontology graph và quan hệ nghiệp vụ.
- `minio`: lưu manual/file gốc.
- `manual_chunks`: nội dung đã parse/chunk trong PostgreSQL để phục vụ RAG.
- `llm_agent`: gọi Gemini/OpenAI khi có API key để tổng hợp JSON có guardrail.
- `n8n`: automation/notification ra hệ thống ngoài.

## Ranh giới dữ liệu

- PostgreSQL là source of record cho dữ liệu giao dịch.
- Neo4j là source of truth cho quan hệ Ontology.
- MinIO lưu file gốc.
- LLM chỉ nhận context đã được backend chuẩn bị từ tool/domain service.
- API key model chỉ nằm ở backend, không đưa xuống frontend.
