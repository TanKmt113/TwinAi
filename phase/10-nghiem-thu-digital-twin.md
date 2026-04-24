# Phase 10: Nghiệm Thu Digital Twin

## Mục tiêu

Xác nhận phần mở rộng Digital Twin chạy đúng end-to-end:

```text
Sensor -> Telemetry -> Realtime Rule -> Neo4j Ontology -> Alert/Task -> 3D Twin -> Chat
```

## Trạng thái tài liệu

Đây là **checklist nghiệm thu roadmap**, chưa phải checklist cho phần code hiện đã có trong repo.

Hiện tại repo mới có nhánh IoT incident demo và MVP vận hành; chưa có pipeline Digital Twin đầy đủ để chạy checklist này.

## Kịch bản nghiệm thu chính

### Bước 1: Kiểm tra sensor seed

Kỳ vọng:

```text
ELV-CALIDAS-01 có sensor SNS-CABLE-VIB-001
Sensor gắn với CMP-CABLE-001
Metric = vibration
Unit = mm/s
```

### Bước 2: Gửi telemetry bình thường

Request:

```text
POST /api/telemetry/readings
```

Payload:

```json
{
  "sensor_code": "SNS-CABLE-VIB-001",
  "measured_at": "2026-04-23T10:30:00Z",
  "value": 3.2,
  "quality": "good",
  "metadata": {
    "source": "simulator"
  }
}
```

Kỳ vọng:

- Reading được lưu.
- Latest telemetry trả `3.2 mm/s`.
- Không tạo SensorAlert.
- 3D Twin hiển thị trạng thái bình thường.

### Bước 3: Gửi telemetry vượt ngưỡng

Gửi ít nhất 3 readings trong 5 phút:

```text
6.4
6.8
7.1
```

Kỳ vọng:

- Rule `R-ELV-VIB-001` được kích hoạt.
- Tạo `SensorAlert` open.
- Evidence ghi đủ sensor_code, metric, values, measured_at, threshold.
- Nếu rule cho phép, tạo inspection task.
- Xác định được primary contact hoặc notification group cho alert này.

### Bước 4: Kiểm tra Neo4j

Kỳ vọng graph có chuỗi:

```text
Calidas 1
  -> Cáp kéo Calidas 1
  -> Sensor SNS-CABLE-VIB-001
  -> Metric vibration
  -> SensorAlert
  -> Rule R-ELV-VIB-001
```

### Bước 5: Kiểm tra 3D Twin

Kỳ vọng:

- Scene render không trắng.
- Cabin/shaft/cable/motor/door hiển thị.
- Sensor marker xuất hiện trên vùng cáp.
- Cáp kéo đổi màu cảnh báo khi có alert open.
- Inspector hiển thị latest vibration và alert reason.

### Bước 6: Hỏi Chat

Câu hỏi:

```text
Vì sao cáp kéo Calidas 1 đang cảnh báo rung?
```

Kỳ vọng câu trả lời có:

- Kết luận.
- Sensor code.
- Metric và giá trị đo.
- Rule threshold.
- Thời gian đo.
- Alert/task liên quan nếu có.
- Người cần được notify hoặc escalation path nếu alert vẫn mở.
- Citations hoặc evidence từ telemetry/rule/manual.

### Bước 7: Resolve alert

Kỳ vọng:

- Alert chuyển `resolved`.
- 3D Twin trở về trạng thái bình thường nếu không còn alert open.
- Audit log ghi action.
- Notification/escalation state được cập nhật tương ứng.

## Checklist nghiệm thu

- [ ] Sensor model và seed data có đủ.
- [ ] API ingest single/batch reading chạy được.
- [ ] Latest/history telemetry trả đúng.
- [ ] Realtime rule không trigger nếu chưa đủ `min_samples`.
- [ ] Realtime rule trigger khi vượt threshold trong window.
- [ ] SensorAlert được deduplicate.
- [ ] Sensor/SensorAlert sync vào Neo4j.
- [ ] 3D Twin render đúng asset/component/sensor.
- [ ] 3D Twin cập nhật theo telemetry/alert.
- [ ] Chat dùng telemetry evidence.
- [ ] Alert có org routing đúng người nhận.
- [ ] Audit log ghi alert/task/resolve.

## Tiêu chí đạt

Digital Twin mở rộng đạt nếu demo được trong 10-15 phút:

```text
Gửi sensor reading giả lập
  -> dashboard thấy telemetry
  -> rule tạo alert
  -> hệ thống biết cần báo cho ai
  -> ontology graph có sensor/alert
  -> 3D Twin đổi trạng thái
  -> chat giải thích có evidence
```

## Tiêu chí chưa đạt

Chưa đạt nếu:

- 3D chỉ là hình tĩnh không bind dữ liệu.
- Sensor reading không map được asset/component.
- Alert tạo từ một sample đơn lẻ mà không có window/min_samples.
- Neo4j không có Sensor/SensorAlert relationship.
- Chat trả lời cảnh báo mà không có telemetry evidence.
- Alert mở nhưng hệ thống không xác định được người nhận thông báo/escalation.
