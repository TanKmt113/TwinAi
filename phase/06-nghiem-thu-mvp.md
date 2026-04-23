# Phase 06: Nghiệm thu MVP

## Mục tiêu

Xác nhận toàn bộ hệ thống MVP chạy đúng kịch bản end-to-end.

## Kịch bản nghiệm thu chính

### Bước 1: Mở dashboard

Kỳ vọng:

- Dashboard hiển thị dữ liệu thang máy.
- Calidas 1 có cáp kéo còn 5 tháng.
- Chưa cần hiển thị task nếu reasoning chưa chạy.

### Bước 2: Chạy reasoning

User bấm:

```text
Chạy suy luận
```

Backend gọi:

```text
POST /api/reasoning/run
```

Kỳ vọng:

- Agent run được tạo.
- Rule `R-ELV-CABLE-001` được kích hoạt.
- Calidas 1 được đánh dấu có rủi ro.

### Bước 3: Kiểm tra task

Kỳ vọng:

- Có task kiểm tra cáp kéo Calidas 1.
- Task yêu cầu evidence:
  - Đường kính cáp.
  - Độ rung.
  - Ngày kiểm tra gần nhất.
  - Nhận định kỹ thuật viên.

### Bước 4: Kiểm tra purchase request

Kỳ vọng:

- Có purchase request draft cho `SP-CABLE-CALIDAS`.
- Lý do:

```text
Cáp kéo còn 5 tháng, tồn kho = 0, lead time = 7 tháng.
```

- Người phê duyệt cuối: CEO.
- Người nhận xử lý đầu tiên: kỹ thuật viên hoặc primary contact đã cấu hình.
- Có backup contact hoặc escalation path cho asset.

### Bước 5: Kiểm tra Neo4j Ontology map

Kỳ vọng graph có chuỗi:

```text
Calidas 1
  -> Cáp kéo Calidas 1
  -> Rule R-ELV-CABLE-001
  -> Manual bảo trì thang máy
  -> Department Kỹ thuật
  -> Primary Contact
  -> Escalation Policy
  -> Bộ cáp kéo Calidas
  -> InventoryItem tồn kho 0
  -> PurchaseRequest
  -> ApprovalPolicy
  -> CEO
```

### Bước 6: Hỏi Chat

Câu hỏi:

```text
Có thang máy nào sắp cần kiểm tra hoặc thay linh kiện không?
```

Kỳ vọng câu trả lời có:

- Kết luận: Có, Calidas 1.
- Rule: `R-ELV-CABLE-001`.
- Căn cứ manual.
- Tồn kho.
- Lead time.
- Task đã tạo.
- Purchase request draft.
- Người cần được notify đầu tiên.
- Người phê duyệt.
- Citations.

### Bước 7: Câu hỏi ngoài phạm vi

Câu hỏi:

```text
Dự báo doanh thu tháng sau là bao nhiêu?
```

Kỳ vọng:

```text
Không đủ dữ liệu.
```

Không được bịa số liệu.

### Bước 8: Submit và approve purchase request

Kỳ vọng:

- Request chuyển từ `draft` sang `waiting_for_approval`.
- n8n nhận webhook.
- Hệ thống xác định đúng primary contact / backup contact / escalation target.
- Approver approve/reject.
- Audit log ghi đầy đủ.

## Checklist nghiệm thu

- [ ] Docker Compose chạy được toàn bộ service.
- [ ] PostgreSQL có seed data.
- [ ] Neo4j có graph data.
- [ ] Rule Engine chạy được.
- [ ] Không tạo trùng task.
- [ ] Không tạo trùng purchase request.
- [ ] UI hiển thị dashboard.
- [ ] UI hiển thị ontology map từ Neo4j.
- [ ] Manual được upload và parse.
- [ ] Chat trả lời có citations.
- [ ] Chat không hallucinate với câu hỏi ngoài phạm vi.
- [ ] Approval flow chạy được.
- [ ] Org routing xác định đúng primary contact / backup contact.
- [ ] n8n webhook nhận event.
- [ ] Audit log đầy đủ.

## Tiêu chí MVP đạt

MVP đạt nếu có thể demo trọn vẹn trong 10-15 phút cho stakeholder, từ dữ liệu thang máy đến agent action, approval, notification/escalation và câu trả lời có căn cứ.

## Tiêu chí chưa đạt

MVP chưa đạt nếu:

- Chỉ có chatbot nhưng không có Rule Engine.
- Chỉ có bảng dữ liệu nhưng không có Neo4j graph.
- Rule chạy nhưng không tạo task/purchase request.
- Rule chạy nhưng không xác định được cần báo cho ai.
- Chat trả lời không có citations.
- Không có audit log.
- Agent tự động gửi đơn mua hàng thật khi chưa phê duyệt.

