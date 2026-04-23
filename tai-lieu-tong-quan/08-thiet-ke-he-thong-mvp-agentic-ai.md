# Thiết kế hệ thống MVP Agentic AI Ontology

Tài liệu này thiết kế hệ thống MVP dựa trên:

- `03-thiet-ke-mvp-agentic-ai.md`
- `06-tech-stack-de-xuat.md`
- `07-gia-lap-khoi-dong-mvp-thang-may.md`

Phạm vi thiết kế: hệ thống nội bộ cho use case **bảo trì thang máy - cảnh báo cáp kéo sắp hết tuổi thọ - tạo task kiểm tra - đề xuất mua hàng - phê duyệt - thông báo/escalation đúng người phụ trách**.

## 1. Mục tiêu hệ thống

Hệ thống MVP cần chứng minh được 6 năng lực:

1. Lưu dữ liệu vận hành có cấu trúc: thang máy, linh kiện, tồn kho, quy trình phê duyệt và cơ cấu tổ chức xử lý.
2. Lưu manual/quy trình và cho phép truy xuất nguồn căn cứ.
3. Chạy rule Ontology để phát hiện điều kiện cần hành động.
4. Tạo hành động vận hành: cảnh báo, task kiểm tra, đề xuất mua hàng.
5. Xác định được cần báo cho ai, escalate cho ai và ai là người phê duyệt cuối.
6. Cho phép hỏi đáp tiếng Việt dựa trên dữ liệu thật và rule đã phê duyệt.

## 2. Nguyên tắc thiết kế

### 2.1. Tách rõ Ontology và LLM

Ontology/rule engine quyết định:

- Có cảnh báo hay không.
- Có cần task kiểm tra hay không.
- Có cần đề xuất mua hàng hay không.
- Ai là người xử lý đầu tiên.
- Khi quá SLA thì escalate cho ai.
- Ai là người phê duyệt.

LLM chỉ làm:

- Hiểu câu hỏi tiếng Việt.
- Gọi API/tool phù hợp.
- Diễn giải kết quả từ backend.
- Trích nguồn manual/rule.
- Báo thiếu dữ liệu nếu chưa đủ căn cứ.

### 2.2. MVP nhỏ, dữ liệu thật tối thiểu

MVP chỉ cần chạy đúng một chuỗi:

```text
Thang máy -> Cáp kéo -> Tuổi thọ còn lại -> Rule kiểm tra -> Tồn kho -> Mua hàng -> Phê duyệt -> Thông báo/escalation
```

Không mở rộng sang PCCC, bãi xe, housekeeping hoặc toàn bộ ERP trong giai đoạn này.

### 2.3. Human-in-the-loop

Agent không được tự động tạo đơn mua hàng thật. Agent chỉ tạo:

- Cảnh báo.
- Task kiểm tra.
- Đề xuất mua hàng.

Người có thẩm quyền phải phê duyệt trước khi chuyển thành hành động chính thức.

## 3. Tech stack sử dụng

### 3.1. MVP stack

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
Agent Worker: APScheduler hoặc Celery
Automation: n8n webhook
Deploy: Docker Compose nội bộ
```

### 3.2. Lý do chọn stack này

- **Next.js**: phù hợp dashboard nội bộ, form quản trị, màn hình phê duyệt.
- **FastAPI**: phù hợp AI pipeline, rule engine, API rõ schema.
- **PostgreSQL**: đủ cho dữ liệu nghiệp vụ và audit.
- **Neo4j**: lưu Ontology graph ngay từ MVP, phù hợp yêu cầu kết nối dữ liệu có ý nghĩa.
- **pgvector**: lưu embedding manual trong cùng database để giảm độ phức tạp MVP.
- **MinIO**: lưu file manual gốc nội bộ.
- **OpenAI API**: tăng tốc MVP, xử lý tiếng Việt tốt.
- **n8n**: gửi thông báo/email/webhook nhanh, không đặt logic lõi ở đây.

## 4. Kiến trúc tổng thể

```text
[Sơ đồ kiến trúc mục tiêu theo roadmap Phase 01-10; MVP ban đầu ưu tiên Phase 01-06,
Digital Twin realtime mở rộng ở Phase 07-10]

┌─────────────────────────────────────────────────────────────┐
│                         Next.js UI                          │
│ Dashboard | Ontology Map | Chat | Task | Purchase | Admin    │
│ Approval Queue | Notification/Escalation | Telemetry | 3D Twin│
└──────────────────────────────┬──────────────────────────────┘
                               │ REST/JSON, polling/SSE/WebSocket
┌──────────────────────────────▼──────────────────────────────┐
│                         FastAPI API                         │
│ Auth | Asset API | Manual API | Rule API | Chat API          │
│ Org API | Approval API | Audit API | Telemetry API | Twin API │
└──────────────────────────────┬──────────────────────────────┘
                               │ user request / job / reading
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
│  - asset/component context    - phát hiện rủi ro/finding      │
│  - quan hệ nguồn              - không để LLM quyết định       │
│                                                             │
│  RAG Agent ─────────────────▶ Action Agent                   │
│  - tìm manual chunk           - tạo inspection task           │
│  - citations                  - tạo purchase draft            │
│  - căn cứ kỹ thuật            - không auto approve            │
│                                                             │
│  Approval Agent ────────────▶ Notification Agent             │
│  - tìm policy/approver        - route contact/escalation      │
│  - human gate                 - gửi n8n webhook, ghi trạng thái│
│                                                             │
│  Telemetry Agent ───────────▶ Realtime Rule Agent            │
│  - nhận sensor reading        - kiểm tra threshold/window     │
│  - chuẩn hóa metric/quality   - tạo/update SensorAlert        │
│  - attach evidence            - kích hoạt task/chat context   │
└──────────────────────────────┬──────────────────────────────┘
                               │ tool calls / state / audit
