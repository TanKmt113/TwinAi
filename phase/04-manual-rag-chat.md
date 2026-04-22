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

```text
Storage: MinIO
Parsing: Docling hoặc Unstructured
OCR: Tesseract nếu tài liệu scan
Embedding: text-embedding-3-small
Vector store: PostgreSQL + pgvector
LLM: OpenAI API
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
rule_explanation
purchase_reason
approval_query
manual_source_query
out_of_scope
```

## Tool mà LLM được gọi

```text
get_asset_risks()
get_asset_ontology(asset_code)
get_rule(rule_code)
search_manual_chunks(query)
get_purchase_request_reason(request_id)
get_approval_policy(request_type)
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
  "conclusion": "",
  "evidence": [],
  "recommended_actions": [],
  "missing_data": [],
  "citations": []
}
```

## Deliverables

- Upload manual.
- Lưu manual gốc vào MinIO.
- Parse/chunk manual.
- Tạo embedding.
- Search manual chunk bằng pgvector.
- Link `Rule -> Manual` trong Neo4j.
- Chat endpoint trả lời có citations.
- UI chat đơn giản.

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

