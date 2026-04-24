# Kế hoạch phát triển theo phase

Thư mục này tách kế hoạch triển khai từ tài liệu `08-thiet-ke-he-thong-mvp-agentic-ai.md` thành từng giai đoạn phát triển cụ thể.

Lưu ý:

- Đây là **roadmap + tài liệu phase**, không phải mọi phase trong danh sách đều đã được implement.
- Trạng thái code hiện tại khớp chắc với Phase 01-04.
- Phase 05 đã có nhiều phần chạy thật trong repo.
- Phase 07-10 hiện vẫn chủ yếu là mục tiêu Digital Twin, chưa có implementation đầy đủ trong code.

## Danh sách phase

- `00-tong-quan-phase.md`: tổng quan roadmap, nguyên tắc triển khai và thứ tự phụ thuộc.
- `01-nen-tang-kien-truc.md`: dựng nền tảng repo, Docker Compose, PostgreSQL, Neo4j, MinIO, FastAPI.
- `02-data-neo4j-rule-engine.md`: tạo schema dữ liệu, seed data, Neo4j graph, Rule Engine và API reasoning.
- `03-dashboard-ontology-map.md`: xây giao diện dashboard, danh sách thang máy, agent run và ontology map.
- `04-manual-rag-chat.md`: upload manual, parse/chunk, embedding, pgvector, chat có citations.
- `05-approval-notification-audit.md`: phê duyệt purchase request, org routing/escalation, notification qua n8n và audit log viewer.
- `06-nghiem-thu-mvp.md`: kịch bản nghiệm thu cuối cùng cho MVP.
- `07-realtime-sensor-telemetry.md`: thêm sensor model, API ingest telemetry và dashboard realtime cơ bản.
- `08-realtime-rule-engine.md`: thêm rule realtime từ sensor, sensor alert và đồng bộ sensor vào Neo4j.
- `09-3d-digital-twin.md`: thêm mô phỏng 3D thang máy bằng Three.js và bind dữ liệu realtime.
- `10-nghiem-thu-digital-twin.md`: nghiệm thu luồng Digital Twin mở rộng với sensor + 3D + ontology.

## Thứ tự triển khai

```text
Phase 01
  -> Phase 02
  -> Phase 03
  -> Phase 04
  -> Phase 05
  -> Phase 06
  -> Phase 07
  -> Phase 08
  -> Phase 09
  -> Phase 10
```

Phase 02 là lõi quan trọng nhất vì chứa dữ liệu, Neo4j Ontology graph và Rule Engine. Không nên build Chat/RAG trước khi Phase 02 chạy đúng.

Chi tiết **đồng bộ tài liệu ↔ code** cho Phase 04 (stack thực tế, intent `asset_component_count_query`, health UI, tồn đọng) nằm trong `phase/04-manual-rag-chat.md`. Phase 05 ghi rõ phần đã có thật trong code hiện tại ở `phase/05-approval-notification-audit.md`.

Phase 07-10 là phần mở rộng Digital Twin. Không nên build 3D trước khi có telemetry model và sensor API, vì 3D chỉ có giá trị vận hành khi được điều khiển bởi dữ liệu trạng thái thật hoặc giả lập có cấu trúc.

Nhánh `POST /api/iot/telemetry` hiện có trong code chỉ là **IoT incident demo**:

- nhận metric đơn,
- so ngưỡng tĩnh,
- tạo `OperationalIncident`.

Nó không thay thế cho Phase 07-10.
