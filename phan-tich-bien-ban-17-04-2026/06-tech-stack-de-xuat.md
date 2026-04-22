# Tech stack đề xuất cho hệ thống Agentic AI Ontology

Tài liệu này đề xuất nền tảng kỹ thuật để chuyển bản demo Agentic AI bảo trì thang máy thành một hệ thống thực tế có thể triển khai nội bộ.

## 1. Mục tiêu kỹ thuật

Hệ thống cần đạt các mục tiêu sau:

1. Quản lý manual, quy trình và dữ liệu vận hành nội bộ.
2. Mô hình hóa Ontology: tài sản, linh kiện, quy tắc, tồn kho, mua hàng, phê duyệt.
3. Chạy rule suy luận có căn cứ, không phụ thuộc vào suy đoán của LLM.
4. Cho phép người dùng hỏi bằng tiếng Việt tự nhiên.
5. Trả lời có nguồn căn cứ, rule liên quan và dữ liệu chứng minh.
6. Tạo task/cảnh báo/đề xuất mua hàng.
7. Có phê duyệt, phân quyền và audit log.
8. Có khả năng triển khai nội bộ, bảo vệ dữ liệu công ty.

## 2. Nguyên tắc thiết kế

### 2.1. Ontology là lõi logic

Ontology phải là lớp quyết định chính:

- Thực thể nào tồn tại trong hệ thống.
- Thực thể liên kết với nhau như thế nào.
- Điều kiện nào kích hoạt hành động.
- Ai chịu trách nhiệm.
- Cần bằng chứng nào để ra quyết định.

LLM không được tự tạo rule nghiệp vụ.

### 2.2. LLM chỉ là lớp giao diện và diễn giải

LLM nên làm các việc sau:

- Hiểu câu hỏi của người dùng.
- Tìm đúng tài liệu, rule và dữ liệu liên quan.
- Gọi backend/tool để lấy kết quả thật.
- Diễn giải kết quả bằng tiếng Việt dễ hiểu.
- Nêu rõ dữ liệu thiếu nếu chưa đủ căn cứ.

LLM không nên:

- Tự quyết định mua hàng.
- Tự thay đổi quy trình phê duyệt.
- Tự tạo dữ liệu không có trong hệ thống.
- Trả lời chắc chắn khi thiếu căn cứ.

### 2.3. MVP phải nhỏ nhưng chạy thật

MVP không nên cố mô hình hóa toàn bộ công ty. Nên bắt đầu với một use case rõ ràng:

- Bảo trì thang máy.
- Linh kiện cáp kéo.
- Tuổi thọ còn lại.
- Tồn kho phụ tùng.
- Lead time mua hàng.
- Người phê duyệt.

## 3. Kiến trúc tổng quan

```text
Frontend Web App
    |
Backend API
    |
    |-- Relational Database
    |-- Vector Search
    |-- Object Storage
    |-- Ontology / Rule Engine
    |-- LLM Gateway
    |-- Agent Worker
    |-- Workflow / Approval
    |-- Audit Log
```

Luồng xử lý chính:

```text
Upload manual
    -> Parse/OCR tài liệu
    -> Chia chunk
    -> Tạo embedding
    -> Lưu tài liệu và vector
    -> Người nghiệp vụ định nghĩa rule
    -> Rule được phê duyệt
    -> Agent chạy suy luận
    -> Tạo cảnh báo/task/đề xuất mua hàng
    -> Người có quyền phê duyệt
    -> Lưu audit log
```

## 4. Tech stack đề xuất cho MVP

### 4.1. Frontend

Đề xuất: **Next.js / React**

Vai trò:

- Dashboard tài sản và cảnh báo.
- Bản đồ Ontology.
- Màn hình hỏi đáp.
- Màn hình task/cảnh báo.
- Màn hình phê duyệt.
- Màn hình quản lý manual và rule.

Lý do chọn:

- Phù hợp để phát triển nhanh dashboard nội bộ.
- Có hệ sinh thái UI tốt.
- Dễ tích hợp API backend.
- Có thể mở rộng sang auth, phân quyền, server-side rendering nếu cần.

Thư viện UI có thể dùng:

- Tailwind CSS.
- shadcn/ui.
- React Flow cho sơ đồ Ontology.
- TanStack Table cho bảng dữ liệu.

### 4.2. Backend API

Đề xuất: **Python FastAPI**

Vai trò:

