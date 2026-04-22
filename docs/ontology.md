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
```

Phase 2 sẽ seed graph thật từ use case thang máy.

