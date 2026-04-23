# Phase 05: Approval + Org Routing + Notification + Audit

## Mục tiêu

Hoàn thiện vòng vận hành: purchase request được submit, phê duyệt/từ chối, chọn đúng người nhận thông báo/escalation và truy vết đầy đủ.

Ghi chú trạng thái hiện tại:

- Repo có purchase request list/draft và audit log từ reasoning; **lifecycle submit / approve / reject**, **audit API**, **routing** (contacts, notification-targets, escalation policy đọc từ DB + seed), và **webhook n8n** sau commit đã có ở backend.
- **Org (đọc):** `org_units`, `org_users`, `GET /api/org/*`. Luồng purchase workflow dùng `role_tags` / policy seed (ví dụ `ELV-CABLE-ESCALATION-01`) cho routing MVP; chat vẫn có thể chưa resolve hết ngữ cảnh org.
- Neo4j: sync theo task/request trong workflow; đồng bộ full cây org như graph mục tiêu vẫn là mở rộng sau.
- **UI:** Workflows (thao tác nhanh + link chi tiết), trang `/purchase-requests/[id]` (tóm tắt, submit/approve/reject/cancel, audit table, JSON contacts + notification targets + escalation), trang `/audit-logs` (lọc `entity_type` / `entity_id`).
- **Bảo vệ ghi (MVP):** `PHASE5_WRITE_SECRET` + header `X-Phase5-Write-Secret` trên POST workflow; Next proxy tự gắn header nếu cùng biến môi trường.

## Điều kiện bắt đầu Phase 05 (từ Phase 04)

Phase 04 được coi là đủ để chuyển sang Phase 05 khi: manual upload+parse+search hoạt động, chat trả lời có căn cứ với LLM hoặc fallback, và health/deploy ổn định. Chi tiết tồn đọng nhẹ Phase 04 xem `phase/04-manual-rag-chat.md` mục “Trạng thái hoàn thành vs tồn đọng”.

## Phạm vi

Phase này xử lý:

- Purchase request lifecycle.
- Approval flow.
- Org routing cho asset/rule/sự cố.
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

## Org routing và escalation logic

Ontology cần trả lời:

```text
Asset này thuộc bộ phận nào?
Primary contact là ai?
Backup contact là ai?
Nếu sau 30 phút chưa acknowledge thì escalate cho ai?
Severity nào cần báo thêm cho quản lý hoặc approver?
```

Graph tổ chức MVP:

```text
Asset -> Department
Asset -> Primary Contact
Asset -> Backup Contact
Rule -> EscalationPolicy
Rule -> NotificationGroup
User -> Department
User -> ReportsTo -> User
```

## API cần build

**Đã có (đọc org — bổ sung trước timeline đầy đủ Phase 05):**

```text
GET  /api/org/units
GET  /api/org/users
```

**Đã có trên backend (Phase 05 — API):**

```text
GET  /api/purchase-requests
GET  /api/purchase-requests/{request_id}
POST /api/purchase-requests/{request_id}/submit
POST /api/purchase-requests/{request_id}/approve
POST /api/purchase-requests/{request_id}/reject
POST /api/purchase-requests/{request_id}/cancel

GET  /api/assets/{asset_id}/contacts
GET  /api/rules/{rule_id}/notification-targets
GET  /api/escalation-policies/{policy_id}

GET  /api/audit-logs
GET  /api/audit-logs?entity_type=purchase_request&entity_id={id}
```

## n8n notification

Backend gọi n8n webhook khi:

- Có task kiểm tra mới.
- Có purchase request mới.
- Purchase request chờ duyệt.
- Purchase request được approve/reject.
- Có alert cần báo cho primary contact.
- Có alert quá SLA cần escalate.

Payload gợi ý:

```json
{
  "event": "purchase_request_waiting_for_approval",
  "request_id": "...",
  "asset": "Thang máy Calidas 1",
  "component": "Cáp kéo Calidas 1",
  "reason": "Còn 5 tháng tuổi thọ, tồn kho = 0, lead time = 7 tháng",
  "approver": "CEO",
  "primary_contact": "Kỹ thuật viên trực",
  "backup_contact": "Trưởng bộ phận kỹ thuật",
  "escalation_policy": "ELV-CRITICAL-01"
}
```

## Agentic action flow

```text
Reasoning Agent phát hiện rule kích hoạt
  -> Action Agent tạo inspection task nếu chưa tồn tại
  -> Action Agent kiểm tra tồn kho và lead time
  -> Action Agent tạo purchase request draft nếu đủ điều kiện
  -> Approval Agent xác định approval policy và final approver
  -> Org Routing Agent lấy primary contact, backup contact, notification group, escalation policy
  -> Notification Agent gửi n8n webhook cho đúng người nhận khi request chờ duyệt hoặc task mới được tạo
  -> Audit Service ghi lại toàn bộ hành động
```

Guardrail:

```text
Agent chỉ tạo draft.
Agent không submit request thay người.
Agent không approve/reject thay người.
Mọi action phải có audit log.
Notification failure không rollback dữ liệu chính.
Không gửi sai đối tượng nếu asset/rule chưa có routing rõ ràng; khi thiếu routing phải báo "không đủ dữ liệu cấu hình".
```

## Audit log cần ghi

```text
agent_created_inspection_task
agent_created_purchase_request
user_submitted_purchase_request
user_approved_purchase_request
user_rejected_purchase_request
user_cancelled_purchase_request
notification_sent
notification_failed
escalation_triggered
missing_notification_routing
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
on_call
```

## Deliverables

- Purchase request detail page. **Đã có:** `/purchase-requests/[id]`.
- Submit/approve/reject/cancel actions. **Đã có:** API + UI (Workflows + detail).
- Asset contacts / notification targets viewer. **Đã có:** JSON inspect trên trang chi tiết (đọc từ API Phase 05).
- Escalation policy config hoặc seed dữ liệu org routing. **Đã có:** seed `ELV-CABLE-ESCALATION-01` + block JSON policy trên detail.
- n8n webhook integration. **Đã có:** backend (sau commit).
- Audit log table. **Đã có:** `/audit-logs` + bảng trên detail PR.
- Audit detail by entity. **Đã có:** query filter + link từ detail PR.
- Permission guard cơ bản. **Đã có:** `PHASE5_WRITE_SECRET` (tuỳ chọn, bật trên môi trường shared).

## Tiêu chí hoàn thành

Phase 05 đạt khi:

1. Agent tạo purchase request draft.
2. Người dùng submit request.
3. Hệ thống xác định approver.
4. Hệ thống xác định đúng primary contact và backup contact cho asset/rule.
5. n8n nhận webhook.
6. Approver approve/reject request.
7. Audit log ghi đầy đủ từng bước.
8. UI hiển thị lịch sử thay đổi và người đã/đang được notify.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Agent tự động hóa quá mức | Agent chỉ tạo draft, không submit thay người |
| Thiếu truy vết | Mọi action phải ghi audit log |
| Notification lỗi làm hỏng workflow | Notification failure không rollback dữ liệu chính |
| Sai người phê duyệt | Approval policy phải được cấu hình rõ và audit được |
| Sai người nhận thông báo | Asset owner, primary contact, escalation policy phải được cấu hình rõ và kiểm thử bằng dữ liệu seed |
