# Phase 05: Approval + Org Routing + Notification + Audit

## Mục tiêu

Hoàn thiện vòng vận hành: purchase request được submit, phê duyệt/từ chối, chọn đúng người nhận thông báo/escalation và truy vết đầy đủ.

## Trạng thái triển khai (đồng bộ với code)

- **Purchase lifecycle:** submit / approve / reject / cancel; **phê duyệt 2 cấp** khi `inventory_items.import_required = true` (hàng nhập khẩu): lần approve đầu ghi `first_approved_at` / `first_approved_by`, giữ `waiting_for_approval`; lần hai mới `approved`. Một cấp khi không import.
- **Audit API:** `GET /api/audit-logs` + lọc theo entity.
- **Routing (SQL MVP):** `build_asset_contacts` / `build_rule_notification_targets` trong `apps/api/app/services/routing_context.py` — ưu tiên `asset_contact_assignments`, fallback `org_users.role_tags`; cờ `missing_notification_routing` + audit `missing_notification_routing` khi reasoning tạo task/PR mà thiếu primary/backup.
- **n8n:** `apps/api/app/services/notification_flow.py` — sau mỗi POST webhook ghi audit `notification_sent`, lỗi `notification_failed`, không cấu hình URL `notification_skipped`.
- **Reasoning:** sau `commit`, `dispatch_pending_notifications` — event `inspection_task_created`, `purchase_request_drafted` (payload có asset/component/request).
- **Purchase workflow events n8n:** `purchase_request_waiting_for_approval`, `purchase_request_level1_approved`, `purchase_request_approved`, `purchase_request_rejected`, `purchase_request_cancelled` (payload có `first_*` khi có).
- **Escalation SLA (API):** `POST /api/routing/escalation-check` — so sánh `opened_at` với `acknowledge_minutes` trong policy; `dry_run=false` có thể ghi audit `escalation_triggered`.
- **Neo4j:** `sync_seed_graph` đồng bộ thêm **OrgUnit / OrgUser** và quan hệ `REPORTS_TO` (đơn vị), `BELONGS_TO`, `REPORTS_TO` (quản lý) — xem `apps/api/app/services/neo4j_sync.py`.
- **Chat:** tool context có `asset_routing_contacts`, `routing_guardrails` (thiếu routing → `missing_data`).
- **Auth (MVP):** `POST /api/auth/login` (OrgUser + `password_hash` bcrypt); `AUTH_ENABLED` + `JWT_SECRET`; ghi workflow: header `X-Phase5-Write-Secret` **hoặc** Bearer JWT hợp lệ (`require_phase5_write_access`). Với JWT, approve có kiểm tra role (cấp 1 vs cấp 2) khi gửi kèm Bearer.
- **Web:** `/login`, lưu `twinai_access_token`; proxy forward `Authorization`; `AuthGate` chuyển `/login?next=` khi `NEXT_PUBLIC_REQUIRE_LOGIN` ≠ `false` (mặc định bật tường đăng nhập); sidebar Đăng nhập / Đăng xuất; purchase workflow gửi Bearer nếu có token.
- **DB đã tồn tại (Postgres volume cũ):** `apply_postgres_schema_patches` thêm cột `purchase_requests.first_approved_at`, `first_approved_by`, `org_users.password_hash` nếu thiếu; `backfill_null_org_user_passwords` gán mật khẩu demo `demo` (bcrypt) cho user thiếu hash mỗi lần bootstrap.

## Điều kiện bắt đầu Phase 05 (từ Phase 04)

Phase 04 được coi là đủ để chuyển sang Phase 05 khi: manual upload+parse+search hoạt động, chat trả lời có căn cứ với LLM hoặc fallback, và health/deploy ổn định. Chi tiết tồn đọng nhẹ Phase 04 xem `phase/04-manual-rag-chat.md` mục “Trạng thái hoàn thành vs tồn đọng”.

## Phạm vi

Phase này xử lý:

- Purchase request lifecycle (kể cả 2 cấp duyệt import).
- Approval flow + RBAC JWT tùy chọn.
- Org routing cho asset/rule/sự cố (SQL + seed; graph org trên Neo4j).
- Notification qua n8n + audit trạng thái gửi.
- Audit log viewer.
- Kiểm tra SLA escalate (endpoint).

## Purchase request lifecycle

```text
draft
  -> waiting_for_approval   (có thể: sau approve cấp 1 vẫn ở trạng thái này nếu import_required)
  -> approved | rejected | cancelled
```

Cột bổ sung: `first_approved_at`, `first_approved_by` (nullable).

## Approval logic

```text
Nếu mua phụ tùng nhập khẩu (import_required)
  -> phê duyệt cấp 1: role department_head / team_lead / approver / branch_head (khi dùng JWT + AUTH_ENABLED)
  -> phê duyệt cuối: final_approver / executive
Nếu không import
  -> một lần approve -> approved
```

Khi không bật JWT, body `WorkflowActorBody` vẫn ghi `actor_id` cho audit; RBAC role chỉ áp khi có Bearer hợp lệ.

## Org routing và escalation logic

Ontology MVP (trả lời bằng dữ liệu SQL + policy seed):

```text
Asset này thuộc bộ phận nào?        -> department_owner + org (tùy seed)
Primary / Backup contact?            -> asset_contact_assignments rồi fallback role_tags
SLA acknowledge / escalate?          -> EscalationPolicy.config_json + POST /api/routing/escalation-check
```