- Cung cấp API cho frontend.
- Xử lý upload manual.
- Chạy pipeline parse tài liệu.
- Kết nối database/vector store/LLM.
- Chạy rule suy luận.
- Tạo task/cảnh báo/đề xuất mua hàng.

Lý do chọn:

- Python phù hợp với AI/document processing.
- FastAPI nhẹ, nhanh, dễ viết API có schema rõ ràng.
- Dễ tích hợp OpenAI, Qdrant, Neo4j, PostgreSQL, OCR.

### 4.3. Database chính

Đề xuất: **PostgreSQL**

Vai trò:

- Lưu tài sản.
- Lưu linh kiện.
- Lưu tồn kho.
- Lưu rule.
- Lưu task.
- Lưu yêu cầu mua hàng.
- Lưu phê duyệt.
- Lưu audit log.

Lý do chọn:

- Ổn định, phổ biến, dễ vận hành.
- Phù hợp dữ liệu nghiệp vụ có cấu trúc.
- Có thể mở rộng bằng `pgvector` để lưu vector embedding.
- Dễ backup, phân quyền và audit.

### 4.4. Vector search

Đề xuất cho MVP: **pgvector**

Vai trò:

- Lưu embedding của các đoạn manual.
- Tìm đoạn tài liệu liên quan khi người dùng hỏi.
- Hỗ trợ RAG có căn cứ.

Lý do chọn:

- Chạy chung trong PostgreSQL, giảm độ phức tạp.
- Đủ tốt cho MVP và dữ liệu nội bộ nhỏ.
- Dễ query kết hợp metadata bằng SQL.

Khi nên chuyển sang Qdrant:

- Số lượng tài liệu lớn.
- Cần hybrid search mạnh hơn.
- Cần performance cao cho vector search.
- Cần scale độc lập với database nghiệp vụ.

### 4.5. Object storage

Đề xuất: **MinIO**

Vai trò:

- Lưu file manual gốc.
- Lưu PDF, DOCX, ảnh scan.
- Lưu version tài liệu.

Lý do chọn:

- Có thể self-host nội bộ.
- Tương thích API S3.
- Phù hợp yêu cầu chủ quyền dữ liệu.

### 4.6. Document parsing / OCR

Đề xuất:

- **Docling** hoặc **Unstructured** cho PDF/DOCX.
- **Tesseract OCR** cho ảnh scan.

Vai trò:

- Trích xuất text từ manual.
- Giữ cấu trúc heading, bảng, danh sách nếu có thể.
- Chia tài liệu thành chunk có metadata.

Metadata nên lưu:

- Tên tài liệu.
- Bộ phận sở hữu.
- Phiên bản.
- Trang.
- Heading.
- Loại tài liệu.
- Ngày hiệu lực.

### 4.7. LLM

Đề xuất cho MVP: **OpenAI API**

Vai trò:

- Hiểu câu hỏi tiếng Việt.
- Sinh câu trả lời có cấu trúc.
- Gọi tool/backend qua function calling.
- Diễn giải kết quả từ Ontology.

Lý do chọn:

- Nhanh để MVP.
- Chất lượng tiếng Việt tốt.
- Hỗ trợ structured output/function calling.
- Giảm thời gian vận hành model.

Khi nào cân nhắc local LLM:

- Dữ liệu không được phép ra khỏi hạ tầng nội bộ.
- Công ty muốn Sovereign AI hoàn toàn.
- Có đủ GPU và nhân sự vận hành model.

Ứng viên local LLM:

- Llama.
- Qwen.
- Mistral.
- Gemma.

### 4.8. Embedding model

Đề xuất:

- MVP: `text-embedding-3-small`.
- Khi cần chất lượng cao hơn: `text-embedding-3-large`.

Vai trò:

- Biến đoạn manual thành vector.
- Tìm tài liệu liên quan theo ngữ nghĩa.

Lưu ý:

- Embedding chỉ giúp tìm kiếm.
- Không thay thế Ontology.
- Không được dùng embedding để ra quyết định nghiệp vụ.

### 4.9. Ontology / Rule Engine

Đề xuất cho MVP: **dùng Neo4j ngay cho Ontology graph**.

Vai trò của Neo4j:

- Lưu graph Ontology: tài sản, linh kiện, rule, manual, phụ tùng, tồn kho, mua hàng, phê duyệt.
- Truy vấn chuỗi quan hệ nhiều bước bằng Cypher.
- Hiển thị bản đồ Ontology cho người dùng.
- Cung cấp context có cấu trúc cho LLM.
- Giữ logic liên kết dữ liệu tách khỏi bảng nghiệp vụ thuần túy.

