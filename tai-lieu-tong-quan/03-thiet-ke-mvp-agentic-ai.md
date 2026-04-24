# Thiết kế MVP Agentic AI

## Ghi chú trạng thái hiện tại

Tài liệu này mô tả **thiết kế MVP mục tiêu**. So với code hiện tại:

- các phần Asset/Component/Rule/Manual/RAG/Chat/Task/Purchase đã có implementation chính,
- approval/routing/audit cũng đã có một phần đáng kể,
- còn phần realtime telemetry / Digital Twin chưa nằm trong phạm vi MVP đang chạy thật.

## Mục tiêu MVP

Xây dựng một hệ thống nhỏ có khả năng:

1. Đọc và quản lý tri thức từ manual/quy trình nội bộ.
2. Mô hình hóa các thực thể và mối quan hệ quan trọng bằng Ontology.
3. Phát hiện một số điều kiện cần cảnh báo hoặc hành động.
4. Cho phép người dùng hỏi bằng ngôn ngữ tự nhiên.
5. Trả lời có căn cứ, nêu được nguồn manual/quy tắc và hành động đề xuất.

MVP nên được xem là bài tập khởi động 1/100, không phải bản sản phẩm đầy đủ.

## Use case đề xuất số 1: Bảo trì thang máy

### Bài toán

Công ty cần đảm bảo thang máy được bảo trì đúng hạn, phát hiện sớm rủi ro hết tuổi thọ linh kiện, đồng thời kết nối được với kho phụ tùng, mua hàng và phê duyệt.

### Thực thể cốt lõi

- `Elevator`: thang máy.
- `Component`: linh kiện, ví dụ cáp kéo, motor, bộ điều khiển.
- `MaintenanceManual`: manual bảo trì.
- `MaintenanceRule`: quy tắc bảo trì.
- `InspectionTask`: nhiệm vụ kiểm tra.
- `SparePart`: phụ tùng thay thế.
- `InventoryItem`: tồn kho.
- `PurchaseRequest`: yêu cầu mua hàng.
- `ApprovalPolicy`: quy trình phê duyệt.
- `Approver`: người phê duyệt.

### Mối quan hệ mẫu

- `Elevator` có `Component`.
- `Component` có `expected_lifetime`.
- `MaintenanceManual` định nghĩa `MaintenanceRule`.
- `MaintenanceRule` áp dụng cho `Component`.
- `Component` cần `SparePart` khi hết hạn hoặc không đạt kiểm tra.
- `SparePart` được quản lý bởi `InventoryItem`.
- `InventoryItem` thiếu hàng thì tạo `PurchaseRequest`.
- `PurchaseRequest` cần `ApprovalPolicy`.
- `ApprovalPolicy` gắn với `Approver`.

### Quy tắc suy luận mẫu

Nếu linh kiện còn dưới 6 tháng tuổi thọ:

1. Tạo cảnh báo kỹ thuật.
2. Tạo nhiệm vụ kiểm tra.
3. Kiểm tra tồn kho phụ tùng thay thế.
4. Nếu phụ tùng không có sẵn và lead time mua hàng lớn hơn thời gian còn lại, tạo đề xuất mua hàng.
5. Xác định người phê duyệt theo quy trình.
6. Lập lịch kiểm tra lại nếu kết quả kiểm tra chưa cần thay.

## Kiến trúc MVP

### Lớp dữ liệu đầu vào

Nguồn dữ liệu ban đầu:

- Manual thang máy.
- Quy trình bảo trì.
- Danh sách thang máy và linh kiện.
- Lịch sử bảo trì.
- Tồn kho phụ tùng.
- Quy trình mua hàng.
- Sơ đồ phê duyệt.

### Lớp chuẩn hóa tri thức

Cần chuyển tài liệu thành các đối tượng có cấu trúc:

- Thực thể.
- Thuộc tính.
- Mối quan hệ.
- Điều kiện.
- Hành động.
- Nguồn căn cứ.

Ví dụ:

```yaml
rule_id: elevator_cable_inspection_6_months
source: Manual bảo trì thang máy
condition: cable.remaining_lifetime_months <= 6
action:
  - create_inspection_task
  - check_spare_part_inventory
  - evaluate_purchase_need
evidence_required:
  - cable_diameter
  - vibration_measurement
  - last_inspection_date
```

### Lớp Ontology

Ontology là nơi lưu mô hình logic và mối quan hệ. Đây là phần cần thiết kế thủ công/có kiểm soát, không giao cho LLM tự do suy đoán.

Yêu cầu:

- Có schema rõ ràng.
- Có tên thực thể và quan hệ nhất quán.
- Có quy tắc suy luận minh bạch.
- Có khả năng truy vết nguồn.
- Có cơ chế kiểm tra tính hợp lệ của dữ liệu.

### Lớp LLM

LLM đóng vai trò:

- Hiểu câu hỏi của người dùng.
- Tìm đúng thực thể/quy tắc trong Ontology.
- Tổng hợp câu trả lời thành ngôn ngữ tự nhiên.
- Giải thích lý do dựa trên bằng chứng.

LLM không nên:

- Tự tạo quy tắc không có trong Ontology.
- Tự đưa ra quyết định nếu thiếu dữ liệu.
- Thay đổi logic nghiệp vụ khi chưa có phê duyệt.

### Lớp Agent

Agent là thành phần biến logic thành hành động:

- Tạo task.
- Gửi cảnh báo.
- Đề xuất mua hàng.
- Lập lịch kiểm tra.
- Yêu cầu phê duyệt.
- Theo dõi trạng thái đến khi đóng quy trình.

## Tiêu chí hoàn thành MVP

MVP được xem là đạt nếu có thể:

- Trả lời câu hỏi: "Có thang máy nào sắp cần kiểm tra hoặc thay linh kiện không?"
- Đưa ra lý do và nguồn căn cứ từ manual/quy tắc.
- Hiển thị được chuỗi liên kết: thang máy -> linh kiện -> tuổi thọ -> quy tắc bảo trì -> tồn kho -> mua hàng -> phê duyệt.
- Tạo được đề xuất hành động rõ ràng.
- Phân biệt được trường hợp đủ thông tin và thiếu thông tin.

Ghi chú:

- Các tiêu chí trên hiện khớp với hướng `agentic operations MVP`.
- Không nên đọc tài liệu này như cam kết rằng repo hiện đã có sensor telemetry hoặc 3D twin.