┌──────────────────────────────▼──────────────────────────────┐
│                    Backend Domain Services                  │
│ Ontology Service | Rule Engine | RAG Service | Purchase API  │
│ Approval | Org Routing | Audit | Notification | Telemetry    │
│ Realtime Rules | Sensor Alert | 3D Twin State | Object Store │
└──────────────┬───────────────┬───────────────┬──────────────┘
               │               │               │
┌──────────────▼───┐   ┌───────▼────────┐  ┌───▼──────────────┐
│ PostgreSQL       │   │ MinIO          │  │ OpenAI/Gemini API │
│ business data    │   │ manual files   │  │ LLM + embedding   │
│ pgvector         │   │ originals      │  │ tool-call JSON    │
│ org/audit data   │   └────────────────┘  └──────────────────┘
│ telemetry        │
│ sensor_alerts    │   ┌────────────────┐  ┌──────────────────┐
│ agent_runs/events│   │ TimescaleDB     │  │ MQTT / Simulator │
└──────────────┬───┘   │ optional later  │  │ optional ingest   │
               │       │ high-volume TS  │  │ Phase 07-10       │
               │       └────────────────┘  └──────────────────┘
               │ Ontology/SensorAlert sync từ domain services
┌──────────────▼───┐
│ Neo4j            │
│ Ontology graph   │
│ relationships    │
│ Sensor state     │
└──────────────┬───┘
               │
┌──────────────▼───────────────────────────────────────────────┐
│                         n8n Webhook                          │
│ Email | Slack/Teams/Zalo nội bộ | Ticket system | ERP bridge  │
└──────────────────────────────────────────────────────────────┘
```

Ghi chú quan trọng:

- LLM chỉ nằm ở lớp giao tiếp và tổng hợp phản hồi. Quyết định nghiệp vụ phải đi qua Rule Engine, Ontology, Domain Service và human approval.
- PostgreSQL là source of record cho dữ liệu giao dịch, audit, org, purchase request và telemetry MVP. TimescaleDB chỉ là lựa chọn nâng cấp khi sensor readings tăng lớn.
- Neo4j lưu quan hệ Ontology, quan hệ Asset/Component/Sensor/Rule/Alert và trạng thái tổng hợp; không lưu từng sensor reading dày đặc.
- 3D Twin là view vận hành đọc từ telemetry, SensorAlert và ontology mapping. 3D không được hard-code trạng thái cảnh báo.
- MQTT/simulator là nguồn ingest tùy phase. MVP có thể bắt đầu bằng `POST /api/telemetry/readings` và polling 3-5 giây.

## 5. Module hệ thống

### 5.1. Frontend Web App

Các màn hình cần có trong MVP:

1. **Dashboard tổng quan**
   - Số cảnh báo đang mở.
   - Số task kiểm tra.
   - Số đề xuất mua hàng chờ duyệt.
   - Tài sản rủi ro cao.

2. **Asset Management**
   - Danh sách thang máy.
   - Chi tiết thang máy.
   - Danh sách linh kiện theo thang máy.
   - Tuổi thọ còn lại.

3. **Ontology Map**
   - Hiển thị chuỗi liên kết:

   ```text
   Asset -> Component -> Rule -> Inventory -> Purchase Request -> Approver
   ```

4. **Rule Management**
   - Danh sách rule.
   - Tạo/sửa rule ở trạng thái draft.
   - Gửi xác nhận nghiệp vụ.
   - Approve/archive rule.

5. **Agent Runs**
   - Lịch sử các lần agent chạy.
   - Rule nào kích hoạt.
   - Dữ liệu đầu vào.
   - Hành động được tạo.

6. **Task Management**
   - Task kiểm tra cáp kéo.
   - Người phụ trách.
   - Bằng chứng cần nhập.
   - Kết quả kiểm tra.

7. **Purchase Requests**
   - Đề xuất mua hàng.
   - Lý do tạo.
   - Tồn kho.
   - Lead time.
   - Người phê duyệt.

8. **Chat / Ask Ontology**
   - Người dùng hỏi bằng tiếng Việt.
   - Hệ thống trả lời có căn cứ.
   - Hiển thị rule/source/manual liên quan.

### 5.2. Backend API

Backend chia thành các service nội bộ:

```text
AssetService
ComponentService
ManualService
RuleService
ReasoningService
InventoryService
PurchaseService
ApprovalService
ChatService
AuditService
NotificationService
OrgRoutingService
```

### 5.3. Ontology Service

Ontology Service chịu trách nhiệm trả lời các câu hỏi dạng quan hệ:

- Thang máy này có linh kiện nào?
- Linh kiện này thuộc loại nào?
- Linh kiện này áp dụng rule nào?
- Rule này tạo hành động gì?
- Phụ tùng nào dùng để thay linh kiện này?
- Phụ tùng này tồn kho bao nhiêu?
- Yêu cầu mua hàng này cần ai phê duyệt?
- Asset này thuộc bộ phận nào?
- Khi có sự cố thì cần báo cho ai trước?
- Nếu chưa xử lý thì cần escalate lên ai?

Trong MVP, Ontology Service query Neo4j bằng Cypher. PostgreSQL vẫn là nơi lưu dữ liệu giao dịch, còn Neo4j là nơi biểu diễn quan hệ Ontology.

Graph model MVP:

```text
(:Asset)-[:HAS_COMPONENT]->(:Component)
(:Component)-[:HAS_TYPE]->(:ComponentType)
(:Component)-[:APPLIES_RULE]->(:Rule)
(:Rule)-[:BASED_ON]->(:Manual)
(:Asset)-[:OWNED_BY]->(:Department)
(:Asset)-[:PRIMARY_CONTACT]->(:User)
(:Asset)-[:BACKUP_CONTACT]->(:User)
(:User)-[:BELONGS_TO]->(:Department)
(:User)-[:HAS_ROLE]->(:Role)
(:User)-[:REPORTS_TO]->(:User)
(:Component)-[:REQUIRES_SPARE_PART]->(:SparePart)
(:SparePart)-[:STORED_AS]->(:InventoryItem)
(:InventoryItem)-[:TRIGGERS_PURCHASE]->(:PurchaseRequest)
(:Rule)-[:USES_ESCALATION_POLICY]->(:EscalationPolicy)
(:Rule)-[:NOTIFIES_GROUP]->(:NotificationGroup)
(:EscalationPolicy)-[:LEVEL_1_CONTACT]->(:User)
(:EscalationPolicy)-[:LEVEL_2_CONTACT]->(:User)
(:EscalationPolicy)-[:FINAL_ESCALATION]->(:User)
(:NotificationGroup)-[:HAS_MEMBER]->(:User)
(:PurchaseRequest)-[:REQUIRES_APPROVAL]->(:ApprovalPolicy)
(:ApprovalPolicy)-[:FINAL_APPROVER]->(:User)
```

Ví dụ truy vấn Ontology cho một thang máy:

```cypher
MATCH (a:Asset {code: $asset_code})-[:HAS_COMPONENT]->(c:Component)
OPTIONAL MATCH (c)-[:APPLIES_RULE]->(r:Rule)
OPTIONAL MATCH (r)-[:BASED_ON]->(m:Manual)
OPTIONAL MATCH (a)-[:OWNED_BY]->(d:Department)
OPTIONAL MATCH (a)-[:PRIMARY_CONTACT]->(pc:User)
OPTIONAL MATCH (a)-[:BACKUP_CONTACT]->(bc:User)
OPTIONAL MATCH (c)-[:REQUIRES_SPARE_PART]->(sp:SparePart)-[:STORED_AS]->(inv:InventoryItem)
OPTIONAL MATCH (r)-[:USES_ESCALATION_POLICY]->(ep:EscalationPolicy)
OPTIONAL MATCH (r)-[:NOTIFIES_GROUP]->(ng:NotificationGroup)
OPTIONAL MATCH (pr:PurchaseRequest)-[:FOR_COMPONENT]->(c)
OPTIONAL MATCH (pr)-[:REQUIRES_APPROVAL]->(ap:ApprovalPolicy)-[:FINAL_APPROVER]->(u:User)
RETURN a, c, r, m, d, pc, bc, sp, inv, ep, ng, pr, ap, u
```

Ontology tổ chức cần phân biệt rõ:

- `ApprovalPolicy`: ai có quyền phê duyệt hành động chính thức.
- `EscalationPolicy`: khi cảnh báo chưa được acknowledge hoặc vượt SLA thì báo lên ai.
- `NotificationGroup`: nhóm người nhận thông báo theo domain hoặc severity.
- `PRIMARY_CONTACT` / `BACKUP_CONTACT`: người xử lý đầu tiên và người dự phòng cho từng asset hoặc component quan trọng.

### 5.4. Rule Engine

Rule Engine chạy rule đã approved trên dữ liệu hiện tại.

Rule đầu tiên:

```yaml
rule_id: R-ELV-CABLE-001
condition:
  component_type: cable
  remaining_lifetime_months_lte: 6
