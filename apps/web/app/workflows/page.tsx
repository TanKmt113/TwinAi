import { AdminShell } from "../../components/admin-shell";
import { getDashboardData } from "../../lib/api";

export default async function WorkflowsPage() {
  const { health, tasks, purchaseRequests } = await getDashboardData();
  const isOnline = health.status === "ok";
  const openTasks = tasks.filter((task) => task.status === "open");
  const draftPurchases = purchaseRequests.filter((request) => ["draft", "waiting_for_approval"].includes(request.status));

  return (
    <AdminShell
      eyebrow="Workflow queue"
      title="Task kiểm tra và đề xuất mua hàng"
      status={isOnline ? "API online" : "API offline"}
      isOnline={isOnline}
      tag="Human approval gate"
    >
      <section className="metric-grid">
        <article className="metric-card">
          <p>Task mở</p>
          <strong>{openTasks.length}</strong>
          <span>đang chờ kỹ thuật xử lý</span>
        </article>
        <article className="metric-card">
          <p>Purchase draft</p>
          <strong>{draftPurchases.length}</strong>
          <span>đề xuất chưa hoàn tất phê duyệt</span>
        </article>
      </section>

      <section className="admin-grid one-two">
        <article className="admin-section">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">Inspection tasks</p>
              <h2>Task kiểm tra</h2>
            </div>
            <span className="module-tag">{tasks.length} task</span>
          </div>
          <div className="list-stack">
            {tasks.map((task) => (
              <div className="list-item vertical" key={task.id}>
                <strong>{task.title}</strong>
                <span>{task.status} · {task.assigned_to ?? "chưa gán"}</span>
                <span>{task.description ?? "Không có mô tả"}</span>
              </div>
            ))}
            {!tasks.length ? <p className="empty-text">Chưa có task. Hãy chạy suy luận.</p> : null}
          </div>
        </article>

        <article className="admin-section">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">Purchase requests</p>
              <h2>Đề xuất mua hàng</h2>
            </div>
            <span className="module-tag">{purchaseRequests.length} request</span>
          </div>
          <div className="list-stack">
            {purchaseRequests.map((request) => (
              <div className="list-item vertical" key={request.id}>
                <strong>{request.status} · Approver: {request.final_approver ?? "-"}</strong>
                <span>{request.reason}</span>
                <span>Policy: {request.approval_policy_code ?? "-"}</span>
              </div>
            ))}
            {!purchaseRequests.length ? <p className="empty-text">Chưa có purchase request. Hãy chạy suy luận.</p> : null}
          </div>
        </article>
      </section>
    </AdminShell>
  );
}
