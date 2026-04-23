# Phase 07: Realtime Sensor + Telemetry

## Mục tiêu

Mở rộng MVP từ Ontology vận hành sang Digital Twin có trạng thái realtime.

Phase này tập trung nhận, lưu và hiển thị dữ liệu sensor. Chưa cần mô phỏng 3D và chưa cần MQTT thật nếu chưa có thiết bị.

## Phạm vi

Use case đầu tiên:

```text
Thang máy Calidas 1
  -> Cáp kéo Calidas 1
  -> Sensor rung SNS-CABLE-VIB-001
  -> Metric vibration
  -> Reading vibration theo thời gian
```

## Data model cần thêm

### Sensor

```text
id
code
asset_id
component_id
metric
unit
location
status
metadata_json
created_at
updated_at
```

Metric MVP:

```text
vibration
motor_temperature
door_cycle_count
load_weight
current_ampere
fault_code
```

### SensorReading

```text
id
sensor_id
measured_at
value
quality
metadata_json
created_at
```

`quality` dùng các giá trị:

```text
good
estimated
missing
bad
```

## API cần build

```text
GET  /api/sensors
GET  /api/assets/{asset_id}/sensors
POST /api/telemetry/readings
POST /api/telemetry/readings/batch
GET  /api/assets/{asset_id}/telemetry/latest
GET  /api/assets/{asset_id}/telemetry/history?sensor_code={code}&from={iso}&to={iso}
```

Payload ingest:

```json
{
  "sensor_code": "SNS-CABLE-VIB-001",
  "measured_at": "2026-04-23T10:30:00Z",
  "value": 6.8,
  "quality": "good",
  "metadata": {
    "source": "simulator"
  }
}
```

## Storage

MVP có thể dùng PostgreSQL thường:

```text
sensors
sensor_readings
```

Khi dữ liệu nhiều, chuyển sang TimescaleDB:

```text
sensor_readings -> hypertable by measured_at
```

Không đưa dữ liệu sensor realtime dày đặc vào Neo4j. Neo4j chỉ lưu quan hệ và trạng thái tổng hợp.

## Frontend

Thêm Telemetry panel trong dashboard:

```text
Asset
Sensor
Metric
Latest value
Unit
Measured at
Quality
Mini trend
```

MVP có thể polling mỗi 3-5 giây. SSE/WebSocket để Phase 08 hoặc 10.

## Deliverables

- SQLAlchemy model `Sensor`, `SensorReading`.
- Seed sensor cho `ELV-CALIDAS-01` và `CMP-CABLE-001`.
- API ingest single/batch reading.
- API latest/history.
- Telemetry panel trên dashboard.
- Simulator script hoặc nút tạo reading giả lập.

## Tiêu chí hoàn thành

Phase 07 đạt khi:

1. Gửi được reading cho `SNS-CABLE-VIB-001`.
2. Reading được lưu với timestamp và quality.
3. Dashboard hiển thị latest telemetry.
4. History API trả dữ liệu theo sensor.
5. Dữ liệu sensor map đúng về asset/component.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Sensor data quá nhiều | Bắt đầu PostgreSQL, chuẩn bị đường chuyển TimescaleDB |
| Sensor không map được asset/component | Bắt buộc seed/mapping sensor trước khi nhận reading |
| Dữ liệu giả lập bị hiểu là dữ liệu thật | Metadata phải ghi `source=simulator` |
| UI realtime gây tải backend | Bắt đầu bằng polling chậm, tối ưu sau bằng SSE |
