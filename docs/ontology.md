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