**Lưu ý:** `routing_context` **không** gọi Neo4j để suy luận người nhận; Neo4j dùng đồng bộ và ontology map khác (chat/API `.../ontology`).

## API (backend)

**Org (đọc):**

```text
GET  /api/org/units
GET  /api/org/users
```

**Purchase + routing + audit:**

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
POST /api/routing/escalation-check

GET  /api/audit-logs
GET  /api/audit-logs?entity_type=purchase_request&entity_id={id}
```

**Auth (khi AUTH_ENABLED=true):**

```text
POST /api/auth/login
```

**Bảo vệ POST workflow:** `require_phase5_write_access` — khớp `X-Phase5-Write-Secret` nếu cấu hình, hoặc JWT hợp lệ khi `AUTH_ENABLED`.

## n8n notification

Envelope gửi đi: `{ "event": "<tên_event>", "payload": { ... } }` (xem `post_n8n_workflow_event`).

Backend gọi webhook (best-effort, không rollback nghiệp vụ chính) khi gồm:

- Tạo task kiểm tra (reasoning): `inspection_task_created`.
- Tạo purchase draft (reasoning): `purchase_request_drafted`.
- Submit / cấp 1 / duyệt cuối / reject / cancel (purchase workflow): các event `purchase_request_*` tương ứng.

Payload purchase có thể gồm: `request_id`, `status`, `reason`, `approval_policy_code`, `final_approver`, `first_approved_at`, `first_approved_by`, mã asset/component/inventory (tùy bước).

## Agentic action flow

```text
Reasoning: rule approved + condition_json khớp component
  -> Tạo inspection task (và audit); nếu thiếu primary/backup -> audit missing_notification_routing
  -> Đủ điều kiện tồn kho/lead time -> purchase request draft + audit tương tự
  -> commit DB -> dispatch n8n (task + draft)
Purchase workflow (người): submit / approve (1 hoặc 2 bước) / reject / cancel -> n8n + audit
Notification helper -> notification_sent | notification_failed | notification_skipped
```

## Guardrail

```text
Agent chỉ tạo draft; không submit/approve/reject thay người (trừ luồng nghiệp vụ được định nghĩa rõ sau này).
Notification failure không rollback transaction nghiệp vụ chính.
Thiếu primary hoặc backup contact -> missing_notification_routing + cờ trong API contacts/chat.
```

## Audit log (action điển hình)

```text
agent_created_inspection_task
agent_created_purchase_request
missing_notification_routing
user_submitted_purchase_request
user_approved_purchase_request_level1
user_approved_purchase_request
user_rejected_purchase_request
user_cancelled_purchase_request
notification_sent
notification_failed
notification_skipped
escalation_triggered
```

## Role MVP

Trên `org_users.role_tags` (seed demo): `technician`, `field`, `department_head`, `team_lead`, `branch_head`, `final_approver`, `executive`, … — dùng cho routing fallback và RBAC approve khi JWT bật. Danh sách role “tài liệu” dài hơn (`admin`, `viewer`, …) có thể bổ sung dần vào seed/API.

## Deliverables

- Purchase detail `/purchase-requests/[id]` + tóm tắt “ai được notify”, cảnh báo `missing_notification_routing`, hiển thị phê duyệt cấp 1 nếu có.
- Workflows + audit-logs.
- n8n + audit notification.
- JWT + login web + tường đăng nhập tùy `NEXT_PUBLIC_REQUIRE_LOGIN`.
- Patch schema Postgres + backfill mật khẩu demo cho org user thiếu hash.
- Neo4j: đồng bộ org trong `sync_seed_graph`.

## Tiêu chí hoàn thành

1. Agent tạo draft + task; n8n/audit có thể kiểm tra trên môi trường có cấu hình `N8N_WEBHOOK_URL`.
2. Người submit; với import — hai bước approve đúng nghiệp vụ.
3. Xác định approver/policy từ dữ liệu (rule + inventory).
4. Primary/backup từ assignments + fallback; API escalation-check minh họa SLA.
5. Audit đủ loại sự kiện chính (kể cả notification + thiếu routing).
6. UI + chat phản ánh routing/guardrail cơ bản.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Agent tự động hóa quá mức | Agent chỉ draft; người submit/duyệt |
| Thiếu truy vết | Audit + viewer |
| Notification lỗi | Không rollback; audit `notification_failed` |
| Schema DB cũ | `apply_postgres_schema_patches` + redeploy API |
| User không đăng nhập được | `password_hash` backfill + `AUTH_ENABLED` / `JWT_SECRET` |
| Sai người nhận | Cấu hình `asset_contact_assignments` + n8n map payload |

## File tham chiếu nhanh

| Khu vực | File |
|---------|------|
| Routing SQL | `apps/api/app/services/routing_context.py` |
| Notification + audit | `apps/api/app/services/notification_flow.py`, `n8n_webhook.py` |
| Purchase + 2 cấp | `apps/api/app/services/purchase_workflow.py` |
| Reasoning + notify sau commit | `apps/api/app/services/reasoning.py` |
| Schema patch / bootstrap | `apps/api/app/services/schema_patches.py`, `bootstrap.py`, `seed.py` |
| Auth | `apps/api/app/api/auth.py`, `deps.py`, `core/security.py` |
| Escalation API | `apps/api/app/api/phase5_routing.py` |
| Neo4j org | `apps/api/app/services/neo4j_sync.py` |
| Web login / gate | `apps/web/app/login/page.tsx`, `components/auth-gate.tsx`, `components/admin-shell.tsx`, `lib/api.ts` |
