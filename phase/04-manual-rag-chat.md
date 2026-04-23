# Phase 04: Manual + RAG + Chat

## Mục tiêu

Thêm khả năng upload manual, tìm nguồn căn cứ và hỏi đáp tiếng Việt có citations.

## Phạm vi

Phase này không thay Rule Engine. Rule Engine đã có từ Phase 02. RAG/Chat chỉ bổ sung lớp diễn giải và truy xuất nguồn.

## Luồng manual

```text
Upload manual
  -> lưu file gốc vào MinIO
  -> parse text
  -> chia chunk
  -> tạo embedding
  -> lưu chunk + embedding vào PostgreSQL/pgvector
  -> liên kết Manual node trong Neo4j với Rule node
```

## Công cụ

**Theo spec gốc (tài liệu thiết kế):**

```text
Storage: MinIO
Parsing: Docling hoặc Unstructured
OCR: Tesseract nếu tài liệu scan
Embedding: text-embedding-3-small
Vector store: PostgreSQL + pgvector
LLM: OpenAI API
```

**Theo code hiện tại (đồng bộ repo):**

```text
Storage: MinIO (upload/đọc file manual)
Parse: txt, md, csv, pdf (pypdf), docx — không dùng Docling/Unstructured trong MVP này
Embedding: Gemini (gemini-embedding-*) hoặc OpenAI (text-embedding-3-small) theo LLM_PROVIDER
Vector search: PostgreSQL + pgvector; truy vấn chỉ so khớp chunk cùng số chiều với embedding query (tránh lỗi legacy chunk dimension khác)
LLM chat: Gemini hoặc OpenAI (JSON response) qua LlmAgentClient
Health: GET /health/services (Postgres, Neo4j, MinIO, LLM, n8n); UI Tổng quan hiển thị trạng thái dịch vụ
Chat UI: banner “LLM đang bật / không gọi LLM” + agent_mode kỹ thuật
Docker: backend dùng env_file ../apps/api/.env để GEMINI_* / OPENAI_* không bị ghi đè rỗng bởi ${VAR:-}
```

## API cần build

```text
POST /api/manuals/upload
GET  /api/manuals
GET  /api/manuals/{manual_id}
POST /api/manuals/{manual_id}/parse
GET  /api/manuals/{manual_id}/chunks
POST /api/chat/query
```

## Chat intents MVP

```text
asset_risk_query
asset_component_count_query
rule_explanation
purchase_reason
approval_query
manual_source_query
out_of_scope
```

`asset_component_count_query`: phân loại khi hỏi số lượng linh kiện; context chat không kéo rule/manual/purchase không cần thiết.

## Tool mà LLM được gọi

Trong response `tool_calls` (chuỗi logic, không phải HTTP endpoint riêng):

```text
classify_intent
get_asset_risks
get_asset_component_counts
get_asset_ontology
get_rule
search_manual_chunks
get_purchase_request_reason
get_approval_policy
```

Với intent `asset_component_count_query`, chỉ dùng: `classify_intent`, `get_asset_component_counts`, `get_asset_ontology`.

## Chat agent flow

```text
User question
  -> Chat Agent phân loại intent
  -> gom tool context từ Ontology/RAG/Rule/Purchase/Approval
  -> nếu có GEMINI_API_KEY hoặc OPENAI_API_KEY: gọi LLM để tổng hợp JSON
  -> nếu không có key hoặc LLM lỗi: fallback rule-based response
  -> ghi agent_run với agent_mode và tool_calls
```

`agent_mode` cần thể hiện rõ trạng thái:

```text
llm_tool_agent:gemini
llm_tool_agent:openai
rule_fallback_no_llm_key
rule_fallback_after_llm_error
guardrail_out_of_scope
```

## Guardrail

LLM phải tuân thủ:

```text
Chỉ trả lời dựa trên dữ liệu từ tools/context.
Không tự tạo rule.
Không tự tạo số liệu.
Không tự quyết định mua hàng.
Nếu thiếu dữ liệu, trả lời "không đủ dữ liệu".
Mỗi kết luận quan trọng phải có citation.
```

## Response format

```json
{
  "intent": "",
  "conclusion": "",
  "evidence": [],
  "recommended_actions": [],
  "missing_data": [],
  "citations": [],
  "agent_mode": "",
  "tool_calls": []
}
```

## Deliverables

- Upload manual.
- Lưu manual gốc vào MinIO.
- Parse/chunk manual.
- Tạo embedding.
- Search manual chunk bằng pgvector.
- Link `Rule -> Manual` trong Neo4j.
- Chat endpoint trả lời có citations, `agent_mode` và `tool_calls`.
- UI chat hiển thị intent, agent mode, tool calls, evidence và citations.

## Tiêu chí hoàn thành

Phase 04 đạt khi người dùng hỏi:

```text
Có thang máy nào sắp cần kiểm tra hoặc thay linh kiện không?
```

Hệ thống trả lời có:

- Kết luận.
- Rule kích hoạt.
- Manual/source liên quan.
- Task/purchase request đã tạo.
- Dữ liệu tồn kho.
- Người phê duyệt.
- Citations.

Ghi chú mở rộng:

- Câu hỏi kiểu `notification_query` hoặc `escalation_query` sẽ thuộc phạm vi Phase 05 sau khi org routing API được implement.

---

## Trạng thái hoàn thành vs tồn đọng (trước Phase 05)

**Đã đáp ứng tiêu chí cốt lõi Phase 04:** upload/parse/chunk/embed/search manual, chat có citations + `agent_mode` + `tool_calls`, guardrail out-of-scope, Neo4j link manual–rule khi sync bật.

**Tồn đọng nhẹ (không chặn Phase 05):**

- Dữ liệu seed/manual cũ có thể còn embedding dimension khác model hiện tại — code đã lọc theo chiều vector; nên re-parse manual để dữ liệu đồng nhất.
- OCR/Tesseract và Docling chưa tích hợp; PDF scan chất lượng kém có thể parse kém.
- Chat chưa gọi trực tiếp bảng `org_users` / `org_units` (đã có trong DB — xem Phase 05 và `docs/api.md`); routing “báo cho ai” vẫn chủ yếu từ `final_approver` chuỗi trên purchase + department_owner trên asset.

**Kết luận:** Có thể bắt đầu Phase 05 khi đã xác nhận manual/RAG/chat chạy ổn trên môi trường deploy; các hạng mục trên là cải tiến song song, không phải blocker cứng.

Với câu hỏi ngoài phạm vi:

```text
Dự báo doanh thu tháng sau là bao nhiêu?
```

Hệ thống phải trả:

```text
Không đủ dữ liệu.
```

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Chat trả lời như chatbot tự do | Bắt buộc dùng tool và response JSON |
| Manual parse sai | Hiển thị chunk/source để người dùng kiểm tra |
| Embedding tìm sai đoạn | Cho phép filter theo manual/department/domain |
| LLM hallucination | Nếu không có citation thì không cho kết luận chắc chắn |
