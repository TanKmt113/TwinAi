# Giả lập khởi động MVP thang máy

Tài liệu này giả lập ba phần cần làm đầu tiên trước khi xây hệ thống thật:

1. Chốt use case thang máy.
2. Lấy dữ liệu vận hành tối thiểu.
3. Xác nhận rule đầu tiên với trưởng bộ phận kỹ thuật.

Lưu ý: Toàn bộ dữ liệu trong tài liệu này là dữ liệu giả lập để làm mẫu. Khi triển khai thật, cần thay bằng dữ liệu từ bộ phận kỹ thuật, kho, mua hàng và phê duyệt nội bộ.

## 1. Chốt use case MVP

### 1.1. Tên use case

**Agentic AI cảnh báo bảo trì và đề xuất mua phụ tùng cho thang máy**

### 1.2. Mục tiêu

Hệ thống cần tự động phát hiện thang máy có linh kiện sắp hết tuổi thọ, tạo task kiểm tra kỹ thuật, kiểm tra tồn kho phụ tùng, đánh giá nhu cầu mua hàng và xác định người phê duyệt.

### 1.3. Phạm vi MVP

MVP chỉ tập trung vào:

- Thang máy trong khu khách sạn/cơ sở vật chất.
- Linh kiện quan trọng nhất: cáp kéo.
- Rule đầu tiên: cáp kéo còn dưới hoặc bằng 6 tháng tuổi thọ thì cần kiểm tra.
- Kết nối tối thiểu với tồn kho, mua hàng và phê duyệt.

MVP chưa xử lý:

- Toàn bộ thiết bị kỹ thuật khác.
- Toàn bộ manual thang máy.
- Tự động gửi đơn mua hàng thật.
- Tích hợp trực tiếp với ERP/kế toán.
- Dự báo hỏng hóc bằng machine learning.

### 1.4. Câu hỏi hệ thống phải trả lời được

```text
Có thang máy nào sắp cần kiểm tra hoặc thay linh kiện không?
```

Câu trả lời đạt yêu cầu phải có:

- Tên thang máy.
- Linh kiện liên quan.
- Tuổi thọ còn lại.
- Rule được kích hoạt.
- Nguồn căn cứ từ manual/quy trình.
- Tình trạng tồn kho.
- Có cần đề xuất mua hàng không.
- Người phê duyệt.
- Dữ liệu còn thiếu nếu chưa đủ căn cứ.

### 1.5. Kết quả đầu ra của MVP

Hệ thống tạo được:

1. Cảnh báo kỹ thuật.
2. Task kiểm tra cáp kéo.
3. Danh sách bằng chứng cần đo.
4. Kiểm tra tồn kho phụ tùng.
5. Đề xuất mua hàng nếu cần.
6. Người phê duyệt theo quy trình.
7. Audit log cho việc agent tạo hành động.

## 2. Dữ liệu vận hành giả lập

### 2.1. Danh sách thang máy

| Mã tài sản | Tên tài sản | Vị trí | Bộ phận sở hữu | Trạng thái |
|---|---|---|---|---|
| ELV-CALIDAS-01 | Thang máy Calidas 1 | Sảnh khách sạn - trục A | Kỹ thuật | Đang vận hành |
| ELV-CALIDAS-02 | Thang máy Calidas 2 | Sảnh khách sạn - trục B | Kỹ thuật | Đang vận hành |
| ELV-SERVICE-01 | Thang máy dịch vụ 1 | Khu hậu cần | Kỹ thuật | Đang vận hành |

### 2.2. Danh sách linh kiện theo dõi

| Mã linh kiện | Tài sản | Tên linh kiện | Loại | Ngày lắp đặt | Tuổi thọ thiết kế | Tuổi thọ còn lại | Ngày kiểm tra gần nhất |
|---|---|---|---|---|---:|---:|---|
| CMP-CABLE-001 | ELV-CALIDAS-01 | Cáp kéo Calidas 1 | Cáp kéo | 2020-11-15 | 72 tháng | 5 tháng | 2026-01-20 |
| CMP-CABLE-002 | ELV-CALIDAS-02 | Cáp kéo Calidas 2 | Cáp kéo | 2022-02-10 | 72 tháng | 22 tháng | 2026-01-22 |
| CMP-CABLE-003 | ELV-SERVICE-01 | Cáp kéo thang dịch vụ 1 | Cáp kéo | 2021-08-01 | 72 tháng | 15 tháng | 2026-02-05 |

### 2.3. Dữ liệu tồn kho phụ tùng

| Mã phụ tùng | Tên phụ tùng | Dùng cho linh kiện | Số lượng tồn | Số lượng tối thiểu | Lead time mua hàng | Nhà cung cấp |
|---|---|---|---:|---:|---:|---|
| SP-CABLE-CALIDAS | Bộ cáp kéo Calidas | Cáp kéo Calidas 1/2 | 0 | 1 | 7 tháng | Nhà cung cấp Đức |
| SP-CABLE-SERVICE | Bộ cáp kéo thang dịch vụ | Cáp kéo thang dịch vụ | 1 | 1 | 4 tháng | Nhà cung cấp nội địa |