actions:
  - create_technical_alert
  - create_inspection_task
  - check_spare_part_inventory
  - evaluate_purchase_need
  - identify_approval_flow
```

Rule Engine phải đảm bảo:

- Chỉ chạy rule `approved`.
- Đọc quan hệ Ontology từ Neo4j.
- Đọc dữ liệu giao dịch/tuổi thọ/tồn kho từ PostgreSQL khi đó là source of record.
- Không để LLM tự sửa condition.
- Lưu lại input/output của mỗi lần chạy.
- Không tạo trùng task nếu task tương tự đang mở.
- Mọi hành động đều có audit log.

### 5.5. RAG Service

RAG Service xử lý manual:

1. Nhận file manual.
2. Lưu file gốc vào MinIO.
3. Parse text từ PDF/DOCX/ảnh scan.
4. Chia chunk.
5. Tạo embedding.
6. Lưu chunk + embedding vào PostgreSQL/pgvector.
7. Khi người dùng hỏi, tìm chunk liên quan.
8. Trả chunk cho LLM để diễn giải có căn cứ.

RAG không được dùng để thay rule engine. RAG chỉ cung cấp nguồn căn cứ.

### 5.6. Chat Service

Chat Service xử lý câu hỏi tiếng Việt.

Luồng:

```text
User question
  -> classify intent
  -> retrieve related data/rules/manual chunks
  -> call LLM with constrained context
  -> return answer + citations + missing data
