# Phase 09: 3D Digital Twin

## Mục tiêu

Thêm mô phỏng 3D thang máy để người dùng nhìn thấy trạng thái Digital Twin trực quan.

## Trạng thái tài liệu

Phase này hiện là **roadmap chưa implement** trong frontend/backend hiện tại.

Điều kiện tiên quyết:

- chỉ nên triển khai sau khi Phase 07-08 có model/API telemetry và alert thật,
- không dùng 3D như minh họa độc lập nếu chưa có dữ liệu trạng thái từ backend.

3D trong phase này không thay thế dashboard, ontology map hoặc rule engine. Nó là một view vận hành đọc dữ liệu từ Asset/Component/Sensor/Alert.

## Nguyên tắc

1. 3D phải bind với dữ liệu thật hoặc dữ liệu giả lập có schema.
2. Không dùng 3D chỉ làm hình minh họa tĩnh.
3. Mỗi component trong 3D phải map được về `component_code`.
4. Sensor marker trong 3D phải map được về `sensor_code`.
5. Alert màu/animation phải đến từ backend state, không hard-code.

## Công nghệ

Frontend:

```text
Three.js hoặc React Three Fiber
```

Asset 3D:

```text
MVP: dựng hình bằng primitive geometry
Sau MVP: dùng .glb/.gltf từ CAD/model thật
```

## 3D scene MVP

Scene cần có:

```text
Elevator shaft
Cabin
Traction cable
Motor
Door
Sensor markers
Alert badge
Telemetry overlay
```

Mapping:

```json
{
  "ELV-CALIDAS-01": "scene_root",
  "CMP-CABLE-001": "traction_cable_mesh",
  "SNS-CABLE-VIB-001": "cable_vibration_marker"
}
```

## API sử dụng

```text
GET /api/assets/{asset_id}
GET /api/assets/{asset_id}/ontology
GET /api/assets/{asset_id}/telemetry/latest
GET /api/sensor-alerts?asset_id={asset_id}&status=open
```

Realtime MVP:

```text
Polling 3-5 giây
```

Realtime nâng cấp:

```text
GET /api/realtime/assets/{asset_id}/events
```

## Visual state

Component state:

```text
normal -> gray/green
warning -> amber
critical -> red
unknown -> neutral
```

Sensor marker:

```text
good quality -> solid
estimated -> dashed
bad/missing -> muted
```

Animation MVP:

```text
Cabin idle/moving
Cable vibration intensity theo vibration value
Door open/close theo door_cycle event hoặc simulator
Alert pulse khi có SensorAlert open
```

## UI cần có

```text
3D viewport
Asset selector
Component inspector
Sensor latest value
Open alert list
Toggle labels
Reset camera
```

Không đưa hướng dẫn dài vào UI. Tooltips ngắn là đủ.

## Deliverables

- Component `ElevatorTwin3D`.
- Model primitive cho shaft/cabin/cable/motor/door.
- Sensor marker gắn theo `sensor_code`.
- Bind latest telemetry vào material/animation.
- Bind open alert vào màu component.
- Inspector khi click component/sensor.
- Responsive desktop/mobile.

## Tiêu chí hoàn thành

Phase 09 đạt khi:

1. Dashboard hiển thị 3D Twin của `ELV-CALIDAS-01`.
2. Cáp kéo trong scene map đúng `CMP-CABLE-001`.
3. Sensor marker map đúng `SNS-CABLE-VIB-001`.
4. Khi có vibration cao/open alert, cáp đổi màu cảnh báo.
5. Khi telemetry thay đổi, 3D view cập nhật theo polling hoặc realtime event.
6. Click component/sensor thấy context tương ứng.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| 3D đẹp nhưng không đúng dữ liệu | Bắt buộc mapping asset/component/sensor từ backend |
| Scene nặng | MVP dùng primitive geometry, model .glb để phase sau |
| UI khó dùng | Giữ inspector đơn giản, ưu tiên trạng thái và alert |
| Mobile giật | Tắt shadow/hiệu ứng nặng ở viewport nhỏ |
