import { OntologyMap } from "../components/ontology-map";
import { ReasoningControls } from "../components/reasoning-controls";
import { getDashboardData } from "../lib/api";

export default async function Home() {
  const { health, assets, tasks, purchaseRequests, agentRuns, selectedAsset, ontology } = await getDashboardData();
  const isOnline = health.status === "ok";
  const riskyAssets = assets.filter((asset) =>
    asset.components.some((component) => (component.remaining_lifetime_months ?? 999) <= 6),
  );
  const openTasks = tasks.filter((task) => task.status === "open");
  const draftPurchases = purchaseRequests.filter((request) => ["draft", "waiting_for_approval"].includes(request.status));

  return (
    <main className="page">
      <header className="topbar">
        <div>
          <p className="eyebrow">Phase 03</p>
          <h1>Dashboard Ontology thang máy</h1>
        </div>
        <span className={isOnline ? "status" : "status warning"}>
          {isOnline ? "API đang chạy" : "API chưa sẵn sàng"}
        </span>
      </header>

      <section className="metric-grid">
        <Metric title="Tài sản" value={assets.length} detail="thang máy đang theo dõi" />
        <Metric title="Rủi ro" value={riskyAssets.length} detail="asset có linh kiện <= 6 tháng" tone="danger" />
        <Metric title="Task mở" value={openTasks.length} detail="task kiểm tra kỹ thuật" />
        <Metric title="Mua hàng" value={draftPurchases.length} detail="purchase request draft/chờ duyệt" />
      </section>

      <section className="dashboard-grid">
        <article className="card span-2">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Agent controls</p>
              <h2>Chạy Rule Engine</h2>
            </div>
            <span className="muted">Rule: R-ELV-CABLE-001</span>
          </div>
          <ReasoningControls />
        </article>

        <article className="card">
          <p className="eyebrow">Agent runs</p>
          <h2>Lịch sử chạy</h2>
          <div className="list-stack">
            {agentRuns.slice(0, 5).map((run) => (
              <div className="list-item" key={run.id}>
                <strong>{run.run_type}</strong>
                <span>{run.status}</span>
              </div>
            ))}
            {!agentRuns.length ? <p className="empty-text">Chưa có agent run.</p> : null}
          </div>
        </article>
      </section>

      <section className="dashboard-grid">
        <article className="card span-2">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Assets</p>
              <h2>Danh sách thang máy</h2>
            </div>
            <span className="muted">{assets.length} tài sản</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Mã tài sản</th>
                  <th>Tên</th>
                  <th>Vị trí</th>
                  <th>Linh kiện</th>
                  <th>Rủi ro</th>
                </tr>
              </thead>
              <tbody>
                {assets.map((asset) => {
                  const riskyComponents = asset.components.filter(
                    (component) => (component.remaining_lifetime_months ?? 999) <= 6,
                  );
                  return (
                    <tr key={asset.id}>
                      <td><strong>{asset.code}</strong></td>
                      <td>{asset.name}</td>
                      <td>{asset.location ?? "-"}</td>
                      <td>{asset.components.length}</td>
                      <td>
                        <span className={riskyComponents.length ? "badge danger" : "badge ok"}>
                          {riskyComponents.length ? `${riskyComponents.length} rủi ro` : "Ổn định"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </article>

        <article className="card">
          <p className="eyebrow">Asset detail</p>
          <h2>{selectedAsset?.name ?? "Chưa có asset"}</h2>
          <div className="list-stack">
            {selectedAsset?.components.map((component) => (
              <div className="list-item" key={component.id}>
                <strong>{component.name}</strong>
                <span>{component.remaining_lifetime_months ?? "-"} tháng</span>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Ontology map</p>
            <h2>Chuỗi liên kết dữ liệu</h2>
          </div>
          <span className="muted">Asset → Component → Rule → Manual → Purchase → Approver</span>
        </div>
        <OntologyMap asset={selectedAsset} ontology={ontology} purchaseRequests={purchaseRequests} />
      </section>

      <section className="dashboard-grid">
        <article className="card">
          <p className="eyebrow">Inspection tasks</p>
          <h2>Task kiểm tra</h2>
          <div className="list-stack">
            {tasks.map((task) => (
              <div className="list-item vertical" key={task.id}>
                <strong>{task.title}</strong>
                <span>{task.status} · {task.assigned_to ?? "chưa gán"}</span>
              </div>
            ))}
            {!tasks.length ? <p className="empty-text">Chưa có task. Hãy chạy suy luận.</p> : null}
          </div>
        </article>

        <article className="card span-2">
          <p className="eyebrow">Purchase requests</p>
          <h2>Đề xuất mua hàng</h2>
          <div className="list-stack">
            {purchaseRequests.map((request) => (
              <div className="list-item vertical" key={request.id}>
                <strong>{request.status} · Approver: {request.final_approver ?? "-"}</strong>
                <span>{request.reason}</span>
              </div>
            ))}
            {!purchaseRequests.length ? <p className="empty-text">Chưa có purchase request. Hãy chạy suy luận.</p> : null}
          </div>
        </article>
      </section>
    </main>
  );
}

function Metric({ title, value, detail, tone }: { title: string; value: number; detail: string; tone?: "danger" }) {
  return (
    <article className="metric-card">
      <p>{title}</p>
      <strong className={tone === "danger" ? "danger-text" : undefined}>{value}</strong>
      <span>{detail}</span>
    </article>
  );
}

