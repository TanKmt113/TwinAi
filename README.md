# TwinAI Agentic MVP

Codebase MVP cho hệ thống Agentic AI Ontology nội bộ.

Trạng thái thực tế hiện tại:

- **Đã implement chắc:** Phase 01-04.
- **Đã implement một phần đáng kể:** Phase 05 (approval, routing, notification, audit, login JWT MVP).
- **Chưa implement theo đúng roadmap Digital Twin:** Phase 07-10.

Roadmap mở rộng vẫn giữ **Phase 07-10** cho Digital Twin realtime sensor và mô phỏng 3D, nhưng các phần này hiện chủ yếu mới ở mức tài liệu thiết kế.

## Cấu trúc chính

```text
apps/
  api/        FastAPI backend
  web/        Next.js frontend
infra/        Docker Compose, PostgreSQL, Neo4j, MinIO, n8n, pgAdmin
docs/         Tài liệu kỹ thuật triển khai
phase/        Kế hoạch phát triển theo phase
```

## Chạy stack hiện tại

```bash
cd infra
docker compose up --build
```

Sau khi chạy:

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Neo4j: `http://localhost:7474`
- pgAdmin: `http://localhost:5050`
- MinIO: `http://localhost:9001`
- n8n: `http://localhost:5678`

## Health check

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/dependencies
```

## Dashboard hiện có

Frontend tại:

```text
http://localhost:3000
```

Dashboard hiện có:

- Số lượng tài sản, rủi ro, task mở, purchase request.
- Bảng thang máy và linh kiện.
- Nút `Chạy suy luận`.
- Danh sách agent runs.
- Task kiểm tra.
- Purchase request draft.
- Ontology map cho chuỗi thang máy -> linh kiện -> rule -> manual -> mua hàng -> phê duyệt.
- Khu upload/parse manual.
- Chat/RAG hỏi đáp có citations.
- Chat agent có tool context (`get_asset_risks`, `get_asset_ontology`, `search_manual_chunks`, approval/purchase context). Nếu cấu hình `GEMINI_API_KEY` hoặc `OPENAI_API_KEY`, backend gọi LLM để tổng hợp JSON có guardrail; nếu chưa có key, hệ thống fallback sang rule-based response và vẫn ghi agent run.

## Phase 2 API vẫn dùng

Sau khi stack chạy:

```bash
curl http://localhost:8000/api/assets
curl -X POST http://localhost:8000/api/reasoning/run
curl http://localhost:8000/api/inspection-tasks
curl http://localhost:8000/api/purchase-requests
```

## Chat / RAG API

```bash
curl http://localhost:8000/api/manuals
curl -X POST http://localhost:8000/api/chat/query \
  -H "content-type: application/json" \
  -d '{"question":"Có thang máy nào sắp cần kiểm tra hoặc thay linh kiện không?"}'
```

Muốn bật LLM tool agent cho chat:

```bash
# mặc định dùng Gemini
GEMINI_API_KEY=... docker compose up --build

# hoặc chuyển sang OpenAI
LLM_PROVIDER=openai OPENAI_API_KEY=... docker compose up --build
```

Phase 02 đã thêm:

- PostgreSQL schema nghiệp vụ bằng SQLAlchemy.
- Seed data thang máy từ tài liệu 07.
- Neo4j Sync Service cho Ontology graph.
- Rule Engine `R-ELV-CABLE-001`.
- API `POST /api/reasoning/run`.

## Phase 05 hiện trạng

Repo hiện đã có nhiều phần của Phase 05:

- Purchase lifecycle: submit / approve / reject / cancel.
- Dual approval cho vật tư import.
- Org routing MVP theo SQL seed.
- Notification qua n8n theo kiểu best-effort.
- Audit log API + UI.
- Login JWT MVP và bảo vệ một số luồng write.

Tuy nhiên đây vẫn là MVP vận hành, chưa phải orchestration enterprise hoàn chỉnh như sơ đồ mục tiêu.

## Digital Twin mở rộng

Sau Phase 06, roadmap mới bổ sung:

```text
Phase 07: Realtime Sensor + Telemetry
Phase 08: Realtime Rule Engine
Phase 09: 3D Digital Twin
Phase 10: Nghiệm thu Digital Twin
```

Mục tiêu roadmap:

- Nhận sensor reading cho thang máy/linh kiện.
- Lưu latest/history telemetry.
- Gắn Sensor/SensorAlert vào Neo4j ontology.
- Chạy rule realtime như `R-ELV-VIB-001`.
- Hiển thị 3D Digital Twin bằng Three.js.
- Bind trạng thái 3D theo telemetry và alert.

Luồng mục tiêu theo thiết kế:

```text
Sensor reading
  -> Telemetry API
  -> Realtime Rule Engine
  -> SensorAlert
  -> Neo4j Ontology
  -> 3D Twin đổi trạng thái
  -> Chat trả lời có telemetry evidence
```

Lưu ý quan trọng:

- Trong code hiện tại **chưa có** model/API đầy đủ cho `Sensor`, `SensorReading`, `SensorAlert`, realtime rule engine và 3D twin như luồng trên.
- Phần gần nhất với telemetry hiện nay là `POST /api/iot/telemetry`, đây là luồng **IoT incident demo**:
  - nhận metric đơn,
  - so ngưỡng tĩnh trong code,
  - tạo `OperationalIncident`,
  - có thể route notification.
- Luồng IoT demo này **không tương đương** kiến trúc Digital Twin realtime đầy đủ của Phase 07-10.