```

Các intent MVP:

- `asset_risk_query`: hỏi thang máy nào có rủi ro.
- `rule_explanation`: hỏi vì sao rule kích hoạt.
- `purchase_reason`: hỏi vì sao cần mua phụ tùng.
- `approval_query`: hỏi ai phê duyệt.
- `manual_source_query`: hỏi căn cứ từ manual.
- `out_of_scope`: ngoài phạm vi dữ liệu.

### 5.7. Agent Worker

Agent Worker chạy theo lịch hoặc khi có thay đổi dữ liệu.

Trigger MVP:

- Chạy thủ công từ UI.
- Chạy định kỳ mỗi ngày lúc 07:00.
- Chạy khi cập nhật tuổi thọ linh kiện/tồn kho.

Agent Worker làm:

1. Lấy danh sách linh kiện cần theo dõi.
2. Lấy quan hệ Ontology từ Neo4j.
3. Chạy rule engine.
4. Đồng bộ node/relationship mới sang Neo4j nếu tạo task hoặc purchase request.
5. Tạo cảnh báo nếu có rule kích hoạt.
6. Tạo task kiểm tra nếu chưa tồn tại.
7. Kiểm tra tồn kho.
8. Tạo đề xuất mua hàng nếu điều kiện đúng.
9. Xác định approval flow.
10. Xác định người nhận thông báo đầu tiên, backup contact và escalation path.
11. Gửi notification qua n8n nếu cần.
12. Lưu agent run và audit log.

### 5.8. Neo4j Sync Service

Neo4j Sync Service đảm bảo graph Ontology bám sát dữ liệu nghiệp vụ.

Nguyên tắc:

- PostgreSQL là source of record cho dữ liệu giao dịch.
- Neo4j là source of truth cho quan hệ Ontology.
- Mỗi entity quan trọng trong PostgreSQL có `code` ổn định để map sang node Neo4j.
- Khi tạo/sửa asset, component, inventory item, rule, purchase request, backend cập nhật Neo4j trong cùng workflow.
- Nếu sync lỗi, ghi audit/error log và cho phép chạy lại sync.

Các thao tác sync MVP:

```text
upsert_asset_node
upsert_component_node
upsert_rule_node
upsert_manual_node
upsert_spare_part_node
upsert_inventory_node
upsert_purchase_request_node
upsert_approval_policy_node
upsert_user_node
upsert_department_node
upsert_role_node
upsert_escalation_policy_node
upsert_notification_group_node
merge_relationships
```

## 6. Database design

### 6.1. PostgreSQL entity relationship

```text
users
  └── approvals

departments
  └── users

notification_groups
  └── notification_group_members

escalation_policies

assets
  └── components
        ├── inspection_tasks
        ├── inventory_items
        └── purchase_requests

manuals
  └── manual_chunks

rules
  ├── rule_versions
  ├── inspection_tasks
  └── purchase_requests

agent_runs
  └── agent_run_events

audit_logs
```

### 6.2. Neo4j graph schema

Node labels:

```text
Asset
Component
ComponentType
Rule
Manual
SparePart
InventoryItem
InspectionTask
PurchaseRequest
ApprovalPolicy
User
Department
Role
EscalationPolicy
NotificationGroup
```

Relationship types:

```text
(Asset)-[:HAS_COMPONENT]->(Component)
(Asset)-[:OWNED_BY]->(Department)
(Asset)-[:PRIMARY_CONTACT]->(User)
(Asset)-[:BACKUP_CONTACT]->(User)
(Component)-[:HAS_TYPE]->(ComponentType)
(Component)-[:APPLIES_RULE]->(Rule)
(Rule)-[:BASED_ON]->(Manual)
(User)-[:BELONGS_TO]->(Department)
(User)-[:HAS_ROLE]->(Role)
(User)-[:REPORTS_TO]->(User)
(Rule)-[:USES_ESCALATION_POLICY]->(EscalationPolicy)
(Rule)-[:NOTIFIES_GROUP]->(NotificationGroup)
(EscalationPolicy)-[:LEVEL_1_CONTACT]->(User)
(EscalationPolicy)-[:LEVEL_2_CONTACT]->(User)
(EscalationPolicy)-[:FINAL_ESCALATION]->(User)
(NotificationGroup)-[:HAS_MEMBER]->(User)
(Component)-[:REQUIRES_SPARE_PART]->(SparePart)
(SparePart)-[:STORED_AS]->(InventoryItem)
(Component)-[:HAS_INSPECTION_TASK]->(InspectionTask)
(PurchaseRequest)-[:FOR_COMPONENT]->(Component)
(PurchaseRequest)-[:FOR_SPARE_PART]->(SparePart)
(PurchaseRequest)-[:REQUIRES_APPROVAL]->(ApprovalPolicy)
(ApprovalPolicy)-[:FINAL_APPROVER]->(User)
```

Neo4j constraints/indexes MVP:

```cypher
CREATE CONSTRAINT asset_code IF NOT EXISTS FOR (n:Asset) REQUIRE n.code IS UNIQUE;
CREATE CONSTRAINT component_code IF NOT EXISTS FOR (n:Component) REQUIRE n.code IS UNIQUE;
CREATE CONSTRAINT rule_code IF NOT EXISTS FOR (n:Rule) REQUIRE n.code IS UNIQUE;
CREATE CONSTRAINT manual_code IF NOT EXISTS FOR (n:Manual) REQUIRE n.code IS UNIQUE;
CREATE CONSTRAINT spare_part_code IF NOT EXISTS FOR (n:SparePart) REQUIRE n.code IS UNIQUE;
CREATE CONSTRAINT inventory_code IF NOT EXISTS FOR (n:InventoryItem) REQUIRE n.code IS UNIQUE;
CREATE CONSTRAINT purchase_request_id IF NOT EXISTS FOR (n:PurchaseRequest) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT user_id IF NOT EXISTS FOR (n:User) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT department_code IF NOT EXISTS FOR (n:Department) REQUIRE n.code IS UNIQUE;
CREATE CONSTRAINT role_code IF NOT EXISTS FOR (n:Role) REQUIRE n.code IS UNIQUE;
CREATE CONSTRAINT escalation_policy_code IF NOT EXISTS FOR (n:EscalationPolicy) REQUIRE n.code IS UNIQUE;
CREATE CONSTRAINT notification_group_code IF NOT EXISTS FOR (n:NotificationGroup) REQUIRE n.code IS UNIQUE;
```

Ví dụ seed graph từ dữ liệu giả lập:

```cypher
MERGE (a:Asset {code: "ELV-CALIDAS-01"})
SET a.name = "Thang máy Calidas 1", a.location = "Sảnh khách sạn - trục A";

