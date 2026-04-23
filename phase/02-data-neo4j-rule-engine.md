# Phase 02: Data + Neo4j + Rule Engine

## Mục tiêu

Xây lõi hệ thống: dữ liệu, Ontology graph trong Neo4j, Rule Engine và API reasoning.

Đây là phase quan trọng nhất của MVP.

## Phạm vi

Tập trung vào use case:

```text
Thang máy Calidas 1 -> Cáp kéo còn 5 tháng -> Rule R-ELV-CABLE-001 -> Task kiểm tra -> Purchase request draft
```

## Dữ liệu đầu vào

Dùng dữ liệu giả lập từ:

```text
phan-tich-bien-ban-17-04-2026/07-gia-lap-khoi-dong-mvp-thang-may.md
```

Bao gồm:

- `ELV-CALIDAS-01`
- `ELV-CALIDAS-02`
- `ELV-SERVICE-01`
- `CMP-CABLE-001`
- `SP-CABLE-CALIDAS`
- `R-ELV-CABLE-001`

## PostgreSQL schema cần có

Bảng cần tạo:

```text
assets
components
inventory_items
manuals
rules
inspection_tasks
purchase_requests
agent_runs
audit_logs
```

PostgreSQL giữ:

- Dữ liệu nghiệp vụ.
- Task.
- Purchase request.
- Audit log.
- Agent run.

## Neo4j graph cần có

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
```

Relationship types:

```text
(Asset)-[:HAS_COMPONENT]->(Component)
(Component)-[:APPLIES_RULE]->(Rule)
(Rule)-[:BASED_ON]->(Manual)
(Component)-[:REQUIRES_SPARE_PART]->(SparePart)
(SparePart)-[:STORED_AS]->(InventoryItem)
(PurchaseRequest)-[:FOR_COMPONENT]->(Component)
(PurchaseRequest)-[:REQUIRES_APPROVAL]->(ApprovalPolicy)
(ApprovalPolicy)-[:FINAL_APPROVER]->(User)
```

## Rule đầu tiên

```yaml
rule_id: R-ELV-CABLE-001
name: Cảnh báo cáp kéo thang máy còn dưới hoặc bằng 6 tháng tuổi thọ
condition:
  component_type: cable
  remaining_lifetime_months_lte: 6
actions:
  - create_technical_alert
  - create_inspection_task
  - check_spare_part_inventory
  - evaluate_purchase_need
  - identify_approval_flow
status: approved
```

## API cần build

```text
POST /api/reasoning/run
GET  /api/agent-runs
GET  /api/agent-runs/{run_id}
GET  /api/assets
GET  /api/assets/{asset_id}/ontology
GET  /api/inspection-tasks
GET  /api/purchase-requests
```

## Rule Engine logic

Luồng xử lý:

```text
1. Load active components từ PostgreSQL.
2. Với mỗi component, lấy graph context từ Neo4j.
3. Load approved rules.
4. Kiểm tra condition.
5. Nếu component là cable và remaining_lifetime_months <= 6:
   - tạo agent finding.
   - tạo inspection task nếu chưa có task đang mở.
   - kiểm tra inventory.
   - nếu tồn kho = 0 và lead time > remaining lifetime:
     tạo purchase request draft.
   - xác định approval flow.
   - đồng bộ task/purchase request sang Neo4j.
   - ghi audit log.
```

## Neo4j Sync Service

Service này cần có các hàm:

```text
upsert_asset_node
upsert_component_node
upsert_rule_node
upsert_manual_node
upsert_spare_part_node
upsert_inventory_node
upsert_purchase_request_node
merge_relationships
```

## Deliverables

- PostgreSQL migrations.
- Seed data từ tài liệu 07.
- Neo4j constraints.
- Neo4j seed graph.
- Rule Engine chạy được `R-ELV-CABLE-001`.
- API `POST /api/reasoning/run`.
- Tự tạo task kiểm tra.
- Tự tạo purchase request draft.
- Audit log cho agent run.
- Unit test cho rule engine.

## Tiêu chí hoàn thành

Phase 02 đạt khi gọi:

```text
POST /api/reasoning/run
```

Và hệ thống tạo được:

- 1 finding cho `ELV-CALIDAS-01`.
- 1 inspection task cho `CMP-CABLE-001`.
- 1 purchase request draft cho `SP-CABLE-CALIDAS`.
- 1 graph relationship purchase request trong Neo4j.
- audit log đầy đủ.

Ghi chú mở rộng:

- `ApprovalPolicy`, `User`, `Department` ở phase này là phần graph tối thiểu cho approval flow.
- `Primary contact`, `backup contact`, `EscalationPolicy`, `NotificationGroup` là phần mở rộng của Phase 05, chưa nên xem là deliverable bắt buộc của Phase 02.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| PostgreSQL và Neo4j lệch dữ liệu | Dùng code/id ổn định và Neo4j Sync Service |
| Tạo trùng task | Kiểm tra task đang mở trước khi tạo |
| Rule sai nghiệp vụ | Rule phải có trạng thái `approved` |
| Neo4j query phức tạp quá sớm | Chỉ dùng graph cho chuỗi Ontology MVP |