Vai trò của Rule Engine:

- Rule Engine vẫn nằm trong backend FastAPI.
- Rule Engine đọc node/relationship từ Neo4j và dữ liệu nghiệp vụ từ PostgreSQL khi cần.
- Rule phải có schema rõ ràng và trạng thái phê duyệt.
- Rule không được để LLM tự tạo hoặc tự sửa.

PostgreSQL vẫn dùng cho:

- Giao dịch nghiệp vụ.
- Task kiểm tra.
- Purchase request.
- Approval.
- Audit log.
- Manual chunks và vector embedding nếu dùng pgvector.

Neo4j dùng cho:

- Ontology graph.
- Mối quan hệ giữa thực thể.
- Truy vấn reasoning theo quan hệ.
- Graph visualization.

Ví dụ rule:

```yaml
rule_id: elevator_cable_inspection_6_months
name: Cảnh báo cáp kéo còn dưới 6 tháng tuổi thọ
condition:
  component_type: cable
  remaining_lifetime_months_lte: 6
actions:
  - create_inspection_task
  - check_inventory
  - evaluate_purchase_request
source: Manual bảo trì thang máy
status: approved
owner: Trưởng bộ phận kỹ thuật
```

Graph model MVP trong Neo4j:

```text
(:Asset)-[:HAS_COMPONENT]->(:Component)
(:Component)-[:HAS_TYPE]->(:ComponentType)
(:Component)-[:APPLIES_RULE]->(:Rule)
(:Rule)-[:BASED_ON]->(:Manual)
(:Component)-[:REQUIRES_SPARE_PART]->(:SparePart)
(:SparePart)-[:STORED_AS]->(:InventoryItem)
(:InventoryItem)-[:TRIGGERS_PURCHASE]->(:PurchaseRequest)
(:PurchaseRequest)-[:REQUIRES_APPROVAL]->(:ApprovalPolicy)
(:ApprovalPolicy)-[:FINAL_APPROVER]->(:User)
```

Ví dụ Cypher:

```cypher
MATCH (a:Asset {code: "ELV-CALIDAS-01"})-[:HAS_COMPONENT]->(c:Component)-[:APPLIES_RULE]->(r:Rule)
OPTIONAL MATCH (c)-[:REQUIRES_SPARE_PART]->(sp:SparePart)-[:STORED_AS]->(inv:InventoryItem)
OPTIONAL MATCH (pr:PurchaseRequest)-[:FOR_COMPONENT]->(c)-[:REQUIRES_SPARE_PART]->(sp)
OPTIONAL MATCH (pr)-[:REQUIRES_APPROVAL]->(ap:ApprovalPolicy)-[:FINAL_APPROVER]->(u:User)
RETURN a, c, r, sp, inv, pr, ap, u
```

Khuyến nghị thực tế:

- MVP: dùng PostgreSQL + Neo4j song song.
- PostgreSQL là source of record cho dữ liệu giao dịch.
- Neo4j là source of truth cho Ontology/relationship.
- Backend cần có service đồng bộ các thực thể quan trọng từ PostgreSQL sang Neo4j.
- Không lưu audit log chính trong Neo4j; audit nên nằm ở PostgreSQL.

### 4.10. Agent workflow

Giai đoạn MVP:

- Tự viết state machine đơn giản.
- Job chạy định kỳ bằng Celery/Redis Queue/APScheduler.

Ví dụ trạng thái:

```text
detected
  -> inspection_task_created
  -> inventory_checked
  -> purchase_request_created
  -> waiting_for_approval
  -> approved
  -> closed
```

Giai đoạn production:

- Dùng **Temporal** nếu workflow kéo dài nhiều ngày/tháng.
- Dùng **LangGraph** nếu cần agent nhiều bước, human-in-the-loop và trạng thái hội thoại/phân nhánh.

Khuyến nghị:

- Nếu workflow chủ yếu là nghiệp vụ cố định: Temporal.
- Nếu workflow có nhiều bước AI/tool-calling linh hoạt: LangGraph.
- Nếu chỉ MVP: tự viết đơn giản trước.

### 4.11. Workflow automation

Đề xuất: **n8n**

Vai trò:

- Gửi email cảnh báo.
- Gửi thông báo Slack/Teams/Zalo nội bộ nếu có API.
- Gọi webhook tạo ticket.
- Kết nối Google Sheet/ERP tạm thời.

Lý do chọn:

- Dễ demo.
- Có thể self-host.
- Nhiều connector.
- Phù hợp tích hợp nhanh trước khi xây integration chính thức.

Lưu ý:

- Không nên đặt logic Ontology cốt lõi trong n8n.
- n8n chỉ nên là lớp automation/integration.

### 4.12. Authentication và phân quyền

MVP:

- Auth đơn giản bằng username/password.
- Role-based access control trong backend.

Production:

- **Keycloak** hoặc tích hợp SSO nội bộ.

Role gợi ý:

- Admin.
- AI Team.
- Kỹ thuật.
- Kho.
- Mua hàng.
- Trưởng bộ phận.
- CEO/Approver.
- Viewer.

### 4.13. Logging, audit và monitoring

MVP:

- Lưu audit log trong PostgreSQL.
- Log backend ra file/container logs.

Production:

- OpenTelemetry.
- Grafana.
- Prometheus.
- Loki.
- Sentry.

Audit log cần ghi:

- Ai upload tài liệu.
- Ai tạo/sửa/phê duyệt rule.
- Agent đã chạy rule nào.
- Dữ liệu đầu vào là gì.
- Hành động nào được tạo.
- Ai phê duyệt hoặc từ chối.
- LLM đã dùng nguồn nào để trả lời.

## 5. Kiến trúc MVP khuyến nghị

```text
Next.js Frontend
    |
FastAPI Backend
    |
    |-- PostgreSQL + pgvector
    |-- Neo4j
    |-- MinIO
    |-- Rule Engine
    |-- OpenAI API
    |-- Background Worker
    |-- n8n Webhook
```

Đây là kiến trúc có thêm Neo4j ngay từ MVP để đội AI làm quen đúng với tư duy Ontology graph. Đổi lại, hệ thống sẽ phức tạp hơn một chút vì cần đồng bộ dữ liệu giữa PostgreSQL và Neo4j.

## 6. Kiến trúc production khuyến nghị

```text
Next.js Frontend
    |
API Gateway
    |
FastAPI Services
    |
    |-- PostgreSQL: nghiệp vụ, audit, approval
    |-- Neo4j: Ontology graph
    |-- Qdrant: vector search quy mô lớn
    |-- MinIO/S3: file manual gốc
    |-- Temporal: workflow dài hạn
    |-- LangGraph: agent orchestration
    |-- OpenAI hoặc local LLM gateway
    |-- Keycloak: auth/SSO
    |-- Grafana/Prometheus/Sentry: monitoring
```

Production chỉ nên đi theo hướng này khi MVP đã chứng minh được giá trị nghiệp vụ.

## 7. Database schema gợi ý cho MVP

### 7.1. Bảng nghiệp vụ chính

```text
assets
components
manuals
manual_chunks
rules
inventory_items
inspection_tasks
purchase_requests
approval_policies
approvals
agent_runs
audit_logs
```

### 7.2. Quan hệ cốt lõi

```text
assets 1-n components
components n-1 inventory_items
manuals 1-n manual_chunks
rules n-1 manuals
rules 1-n inspection_tasks
purchase_requests n-1 approval_policies
approval_policies n-1 approvers
agent_runs 1-n audit_logs
```

### 7.3. Trường quan trọng

`assets`:

- `id`
- `code`
- `name`
- `location`
- `department_owner`
- `status`

`components`:

- `id`
- `asset_id`
- `name`
- `type`
- `installed_at`
- `expected_lifetime_months`
- `remaining_lifetime_months`
- `last_inspection_at`

`rules`:

- `id`
- `code`
- `name`
- `condition_json`
- `action_json`
- `source_manual_id`
- `owner_user_id`
- `status`
- `version`

`manual_chunks`:

- `id`
- `manual_id`
- `chunk_text`
- `page_number`
- `heading`
- `embedding`

`inspection_tasks`:

- `id`
- `asset_id`
- `component_id`
- `rule_id`
- `status`
- `evidence_required_json`
- `assigned_to`
- `due_date`

`purchase_requests`:

- `id`
- `component_id`
- `inventory_item_id`
- `reason`
- `status`
- `approver_id`
- `created_from_rule_id`

## 8. API gợi ý cho MVP