### 2.4. Quy trình phê duyệt giả lập

| Loại yêu cầu | Điều kiện | Người phê duyệt cấp 1 | Người phê duyệt cuối |
|---|---|---|---|
| Mua phụ tùng thang máy | Giá trị dưới 100 triệu VND | Trưởng bộ phận kỹ thuật | Giám đốc vận hành |
| Mua phụ tùng thang máy | Giá trị từ 100 triệu VND trở lên hoặc nhập khẩu | Trưởng bộ phận kỹ thuật | CEO |

### 2.5. Manual/quy trình liên quan

| Mã tài liệu | Tên tài liệu | Bộ phận sở hữu | Nội dung liên quan | Trạng thái |
|---|---|---|---|---|
| MAN-ELV-001 | Manual bảo trì thang máy Calidas | Kỹ thuật | Kiểm tra cáp kéo định kỳ, đo đường kính cáp, kiểm tra rung động | Đã nhận bản PDF |
| SOP-MNT-001 | Quy trình tạo task bảo trì | Kỹ thuật | Khi có cảnh báo, tạo task cho kỹ thuật viên phụ trách | Cần xác nhận |
| SOP-PUR-001 | Quy trình mua phụ tùng kỹ thuật | Mua hàng | Tạo yêu cầu mua hàng, lấy báo giá, trình phê duyệt | Cần xác nhận |
| SOP-APP-001 | Quy trình phê duyệt mua hàng | Hành chính/CEO Office | Phân quyền phê duyệt theo giá trị và nguồn hàng | Cần xác nhận |

## 3. Rule đầu tiên cần xác nhận

### 3.1. Rule nghiệp vụ

```yaml
rule_id: R-ELV-CABLE-001
name: Cảnh báo cáp kéo thang máy còn dưới hoặc bằng 6 tháng tuổi thọ
domain: elevator_maintenance
status: draft_for_validation
owner_department: Kỹ thuật
source_manual: MAN-ELV-001
condition:
  component_type: cable
  remaining_lifetime_months_lte: 6
actions:
  - create_technical_alert
  - create_inspection_task
  - require_evidence_measurement
  - check_spare_part_inventory
  - evaluate_purchase_need
  - identify_approval_flow
evidence_required:
  - cable_diameter_measurement
  - vibration_measurement
  - last_inspection_date
  - technician_assessment
human_approval_required: true
```

### 3.2. Diễn giải rule bằng ngôn ngữ nghiệp vụ

Nếu một cáp kéo thang máy còn dưới hoặc bằng 6 tháng tuổi thọ, hệ thống phải tạo cảnh báo cho bộ phận kỹ thuật và tạo task kiểm tra thực tế.

Task kiểm tra phải yêu cầu kỹ thuật viên ghi nhận ít nhất:

- Đường kính cáp.
- Mức rung động khi vận hành.
- Ngày kiểm tra gần nhất.
- Nhận định của kỹ thuật viên.

Sau đó hệ thống kiểm tra phụ tùng thay thế trong kho. Nếu tồn kho không đủ và lead time mua hàng dài hơn thời gian còn lại của linh kiện, hệ thống tạo đề xuất mua hàng. Đề xuất mua hàng chỉ là đề xuất, chưa được tự động gửi thành đơn mua hàng thật nếu chưa có người phê duyệt.

### 3.3. Kết quả chạy rule trên dữ liệu giả lập

| Tài sản | Linh kiện | Tuổi thọ còn lại | Rule kích hoạt | Kết quả |
|---|---|---:|---|---|
| Thang máy Calidas 1 | Cáp kéo Calidas 1 | 5 tháng | R-ELV-CABLE-001 | Tạo cảnh báo, tạo task kiểm tra, đề xuất mua hàng |
| Thang máy Calidas 2 | Cáp kéo Calidas 2 | 22 tháng | Không | Không tạo cảnh báo |
| Thang máy dịch vụ 1 | Cáp kéo thang dịch vụ 1 | 15 tháng | Không | Không tạo cảnh báo |

### 3.4. Chuỗi Ontology được chứng minh

```text
Thang máy Calidas 1
  -> có linh kiện Cáp kéo Calidas 1
  -> cáp kéo còn 5 tháng tuổi thọ
  -> kích hoạt rule R-ELV-CABLE-001
  -> cần task kiểm tra kỹ thuật
  -> cần Bộ cáp kéo Calidas nếu phải thay
  -> tồn kho hiện tại = 0
  -> lead time mua hàng = 7 tháng
  -> cần đề xuất mua hàng
  -> hàng nhập khẩu
  -> người phê duyệt cuối = CEO
```

## 4. Giả lập biên bản xác nhận với trưởng bộ phận kỹ thuật

### 4.1. Thông tin cuộc họp giả lập

| Trường | Nội dung |
|---|---|
| Ngày họp | 24.04.2026 |
| Người xác nhận nghiệp vụ | Trưởng bộ phận kỹ thuật |
| Người tham gia | AI Team, Kỹ thuật, Kho, Mua hàng |
| Chủ đề | Xác nhận rule cảnh báo cáp kéo thang máy |
| Trạng thái | Giả lập - cần thay bằng xác nhận thật |

