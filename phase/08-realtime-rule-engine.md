# Phase 08: Realtime Rule Engine

## Mục tiêu

Biến telemetry thành hành động vận hành có căn cứ.

Phase này thêm rule realtime từ sensor, tạo alert, đồng bộ quan hệ sensor vào Neo4j và cho phép chat dùng telemetry evidence.

## Phạm vi

Rule MVP:

```yaml
rule_id: R-ELV-VIB-001
name: Cảnh báo rung cáp kéo vượt ngưỡng
condition:
  metric: vibration
  value_gt: 6.0
  window_minutes: 5
  min_samples: 3
actions:
  - create_sensor_alert
  - attach_telemetry_evidence
  - create_inspection_task_if_not_exists
  - identify_notification_targets
status: approved
```

## Data model cần thêm

### SensorAlert

```text
id
asset_id
component_id
sensor_id
rule_id
severity
status
reason
first_seen_at
last_seen_at
evidence_json
created_at
updated_at
```

Severity:

```text
info
warning
critical
```

Status:

```text
open
acknowledged
resolved
ignored
```

## Neo4j graph cần thêm

Node labels:

```text
Sensor
Metric
SensorAlert
```

Relationship types:

```text
(Asset)-[:HAS_SENSOR]->(Sensor)
(Component)-[:HAS_SENSOR]->(Sensor)
(Sensor)-[:MEASURES]->(Metric)
(Rule)-[:USES_METRIC]->(Metric)
(SensorAlert)-[:TRIGGERED_BY]->(Sensor)
(SensorAlert)-[:AFFECTS_COMPONENT]->(Component)
(InspectionTask)-[:CREATED_FROM_ALERT]->(SensorAlert)
```

## API cần build

```text
GET  /api/sensor-alerts
GET  /api/sensor-alerts/{alert_id}
POST /api/sensor-alerts/{alert_id}/acknowledge
POST /api/sensor-alerts/{alert_id}/resolve
POST /api/realtime-rules/evaluate
```

`POST /api/telemetry/readings` từ Phase 07 có thể tự gọi Realtime Rule Engine sau khi lưu reading.

## Rule Engine logic

```text
1. Nhận SensorReading mới.
2. Load sensor, asset, component.
3. Load approved realtime rules theo metric.
4. Lấy readings trong window_minutes.
5. Nếu đủ min_samples và vượt threshold:
   - tạo hoặc update SensorAlert đang open.
   - attach telemetry evidence.
   - tạo inspection task nếu rule yêu cầu và chưa có task mở.
   - lấy primary contact, backup contact và escalation policy cho asset/component bị ảnh hưởng.
   - sync Sensor/SensorAlert vào Neo4j.
   - ghi audit log.
```

## Chat/RAG extension

Chat tool context cần thêm:

```text
get_asset_telemetry(asset_code)
get_sensor_alerts(asset_code)
get_sensor_history(sensor_code, time_range)
get_notification_targets(asset_code, event_type)
```

Guardrail:

```text
Không dự đoán hỏng hóc nếu chỉ có một reading đơn lẻ.
Phải nêu metric, giá trị, thời gian đo và rule threshold.
Nếu thiếu telemetry history, trả "không đủ dữ liệu".
```

## Deliverables

- Model `SensorAlert`.
- Rule `R-ELV-VIB-001`.
- Realtime Rule Engine.
- Neo4j sync cho Sensor, Metric, SensorAlert.
- Alert list/detail UI.
- Notification/escalation routing cho alert severity warning/critical.
- Chat context có telemetry evidence.
- Unit test cho threshold/window/min_samples.

## Tiêu chí hoàn thành

Phase 08 đạt khi:

1. Gửi 3 reading vibration > 6.0 trong 5 phút.
2. Hệ thống tạo `SensorAlert` severity `warning` hoặc `critical`.
3. Neo4j có chuỗi `Component -> Sensor -> Metric` và `SensorAlert -> Sensor`.
4. Nếu rule cho phép, task kiểm tra được tạo.
5. Hệ thống xác định được ai cần được notify đầu tiên khi alert mở.
6. Chat trả lời được vì sao alert xuất hiện và dẫn evidence.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Alert spam | Deduplicate theo sensor/rule/status open |
| False positive | Dùng window + min_samples, không trigger từ 1 sample |
| Neo4j chứa quá nhiều reading | Chỉ sync sensor/alert/state, không sync từng reading |
| Chat diễn giải quá mức | Bắt buộc citation từ rule + telemetry evidence |
| Sai người nhận alert | Bắt buộc map asset/component với owner/contact/escalation policy từ ontology |
