import { AdminShell } from "../components/admin-shell";
import { MetricCard } from "../components/metric-card";
import { SystemServicesPanel } from "../components/system-services-panel";
import { getDashboardData } from "../lib/api";

export default async function OverviewPage() {
  const { health, systemServices, assets, tasks, purchaseRequests, agentRuns, manuals, selectedAsset } =
    await getDashboardData();
  const isOnline = health.status === "ok";
  const infraSummary =
    systemServices.overall === "ok"
      ? "Hạ tầng OK"
      : systemServices.overall === "critical"
        ? "Hạ tầng: lỗi database"
        : systemServices.overall === "degraded"
          ? "Hạ tầng: cảnh báo"
          : "Hạ tầng: không đọc được";
  const headerStatus = `${isOnline ? "API online" : "API offline"} · ${infraSummary}`;
  const riskyAssets = assets.filter((asset) =>
    asset.components.some((component) => (component.remaining_lifetime_months ?? 999) <= 6),
  );
  const openTasks = tasks.filter((task) => task.status === "open");
  const draftPurchases = purchaseRequests.filter((request) => ["draft", "waiting_for_approval"].includes(request.status));
  const latestRun = agentRuns[0];

  return (
    <AdminShell
      eyebrow="Overview"
      title="Tổng quan vận hành"
      status={headerStatus}
      isOnline={isOnline}
      tag="Phase 04+"
    >
      <SystemServicesPanel data={systemServices} />

      <section className="metric-grid" aria-label="KPI overview">
        <MetricCard title="Tài sản" value={assets.length} detail="thang máy đang theo dõi" />
        <MetricCard title="Rủi ro" value={riskyAssets.length} detail="asset có linh kiện <= 6 tháng" tone="danger" />
        <MetricCard title="Task mở" value={openTasks.length} detail="task kiểm tra kỹ thuật" />
        <MetricCard title="Mua hàng" value={draftPurchases.length} detail="draft/chờ duyệt" />
      </section>

      <section className="admin-grid two-one">
        <article className="admin-section">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">Asset snapshot</p>
              <h2>{selectedAsset?.name ?? "Chưa có asset"}</h2>
            </div>
            <span className="module-tag">{selectedAsset?.code ?? "No asset"}</span>
          </div>
          <div className="list-stack">
            {selectedAsset?.components.map((component) => (
              <div className="list-item" key={component.id}>
                <strong>{component.name}</strong>
                <span>{component.remaining_lifetime_months ?? "-"} tháng còn lại</span>
              </div>
            ))}
            {!selectedAsset ? <p className="empty-text">Chưa có dữ liệu tài sản.</p> : null}
          </div>
        </article>

        <article className="admin-section">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">System queues</p>
              <h2>Hàng chờ xử lý</h2>
            </div>
            <span className="module-tag">{manuals.length} manual</span>
          </div>
          <div className="status-stack">
            <div><strong>Agent run mới nhất</strong><span>{latestRun ? `${latestRun.run_type} · ${latestRun.status}` : "Chưa có"}</span></div>
            <div><strong>Task mở</strong><span>{openTasks.length}</span></div>
            <div><strong>Purchase draft/chờ duyệt</strong><span>{draftPurchases.length}</span></div>
          </div>
        </article>
      </section>
    </AdminShell>
  );
}