MERGE (c:Component {code: "CMP-CABLE-001"})
SET c.name = "Cáp kéo Calidas 1", c.component_type = "cable", c.remaining_lifetime_months = 5;

MERGE (r:Rule {code: "R-ELV-CABLE-001"})
SET r.name = "Cảnh báo cáp kéo thang máy còn dưới hoặc bằng 6 tháng tuổi thọ", r.status = "approved";

MERGE (sp:SparePart {code: "SP-CABLE-CALIDAS"})
SET sp.name = "Bộ cáp kéo Calidas";

MERGE (inv:InventoryItem {code: "SP-CABLE-CALIDAS"})
SET inv.quantity_on_hand = 0, inv.lead_time_months = 7;

MERGE (u:User {id: "CEO"})
SET u.name = "CEO";

MERGE (d:Department {code: "TECH"})
SET d.name = "Bộ phận kỹ thuật";

MERGE (mgr:User {id: "TECH-MANAGER"})
SET mgr.name = "Trưởng bộ phận kỹ thuật";

MERGE (tech:User {id: "TECH-01"})
SET tech.name = "Kỹ thuật viên trực";

MERGE (ep:EscalationPolicy {code: "ELV-CRITICAL-01"})
SET ep.name = "Escalation cho sự cố thang máy critical";

MERGE (ng:NotificationGroup {code: "TECH-OPS"})
SET ng.name = "Nhóm kỹ thuật vận hành";

