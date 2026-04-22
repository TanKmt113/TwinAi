# Phase 05: Approval + Notification + Audit

## Mục tiêu

Hoàn thiện vòng vận hành: purchase request được submit, phê duyệt/từ chối, gửi thông báo và truy vết đầy đủ.

## Phạm vi

Phase này xử lý:

- Purchase request lifecycle.
- Approval flow.
- Notification qua n8n.
- Audit log viewer.
- Role/permission MVP.

## Purchase request lifecycle

```text
draft
  -> waiting_for_approval
  -> approved
  -> rejected
  -> cancelled
```

## Approval logic

Dựa trên dữ liệu giả lập:

```text
Nếu mua phụ tùng thang máy nhập khẩu
  -> phê duyệt cấp 1: Trưởng bộ phận kỹ thuật
  -> phê duyệt cuối: CEO
```

## API cần build

```text
GET  /api/purchase-requests
GET  /api/purchase-requests/{request_id}
POST /api/purchase-requests/{request_id}/submit
POST /api/purchase-requests/{request_id}/approve
POST /api/purchase-requests/{request_id}/reject

GET  /api/audit-logs
GET  /api/audit-logs?entity_type=purchase_request&entity_id={id}
```

## n8n notification

Backend gọi n8n webhook khi:

- Có task kiểm tra mới.
- Có purchase request mới.
- Purchase request chờ duyệt.
- Purchase request được approve/reject.

Payload gợi ý:

```json
{
  "event": "purchase_request_waiting_for_approval",
  "request_id": "...",
  "asset": "Thang máy Calidas 1",
  "component": "Cáp kéo Calidas 1",
  "reason": "Còn 5 tháng tuổi thọ, tồn kho = 0, lead time = 7 tháng",
  "approver": "CEO"
}
```

## Audit log cần ghi

```text
agent_created_inspection_task
agent_created_purchase_request
user_submitted_purchase_request
user_approved_purchase_request
user_rejected_purchase_request
notification_sent
notification_failed
```

## Role MVP

```text
admin
ai_team
technical_manager
technician
warehouse_staff
purchase_staff
approver
viewer
```

## Deliverables

- Purchase request detail page.
- Submit/approve/reject actions.
- n8n webhook integration.
- Audit log table.
- Audit detail by entity.
- Permission guard cơ bản.

## Tiêu chí hoàn thành

Phase 05 đạt khi:

1. Agent tạo purchase request draft.
2. Người dùng submit request.
3. Hệ thống xác định approver.
4. n8n nhận webhook.
5. Approver approve/reject request.
6. Audit log ghi đầy đủ từng bước.
7. UI hiển thị lịch sử thay đổi.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Agent tự động hóa quá mức | Agent chỉ tạo draft, không submit thay người |
| Thiếu truy vết | Mọi action phải ghi audit log |
| Notification lỗi làm hỏng workflow | Notification failure không rollback dữ liệu chính |
| Sai người phê duyệt | Approval policy phải được cấu hình rõ và audit được |

