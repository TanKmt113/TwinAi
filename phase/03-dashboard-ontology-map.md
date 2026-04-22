# Phase 03: Dashboard + Ontology Map

## Mục tiêu

Xây giao diện để người dùng xem dữ liệu, chạy reasoning và hiểu chuỗi Ontology.

## Phạm vi

Frontend cần hiển thị được:

- Dashboard tổng quan.
- Danh sách thang máy và linh kiện.
- Kết quả agent run.
- Task kiểm tra.
- Purchase request draft.
- Ontology map cho Calidas 1.

## Màn hình cần có

### 1. Dashboard

Thông tin hiển thị:

- Số cảnh báo đang mở.
- Số task kiểm tra.
- Số purchase request draft/chờ duyệt.
- Tài sản có rủi ro cao.

### 2. Asset List

Bảng:

```text
Mã tài sản
Tên tài sản
Vị trí
Trạng thái
Số linh kiện đang theo dõi
Rủi ro hiện tại
```

### 3. Asset Detail

Hiển thị:

- Thông tin thang máy.
- Danh sách linh kiện.
- Tuổi thọ còn lại.
- Rule áp dụng.
- Task liên quan.
- Purchase request liên quan.

### 4. Ontology Map

Hiển thị graph:

```text
Asset -> Component -> Rule -> Manual
Component -> SparePart -> InventoryItem
PurchaseRequest -> ApprovalPolicy -> User
```

Gợi ý thư viện:

- React Flow cho graph tương tác.
- Hoặc SVG/Canvas đơn giản cho MVP.

### 5. Agent Run Detail

Hiển thị:

- Run ID.
- Thời gian chạy.
- Rule kích hoạt.
- Input snapshot.
- Output summary.
- Task/purchase request được tạo.
- Audit events.

## API sử dụng

```text
GET  /api/assets
GET  /api/assets/{asset_id}
GET  /api/assets/{asset_id}/ontology
POST /api/reasoning/run
GET  /api/agent-runs
GET  /api/inspection-tasks
GET  /api/purchase-requests
```

## Deliverables

- Next.js dashboard.
- Trang asset list.
- Trang asset detail.
- Nút chạy reasoning.
- Trang agent run detail.
- Ontology map đọc dữ liệu từ Neo4j API.
- Bảng task và purchase request.

## Tiêu chí hoàn thành

Phase 03 đạt khi:

1. Người dùng bấm "Chạy suy luận" từ UI.
2. UI hiển thị Calidas 1 bị kích hoạt rule.
3. UI hiển thị task kiểm tra được tạo.
4. UI hiển thị purchase request draft.
5. Ontology map thể hiện đúng chuỗi:

```text
Calidas 1 -> Cáp kéo -> Rule -> Manual -> SparePart -> Inventory -> Purchase -> CEO
```

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| UI chỉ đẹp nhưng không phản ánh graph thật | Ontology map phải gọi API lấy dữ liệu từ Neo4j |
| Người dùng không hiểu rule | Hiển thị rule, nguồn manual và lý do kích hoạt |
| Dashboard quá nhiều thông tin | MVP chỉ tập trung thang máy và cáp kéo |