MERGE (a)-[:HAS_COMPONENT]->(c)
MERGE (a)-[:OWNED_BY]->(d)
MERGE (a)-[:PRIMARY_CONTACT]->(tech)
MERGE (a)-[:BACKUP_CONTACT]->(mgr)
MERGE (c)-[:APPLIES_RULE]->(r)
MERGE (r)-[:USES_ESCALATION_POLICY]->(ep)
MERGE (r)-[:NOTIFIES_GROUP]->(ng)
MERGE (c)-[:REQUIRES_SPARE_PART]->(sp)
MERGE (sp)-[:STORED_AS]->(inv)
MERGE (tech)-[:BELONGS_TO]->(d)
MERGE (mgr)-[:BELONGS_TO]->(d)
MERGE (tech)-[:REPORTS_TO]->(mgr)
MERGE (ep)-[:LEVEL_1_CONTACT]->(tech)
MERGE (ep)-[:LEVEL_2_CONTACT]->(mgr)
MERGE (ep)-[:FINAL_ESCALATION]->(u)
MERGE (ng)-[:HAS_MEMBER]->(tech)
MERGE (ng)-[:HAS_MEMBER]->(mgr);
```

### 6.3. Bảng `assets`

```sql
CREATE TABLE assets (
  id UUID PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  asset_type TEXT NOT NULL,
  location TEXT,
  department_owner TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.3a. Bảng tổ chức và routing

```sql
CREATE TABLE departments (
  id UUID PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  parent_department_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
  id UUID PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  full_name TEXT NOT NULL,
  department_id UUID REFERENCES departments(id),
  role_code TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  manager_user_id UUID,
  is_on_call BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE escalation_policies (
  id UUID PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  level_1_user_id UUID REFERENCES users(id),
  level_2_user_id UUID REFERENCES users(id),
  final_escalation_user_id UUID REFERENCES users(id),
  acknowledge_sla_minutes INT,
  resolve_sla_minutes INT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE notification_groups (
  id UUID PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  channel_type TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.4. Bảng `components`

```sql
CREATE TABLE components (
  id UUID PRIMARY KEY,
  asset_id UUID NOT NULL REFERENCES assets(id),
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  component_type TEXT NOT NULL,
  installed_at DATE,
  expected_lifetime_months INT,
  remaining_lifetime_months INT,
  last_inspection_at DATE,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.5. Bảng `inventory_items`

```sql
CREATE TABLE inventory_items (
  id UUID PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  component_type TEXT NOT NULL,
  quantity_on_hand INT NOT NULL DEFAULT 0,
  minimum_quantity INT NOT NULL DEFAULT 0,
  lead_time_months INT,
  supplier_name TEXT,
  import_required BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.6. Bảng `manuals`

```sql
CREATE TABLE manuals (
  id UUID PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  department_owner TEXT,
  file_object_key TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_type TEXT,
  version TEXT,
  status TEXT NOT NULL DEFAULT 'uploaded',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.7. Bảng `manual_chunks`

```sql
CREATE TABLE manual_chunks (
  id UUID PRIMARY KEY,
  manual_id UUID NOT NULL REFERENCES manuals(id),
  chunk_index INT NOT NULL,
  heading TEXT,
  page_number INT,
  chunk_text TEXT NOT NULL,
  embedding VECTOR(1536),
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.8. Bảng `rules`

```sql
CREATE TABLE rules (
  id UUID PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  domain TEXT NOT NULL,
  condition_json JSONB NOT NULL,
  action_json JSONB NOT NULL,
  evidence_required_json JSONB NOT NULL DEFAULT '[]',
  source_manual_id UUID REFERENCES manuals(id),
  owner_department TEXT,
  owner_user_id UUID,
  escalation_policy_id UUID,
  status TEXT NOT NULL DEFAULT 'draft',
  version INT NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Trạng thái rule:

```text
draft
validated
approved
archived
```

### 6.9. Bảng `inspection_tasks`

```sql
CREATE TABLE inspection_tasks (
  id UUID PRIMARY KEY,
  asset_id UUID NOT NULL REFERENCES assets(id),
  component_id UUID NOT NULL REFERENCES components(id),
  rule_id UUID REFERENCES rules(id),
  title TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'open',
  assigned_to UUID,
  due_date DATE,
  evidence_required_json JSONB NOT NULL DEFAULT '[]',
  evidence_result_json JSONB NOT NULL DEFAULT '{}',
  created_by_agent BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.10. Bảng `purchase_requests`

```sql
CREATE TABLE purchase_requests (
  id UUID PRIMARY KEY,
  component_id UUID NOT NULL REFERENCES components(id),
  inventory_item_id UUID NOT NULL REFERENCES inventory_items(id),
  rule_id UUID REFERENCES rules(id),
  reason TEXT NOT NULL,
  quantity_requested INT NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'draft',
  approval_policy_id UUID,
  final_approver_id UUID,
  created_by_agent BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Trạng thái purchase request:

```text
draft
waiting_for_approval
approved
rejected
cancelled
```

### 6.11. Bảng `agent_runs`

```sql
CREATE TABLE agent_runs (
  id UUID PRIMARY KEY,
  run_type TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  input_snapshot JSONB NOT NULL DEFAULT '{}',
  output_summary JSONB NOT NULL DEFAULT '{}',
  error_message TEXT
);
```

### 6.12. Bảng `audit_logs`

```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY,
  actor_type TEXT NOT NULL,
  actor_id UUID,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id UUID,
  before_json JSONB,
  after_json JSONB,
  reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 7. API design

### 7.1. Assets

```text
GET    /api/assets
POST   /api/assets
GET    /api/assets/{asset_id}
PATCH  /api/assets/{asset_id}
GET    /api/assets/{asset_id}/components
GET    /api/assets/{asset_id}/ontology
```

### 7.2. Components

```text
GET    /api/components
POST   /api/components
GET    /api/components/{component_id}
PATCH  /api/components/{component_id}
```

### 7.3. Inventory

```text
GET    /api/inventory-items
POST   /api/inventory-items
PATCH  /api/inventory-items/{item_id}
```

### 7.4. Manuals

```text
POST   /api/manuals/upload
GET    /api/manuals
GET    /api/manuals/{manual_id}
POST   /api/manuals/{manual_id}/parse
GET    /api/manuals/{manual_id}/chunks
```

### 7.5. Rules

```text
GET    /api/rules
POST   /api/rules
GET    /api/rules/{rule_id}
PATCH  /api/rules/{rule_id}
POST   /api/rules/{rule_id}/validate
POST   /api/rules/{rule_id}/approve
POST   /api/rules/{rule_id}/archive
```

### 7.6. Reasoning / Agent

```text
POST   /api/reasoning/run
GET    /api/agent-runs
GET    /api/agent-runs/{run_id}
GET    /api/agent-runs/{run_id}/events
```

### 7.7. Tasks

```text
GET    /api/inspection-tasks
GET    /api/inspection-tasks/{task_id}
PATCH  /api/inspection-tasks/{task_id}
POST   /api/inspection-tasks/{task_id}/complete
POST   /api/inspection-tasks/{task_id}/cancel
```

### 7.8. Purchase requests

```text
GET    /api/purchase-requests
GET    /api/purchase-requests/{request_id}
POST   /api/purchase-requests/{request_id}/submit
POST   /api/purchase-requests/{request_id}/approve
POST   /api/purchase-requests/{request_id}/reject
```

### 7.9. Chat

```text
POST   /api/chat/query
```

### 7.10. Organization / Notification Routing

```text
GET    /api/departments
GET    /api/users
GET    /api/assets/{asset_id}/contacts
GET    /api/rules/{rule_id}/notification-targets
GET    /api/escalation-policies/{policy_id}
```

Request:

```json
{
  "question": "Có thang máy nào sắp cần kiểm tra hoặc thay linh kiện không?",
  "context": {
    "department": "Kỹ thuật"
  }
}
```

Response:

```json
{
  "answer": "Có. Thang máy Calidas 1 có cáp kéo còn 5 tháng tuổi thọ...",
  "intent": "asset_risk_query",
  "citations": [
    {
      "type": "rule",
      "code": "R-ELV-CABLE-001",
      "title": "Cảnh báo cáp kéo thang máy còn dưới hoặc bằng 6 tháng tuổi thọ"
    },
    {
      "type": "manual",
      "code": "MAN-ELV-001",
      "title": "Manual bảo trì thang máy Calidas"
    }
  ],
  "missing_data": [],
  "actions": [
    "create_inspection_task",
    "evaluate_purchase_need"
  ]
}
```

## 8. Rule Engine design

### 8.1. Input

Rule Engine nhận:

- Danh sách components.
- Danh sách inventory items.
- Rules đã approved.
- Approval policies.
- Graph context từ Neo4j: asset -> component -> rule -> spare part -> inventory -> approval.
- Existing open tasks/purchase requests để tránh tạo trùng.

### 8.2. Output

Rule Engine trả:

```json
{
  "triggered_rules": [
    {
      "rule_code": "R-ELV-CABLE-001",
      "asset_code": "ELV-CALIDAS-01",
      "component_code": "CMP-CABLE-001",
      "reason": "Cáp kéo còn 5 tháng tuổi thọ, nhỏ hơn hoặc bằng ngưỡng 6 tháng.",
      "actions": [
        "create_technical_alert",
        "create_inspection_task",
        "check_spare_part_inventory",
        "create_purchase_request"
      ]
    }
  ]
}
```

### 8.3. Pseudocode

```python
def run_reasoning():
    approved_rules = rule_repo.list_approved()
    components = component_repo.list_active()

    for component in components:
        graph_context = ontology_repo.get_component_context(component.code)
        for rule in approved_rules:
            if rule.applies_to(component, graph_context) and rule.condition_matches(component):
                finding = create_finding(component, rule, graph_context)
                create_inspection_task_if_needed(finding)
                inventory_result = check_inventory(component)

                if should_create_purchase_request(component, inventory_result):
                    purchase_request = create_purchase_request_if_needed(finding, inventory_result)
                    ontology_sync.upsert_purchase_request(purchase_request)

                write_audit_log(finding)
```

### 8.4. Chống tạo trùng

Trước khi tạo task hoặc purchase request, hệ thống phải kiểm tra:

- Có task đang mở cho cùng `component_id` và `rule_id` không?
- Có purchase request đang chờ duyệt cho cùng `component_id` và `inventory_item_id` không?

Nếu đã có, agent chỉ cập nhật audit log, không tạo bản ghi mới.

## 9. Chat/RAG design

### 9.1. Phân loại intent

Chat Service phân loại câu hỏi thành intent:

```text
asset_risk_query
rule_explanation
purchase_reason
approval_query
manual_source_query
out_of_scope
```

### 9.2. Tool/API mà LLM được gọi

LLM chỉ được gọi các tool có schema rõ:

```text
get_asset_risks()
get_asset_ontology(asset_code)
get_rule(rule_code)
search_manual_chunks(query)
get_purchase_request_reason(request_id)
get_approval_policy(request_type)
```

### 9.3. Prompt guardrail

System prompt cần ép nguyên tắc:

```text
Bạn là lớp giao diện diễn giải cho hệ thống Ontology.
Bạn chỉ được trả lời dựa trên dữ liệu từ tools/context.
Không tự tạo rule, không tự tạo số liệu, không tự quyết định mua hàng.
Nếu thiếu dữ liệu, trả lời rõ "không đủ dữ liệu" và nêu dữ liệu cần bổ sung.
Mỗi kết luận quan trọng phải có căn cứ từ rule, manual hoặc dữ liệu nghiệp vụ.
```

### 9.4. Response format

LLM nên trả JSON có cấu trúc:

```json
{
  "conclusion": "",
  "evidence": [],
  "recommended_actions": [],
  "missing_data": [],
  "citations": []
}
```

Frontend có thể render JSON này thành câu trả lời tiếng Việt.

## 10. Agent workflow design

### 10.1. State machine

```text
scheduled
  -> loading_data
  -> evaluating_rules
  -> creating_alerts
  -> creating_tasks
  -> checking_inventory
  -> creating_purchase_requests
  -> notifying_users
  -> completed
```

Nếu lỗi:

```text
failed
  -> retry
  -> completed hoặc failed_final
```

### 10.2. Workflow MVP

```text
1. User bấm "Chạy suy luận" hoặc job chạy hằng ngày.
2. Backend tạo agent_run.
3. Backend load components active.
4. Rule Engine chạy R-ELV-CABLE-001.
5. Nếu Calidas 1 còn 5 tháng:
   - Tạo alert.
   - Tạo inspection task.
   - Kiểm tra SP-CABLE-CALIDAS.
   - Tồn kho = 0, lead time = 7 tháng.
   - Tạo purchase request draft.
   - Xác định final approver = CEO.
6. Gửi thông báo qua n8n/email nếu cấu hình.
7. Lưu audit log.
8. Trả kết quả lên UI.
```

## 11. Phân quyền

### 11.1. Roles

```text
admin
ai_team
technical_manager
technician
on_call
warehouse_staff
purchase_staff
approver
viewer
```

### 11.2. Permission matrix MVP

| Chức năng | Admin | AI Team | Trưởng kỹ thuật | Kỹ thuật viên | On-call | Kho | Mua hàng | Approver | Viewer |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Xem dashboard | Có | Có | Có | Có | Có | Có | Có | Có | Có |
| Quản lý tài sản | Có | Có | Có | Không | Không | Không | Không | Không | Xem |
| Upload manual | Có | Có | Có | Không | Không | Không | Không | Không | Không |
| Tạo rule draft | Có | Có | Có | Không | Không | Không | Không | Không | Không |
| Approve rule | Có | Không | Có | Không | Không | Không | Không | Không | Không |
| Chạy reasoning | Có | Có | Có | Không | Không | Không | Không | Không | Không |
| Hoàn thành task | Có | Không | Có | Có | Có | Không | Không | Không | Không |
| Nhận escalation ngoài giờ | Có | Không | Có | Không | Có | Không | Không | Không | Không |
| Cập nhật tồn kho | Có | Không | Không | Không | Không | Có | Không | Không | Không |
| Xử lý mua hàng | Có | Không | Không | Không | Không | Không | Có | Không | Không |
| Phê duyệt mua hàng | Có | Không | Không | Không | Không | Không | Không | Có | Không |

## 12. Audit và truy vết

Mỗi kết luận hoặc hành động của hệ thống phải truy vết được:

- Dữ liệu đầu vào.
- Rule được chạy.
- Manual/quy trình liên quan.
- Agent run ID.
- Người tạo/phê duyệt.
- Thời điểm tạo.
- Trạng thái trước/sau.

Ví dụ audit log:

```json
{
  "actor_type": "agent",
  "action": "create_purchase_request",
  "entity_type": "purchase_request",
  "reason": "CMP-CABLE-001 còn 5 tháng, tồn kho SP-CABLE-CALIDAS = 0, lead time = 7 tháng",
  "source_rule": "R-ELV-CABLE-001"
}
```

## 13. Docker Compose MVP

Các service cần có:

```text
frontend
backend
postgres
neo4j
minio
worker
n8n
```

Có thể thêm sau:

```text
redis
prometheus
grafana
```

MVP ban đầu có thể dùng APScheduler trong backend thay vì Celery/Redis để giảm phức tạp.
Neo4j cần được đưa vào Docker Compose ngay từ đầu để đội AI thiết kế và kiểm thử Ontology bằng graph thật, không chỉ mô phỏng bằng bảng SQL.

## 14. Cấu trúc repo đề xuất

```text
twinai-agentic-mvp/
  apps/
    web/
      app/
      components/
      lib/
      package.json
    api/
      app/
        main.py
        api/
        core/
        models/
        schemas/
        services/
        workers/
        tests/
      pyproject.toml
  infra/
    docker-compose.yml
    postgres/
      init.sql
    neo4j/
      constraints.cypher
      seed.cypher
    minio/
  docs/
    architecture.md
    ontology.md
    api.md
    deployment.md
```

## 15. Sprint triển khai đề xuất

### Sprint 1: Data + Rule Engine

Mục tiêu:

- Có database schema.
- Có seed data từ file 07.
- Có API `POST /api/reasoning/run`.
- Chạy được rule `R-ELV-CABLE-001`.
- Tạo được task và purchase request draft.

Deliverables:

- FastAPI backend.
- PostgreSQL schema.
- Seed data.
- Unit test cho rule engine.

### Sprint 2: Dashboard + Ontology Map

Mục tiêu:

- Có UI dashboard.
- Có bảng thang máy/linh kiện.
- Có màn hình agent run.
- Có ontology map cho Calidas 1.

Deliverables:

- Next.js frontend.
- Dashboard MVP.
- API integration.

### Sprint 3: Manual + RAG

Mục tiêu:

- Upload manual.
- Parse/chunk manual.
- Tạo embedding.
- Tìm manual chunk liên quan.
- Chat trả lời có citations.

Deliverables:

- Manual upload.
- pgvector search.
- Chat endpoint.

### Sprint 4: Approval + Notification

Mục tiêu:

- Submit purchase request.
- Approve/reject purchase request.
- Gửi notification qua n8n.
- Audit log đầy đủ.

Deliverables:

- Approval UI.
- n8n webhook.
- Audit log viewer.

## 16. Tiêu chí nghiệm thu MVP

MVP đạt nếu demo được kịch bản sau:

1. Người dùng mở dashboard.
2. Hệ thống hiển thị Calidas 1 có cáp kéo còn 5 tháng.
3. Người dùng bấm "Chạy suy luận".
4. Hệ thống kích hoạt rule `R-ELV-CABLE-001`.
5. Hệ thống tạo task kiểm tra.
6. Hệ thống kiểm tra tồn kho cáp Calidas = 0.
7. Hệ thống tạo purchase request draft.
8. Hệ thống xác định người phê duyệt cuối là CEO.
9. Người dùng hỏi:

```text
Có thang máy nào sắp cần kiểm tra hoặc thay linh kiện không?
```

10. Chat trả lời có:

- Kết luận.
- Căn cứ từ rule.
- Căn cứ từ manual.
- Dữ liệu tồn kho.
- Hành động đề xuất.
- Người phê duyệt.
- Dữ liệu còn thiếu nếu có.

## 17. Rủi ro thiết kế và cách giảm thiểu

| Rủi ro | Cách giảm thiểu |
|---|---|
| LLM trả lời sai hoặc suy đoán | Bắt buộc dùng tool/context, trả JSON có citations, nếu thiếu dữ liệu thì nói không đủ dữ liệu |
| Rule sai nghiệp vụ | Rule phải có owner và trạng thái approved |
| Tạo trùng task/purchase request | Kiểm tra bản ghi đang mở trước khi tạo |
| Manual không đúng thực tế | Gắn manual với người xác nhận nghiệp vụ |
| Dữ liệu tồn kho sai | Lưu nguồn dữ liệu và thời điểm đồng bộ |
| Agent tự động hóa quá mức | MVP chỉ tạo đề xuất, mọi hành động thật cần phê duyệt |

## 18. Kết luận thiết kế

Thiết kế MVP nên đi theo hướng:

```text
PostgreSQL là lõi dữ liệu giao dịch và audit
Neo4j là lõi Ontology graph
Rule Engine là lõi quyết định
LLM là lớp giao diện
Agent Worker là lớp hành động
Human approval là chốt kiểm soát
Audit log là lớp truy vết
```

Với cách này, hệ thống bám sát yêu cầu của Chairman: không xây một chatbot đơn thuần, không xây ERP mới, mà xây một lớp Ontology có khả năng kết nối dữ liệu, suy luận có căn cứ và tạo hành động vận hành.
