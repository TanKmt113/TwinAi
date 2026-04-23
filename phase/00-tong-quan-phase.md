# Phase 00: Tổng quan roadmap

## Mục tiêu

Chia hệ thống MVP Agentic AI Ontology thành các giai đoạn phát triển có thể triển khai, kiểm thử và nghiệm thu độc lập.

## Nguyên tắc triển khai

1. Ontology và Rule Engine đi trước LLM.
2. Neo4j được dùng ngay từ MVP để lưu Ontology graph.
3. PostgreSQL giữ dữ liệu giao dịch, audit, task, purchase request.
4. LLM chỉ là lớp giao diện, không tự quyết định nghiệp vụ.
5. Mỗi phase phải có deliverable chạy được.
6. Không tự động gửi đơn mua hàng thật trong MVP.
7. Realtime sensor đi trước mô phỏng 3D; 3D phải phản ánh trạng thái twin thật, không chỉ là hình minh họa.
8. Sensor data phải có timestamp, quality và mapping rõ tới Asset/Component.

## Roadmap tổng quát

| Phase | Tên | Mục tiêu chính |
|---|---|---|
| 01 | Nền tảng kiến trúc | Dựng repo, Docker Compose, PostgreSQL, Neo4j, MinIO, FastAPI |
| 02 | Data + Neo4j + Rule Engine | Seed dữ liệu, tạo graph Ontology, chạy rule `R-ELV-CABLE-001` |
| 03 | Dashboard + Ontology Map | Xây UI quản trị, dashboard và bản đồ Ontology |
| 04 | Manual + RAG + Chat | Upload manual, embedding, hỏi đáp có citations |
| 05 | Approval + Notification + Audit | Phê duyệt, n8n notification, audit log viewer |
| 06 | Nghiệm thu MVP | Chạy kịch bản demo cuối cùng |
| 07 | Realtime Sensor + Telemetry | Thêm sensor, sensor readings, API ingest và realtime dashboard cơ bản |
| 08 | Realtime Rule Engine | Chạy rule từ sensor, tạo sensor alert, sync Sensor/SensorAlert vào Neo4j |
| 09 | 3D Digital Twin | Dựng mô phỏng 3D thang máy và bind trạng thái sensor/rule vào scene |
| 10 | Nghiệm thu Digital Twin | Demo end-to-end sensor -> ontology -> rule -> 3D -> task/chat |

## Luồng giá trị cần chứng minh

```text
Thang máy Calidas 1
  -> Cáp kéo còn 5 tháng
  -> Rule R-ELV-CABLE-001 được kích hoạt
  -> Tạo task kiểm tra
  -> Tồn kho cáp = 0
  -> Lead time = 7 tháng
  -> Tạo purchase request draft
  -> Người phê duyệt cuối = CEO
  -> Chat trả lời có căn cứ
```

## Luồng Digital Twin mở rộng cần chứng minh

```text
Sensor rung SNS-CABLE-VIB-001
  -> gửi reading vibration = 6.8 mm/s
  -> lưu SensorReading có timestamp và quality
  -> Rule R-ELV-VIB-001 được kích hoạt
  -> tạo SensorAlert cho CMP-CABLE-001
  -> đồng bộ Sensor/SensorAlert vào Neo4j
  -> 3D Twin đổi màu cáp kéo sang cảnh báo
  -> tạo task kiểm tra nếu đủ điều kiện
  -> Chat trả lời có telemetry evidence
```

## Agentic workflow cần chứng minh

```text
Trigger: user hỏi chat / bấm chạy suy luận / job định kỳ
  -> Agent Orchestrator tạo agent_run và chọn tool
  -> Ontology Agent lấy graph context từ Neo4j
  -> RAG Agent tìm manual chunk và citations
  -> Reasoning Agent chạy rule deterministic
  -> Action Agent tạo task hoặc purchase request draft nếu đủ điều kiện
  -> Approval Agent xác định policy và người phê duyệt
  -> Notification Agent gửi n8n webhook nếu cần
  -> Response Agent dùng LLM để tổng hợp JSON có căn cứ
```

## Realtime workflow cần chứng minh

```text
Trigger: sensor reading / MQTT event / simulator
  -> Telemetry Service validate sensor_code, metric, unit, timestamp
  -> ghi SensorReading vào PostgreSQL hoặc TimescaleDB
  -> Realtime Rule Engine kiểm tra window/threshold
  -> Sensor Alert Service tạo alert nếu vượt ngưỡng
  -> Ontology Sync Service upsert Sensor/SensorAlert vào Neo4j
  -> Realtime API đẩy event cho dashboard/3D Twin
  -> Action Agent tạo task nếu rule cho phép
```

Nguyên tắc: LLM chỉ diễn giải và gọi tool có schema. Rule Engine, Ontology và Domain Services mới là nơi quyết định nghiệp vụ.

## Deliverable cuối cùng

MVP được xem là đạt khi người dùng có thể:

1. Mở dashboard.
2. Xem Calidas 1 có rủi ro.
3. Chạy reasoning.
4. Xem task kiểm tra được tạo.
5. Xem purchase request draft.
6. Xem ontology map.
7. Hỏi bằng tiếng Việt và nhận câu trả lời có căn cứ.
8. Phê duyệt hoặc từ chối purchase request.
9. Xem audit log cho toàn bộ hành động.

Digital Twin mở rộng được xem là đạt khi người dùng có thể:

1. Gửi hoặc mô phỏng sensor reading cho Calidas 1.
2. Xem latest telemetry và history theo sensor.
3. Xem Sensor node trong ontology graph.
4. Kích hoạt rule realtime từ sensor vượt ngưỡng.
5. Xem SensorAlert và task liên quan.
6. Xem 3D Twin đổi trạng thái theo telemetry/alert.
7. Hỏi chat và nhận câu trả lời có telemetry evidence.