### 4.2. Nội dung đã thống nhất giả lập

1. Cáp kéo là linh kiện quan trọng, cần được theo dõi trong MVP đầu tiên.
2. Mốc 6 tháng trước khi hết tuổi thọ là mốc hợp lý để tạo cảnh báo kiểm tra.
3. Cảnh báo không đồng nghĩa với thay ngay; bắt buộc phải có kiểm tra thực tế.
4. Kỹ thuật viên phải đo đường kính cáp và rung động trước khi kết luận.
5. Nếu tồn kho phụ tùng bằng 0 và lead time mua hàng dài hơn thời gian còn lại, hệ thống được phép tạo đề xuất mua hàng.
6. Đề xuất mua hàng phải chờ phê duyệt của người có thẩm quyền.
7. Hệ thống không được tự động gửi đơn mua hàng thật trong giai đoạn MVP.

### 4.3. Điểm cần xác nhận thật

| Câu hỏi | Người cần xác nhận | Trạng thái |
|---|---|---|
| Mốc 6 tháng có đúng với manual và thực tế vận hành không? | Trưởng bộ phận kỹ thuật | Chưa xác nhận thật |
| Cần đo thêm chỉ số nào ngoài đường kính cáp và rung động? | Kỹ thuật viên thang máy | Chưa xác nhận thật |
| Ai nhận task kiểm tra đầu tiên? | Trưởng bộ phận kỹ thuật | Chưa xác nhận thật |
| Lead time 7 tháng với cáp Calidas có đúng không? | Mua hàng | Chưa xác nhận thật |
| Bộ cáp kéo Calidas có bắt buộc nhập khẩu từ Đức không? | Mua hàng | Chưa xác nhận thật |
| Ngưỡng giá trị nào phải trình CEO? | CEO Office/Hành chính | Chưa xác nhận thật |
| Dữ liệu tồn kho hiện tại nằm ở đâu? | Kho | Chưa xác nhận thật |

### 4.4. Quyết định giả lập

```text
Rule R-ELV-CABLE-001 được chấp nhận ở mức draft_for_validation.

AI Team được phép dùng rule này để xây prototype nội bộ với dữ liệu giả lập.

Trước khi chạy với dữ liệu thật, rule phải được trưởng bộ phận kỹ thuật xác nhận lại bằng văn bản hoặc email.
```

## 5. Checklist cần làm sau tài liệu giả lập này

### 5.1. Việc của AI Team

- [ ] Tạo schema dữ liệu cho assets, components, inventory_items, rules, tasks, purchase_requests.
- [ ] Tạo dữ liệu seed từ bảng giả lập.
- [ ] Xây API `POST /reasoning/run`.
- [ ] Xây màn hình hiển thị kết quả rule.
- [ ] Xây màn hình task kiểm tra.
- [ ] Xây màn hình đề xuất mua hàng.
- [ ] Xây audit log cho agent run.

### 5.2. Việc của bộ phận kỹ thuật

- [ ] Cung cấp danh sách thang máy thật.
- [ ] Cung cấp danh sách linh kiện quan trọng.
- [ ] Cung cấp ngày lắp đặt hoặc tuổi thọ còn lại.
- [ ] Cung cấp manual bảo trì.
- [ ] Xác nhận rule R-ELV-CABLE-001.
- [ ] Chỉ định người nhận task kiểm tra.

### 5.3. Việc của bộ phận kho

- [ ] Cung cấp danh sách phụ tùng thang máy.
- [ ] Cung cấp số lượng tồn kho.
- [ ] Cung cấp mã phụ tùng thống nhất.
- [ ] Xác nhận cách kiểm tra tồn kho.

### 5.4. Việc của bộ phận mua hàng

- [ ] Cung cấp lead time mua hàng.
- [ ] Cung cấp nhà cung cấp chính.
- [ ] Cung cấp quy trình tạo yêu cầu mua hàng.
- [ ] Xác nhận điều kiện nào cần đề xuất mua hàng sớm.

### 5.5. Việc của người phê duyệt

- [ ] Xác nhận ngưỡng phê duyệt.
- [ ] Xác nhận người phê duyệt cuối.
- [ ] Xác nhận MVP chỉ tạo đề xuất, chưa tạo đơn mua hàng thật.

## 6. Đầu ra mong muốn cho sprint đầu tiên

Sau sprint đầu tiên, hệ thống demo thực tế cần hiển thị được:

1. Danh sách thang máy và linh kiện.
2. Thang máy nào có cáp kéo còn dưới hoặc bằng 6 tháng.
3. Rule nào được kích hoạt.
4. Task kiểm tra nào được tạo.
5. Phụ tùng nào cần kiểm tra tồn kho.
6. Có cần tạo đề xuất mua hàng không.
7. Ai là người phê duyệt.
8. Câu trả lời tiếng Việt có căn cứ cho câu hỏi:

```text
Có thang máy nào sắp cần kiểm tra hoặc thay linh kiện không?
```

