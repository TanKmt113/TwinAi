# Ontology Phase 1

Phase 1 chỉ tạo constraints và seed tối thiểu cho Neo4j.

## Node labels dự kiến

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
Sensor
Metric
SensorAlert
```

## Relationship types dự kiến

```text
(Asset)-[:HAS_COMPONENT]->(Component)
(Component)-[:APPLIES_RULE]->(Rule)
(Rule)-[:BASED_ON]->(Manual)
(Component)-[:REQUIRES_SPARE_PART]->(SparePart)
(SparePart)-[:STORED_AS]->(InventoryItem)
(PurchaseRequest)-[:FOR_COMPONENT]->(Component)
(PurchaseRequest)-[:REQUIRES_APPROVAL]->(ApprovalPolicy)
(ApprovalPolicy)-[:FINAL_APPROVER]->(User)
(Asset)-[:OWNED_BY]->(Department)
(Asset)-[:PRIMARY_CONTACT]->(User)
(Asset)-[:BACKUP_CONTACT]->(User)
(User)-[:BELONGS_TO]->(Department)
(User)-[:HAS_ROLE]->(Role)
(User)-[:REPORTS_TO]->(User)
(Rule)-[:USES_ESCALATION_POLICY]->(EscalationPolicy)
(Rule)-[:NOTIFIES_GROUP]->(NotificationGroup)
(EscalationPolicy)-[:LEVEL_1_CONTACT]->(User)
(EscalationPolicy)-[:LEVEL_2_CONTACT]->(User)
(EscalationPolicy)-[:FINAL_ESCALATION]->(User)
(NotificationGroup)-[:HAS_MEMBER]->(User)
(Asset)-[:HAS_SENSOR]->(Sensor)
(Component)-[:HAS_SENSOR]->(Sensor)
(Sensor)-[:MEASURES]->(Metric)
(Rule)-[:USES_METRIC]->(Metric)
(SensorAlert)-[:TRIGGERED_BY]->(Sensor)
(SensorAlert)-[:AFFECTS_COMPONENT]->(Component)
```

Phase 2 seed graph thật từ use case thang máy khi backend start và Neo4j online.

## Rule MVP

```text
R-ELV-CABLE-001
```

Điều kiện:

```text
component_type = cable
remaining_lifetime_months <= 6
```

Chuỗi graph mục tiêu:

```text
ELV-CALIDAS-01
  -> CMP-CABLE-001
  -> R-ELV-CABLE-001
  -> MAN-ELV-001
  -> SP-CABLE-CALIDAS
  -> InventoryItem quantity_on_hand = 0
```

## Ontology tổ chức và thông báo

MVP không chỉ cần biết "có vấn đề gì" mà còn phải biết "báo cho ai" và "ai chịu trách nhiệm xử lý". Vì vậy Ontology cần thêm một nhánh tổ chức để mô hình hóa chủ sở hữu tài sản, người phụ trách chính, người dự phòng và tuyến escalation.

Chuỗi graph tổ chức mục tiêu:

```text
ELV-CALIDAS-01
  -> Department Kỹ thuật
  -> PRIMARY_CONTACT Technician A
  -> BACKUP_CONTACT Technical Manager
  -> R-ELV-CABLE-001
  -> EscalationPolicy ELV-CRITICAL-01
  -> NotificationGroup TECH-OPS
  -> CEO (nếu approval hoặc escalation mức cuối)
```

Nguyên tắc:

- `ApprovalPolicy` trả lời câu hỏi "ai có quyền phê duyệt".
- `EscalationPolicy` trả lời câu hỏi "khi sự cố xảy ra hoặc quá SLA thì báo ai".
- `NotificationGroup` gom danh sách người nhận thông báo theo domain hoặc severity.
- `PRIMARY_CONTACT` là người xử lý đầu tiên; `BACKUP_CONTACT` là người nhận tiếp khi ngoài giờ hoặc không phản hồi.
- `REPORTS_TO` giúp truy ra tuyến quản lý khi cần escalation theo cơ cấu tổ chức.

## Digital Twin mở rộng

Phase 07-10 thêm sensor và 3D Digital Twin. Neo4j chỉ lưu quan hệ và trạng thái tổng hợp, không lưu từng sensor reading dày đặc.

Chuỗi graph sensor mục tiêu:

```text
ELV-CALIDAS-01
  -> CMP-CABLE-001
  -> SNS-CABLE-VIB-001
  -> Metric vibration
  -> SensorAlert
  -> R-ELV-VIB-001
```

Rule realtime MVP:

```text
R-ELV-VIB-001
```

Điều kiện:

```text
metric = vibration
value > 6.0
window_minutes = 5
min_samples = 3
```

## PostgreSQL: catalog tổ chức (chưa đồng bộ đầy đủ sang Neo4j)

Bảng **`org_units`** (cây `parent_id`, `level_kind`) và **`org_users`** (`org_unit_id`, `manager_user_id`, `role_tags`) lưu cơ cấu nội bộ demo; API `GET /api/org/units`, `GET /api/org/users`. Seed trong `seed_phase_two_data`. Đồng bộ graph Neo4j cho đơn vị/người dùng này là hạng mục Phase 05+ (hiện graph vẫn dựa `Department`/`User` suy ra từ `department_owner` và `final_approver` trên asset/purchase).