```text
POST   /manuals/upload
GET    /manuals
GET    /manuals/{id}

GET    /assets
GET    /assets/{id}
GET    /assets/{id}/ontology

GET    /rules
POST   /rules
POST   /rules/{id}/approve

POST   /reasoning/run
GET    /agent-runs
GET    /agent-runs/{id}

GET    /tasks
POST   /tasks/{id}/complete

GET    /purchase-requests
POST   /purchase-requests/{id}/approve
POST   /purchase-requests/{id}/reject

POST   /chat/query
GET    /audit-logs
```

## 9. Lộ trình triển khai

### Giai đoạn 1: MVP nền tảng

Thời gian: 2-4 tuần

Việc cần làm:

- Tạo backend FastAPI.
- Tạo PostgreSQL schema.
- Tạo dữ liệu mẫu thang máy.
- Tạo rule engine đơn giản.
- Tạo API `POST /reasoning/run`.
- Tạo dashboard Next.js.
- Hiển thị cảnh báo/task/đề xuất mua hàng.

Kết quả:

- Hệ thống chạy được use case bảo trì thang máy bằng dữ liệu có cấu trúc.

### Giai đoạn 2: Manual và RAG có căn cứ

Thời gian: 2-4 tuần

Việc cần làm:

- Upload manual PDF/DOCX.
- Parse manual thành text.
- Chunk tài liệu.
- Tạo embedding.
- Lưu vào pgvector.
- Cho phép hỏi đáp có trích nguồn.

Kết quả:

- Người dùng hỏi bằng tiếng Việt và nhận câu trả lời có căn cứ từ manual.

### Giai đoạn 3: Rule approval và audit

Thời gian: 2-3 tuần

Việc cần làm:

- Tạo màn hình quản lý rule.
- Thêm trạng thái rule: draft, validated, approved, archived.
- Thêm người owner nghiệp vụ.
- Thêm audit log cho thay đổi rule.
- Chặn rule chưa approved không được chạy production.

Kết quả:

- Ontology/rule có quản trị, không bị tự ý thay đổi.

### Giai đoạn 4: Agent hành động

Thời gian: 2-4 tuần

Việc cần làm:

- Agent chạy định kỳ.
- Tạo task kiểm tra.
- Kiểm tra tồn kho.
- Tạo purchase request.
- Gửi thông báo qua n8n/email.
- Có màn hình phê duyệt.

Kết quả:

- Hệ thống không chỉ hỏi đáp mà bắt đầu tạo hành động vận hành.

### Giai đoạn 5: Mở rộng Ontology

Thời gian: sau khi MVP chứng minh giá trị

Use case mở rộng:

- PCCC.
- Bãi xe.
- Housekeeping.
- Điện/nước.
- Mua hàng.
- Nhân sự/phê duyệt.

Kết quả:

- Từ một use case thang máy mở rộng thành lớp tri thức vận hành nội bộ.

## 10. Những điều không nên làm ở giai đoạn đầu

Không nên:

- Xây ERP mới.
- Xây chatbot trước khi có rule engine.
- Đưa toàn bộ tài liệu vào LLM rồi để LLM tự trả lời.
- Lưu mọi thứ vào Neo4j và bỏ qua PostgreSQL cho dữ liệu giao dịch/audit.
- Dùng Kubernetes ngay nếu đội chưa cần scale.
- Tự fine-tune model quá sớm.
- Tự động gửi yêu cầu mua hàng thật khi chưa có phê duyệt.

Nên:

- Bắt đầu từ một use case nhỏ.
- Dữ liệu hóa tài sản và linh kiện.
- Viết rule rõ ràng.
- Gắn rule với manual và owner nghiệp vụ.
- Cho LLM trả lời dựa trên kết quả backend.
- Lưu audit log mọi hành động.

## 11. Kết luận đề xuất

Tech stack nên dùng cho bước đầu:

```text
Frontend: Next.js + React
Backend: Python FastAPI
Database: PostgreSQL + pgvector
Ontology graph: Neo4j
Storage: MinIO
Document parsing: Docling/Unstructured + Tesseract OCR
LLM: OpenAI API
Embedding: text-embedding-3-small
Rule Engine: tự xây trong backend, đọc graph từ Neo4j
Agent Worker: Celery hoặc APScheduler
Automation: n8n
Deploy: Docker Compose nội bộ
```

Tech stack này đủ để làm MVP thật, kiểm soát dữ liệu tốt, không quá phức tạp, và vẫn mở đường cho production sau này.
