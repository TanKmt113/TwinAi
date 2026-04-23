import { AdminShell } from "../../components/admin-shell";
import { ReasoningControls } from "../../components/reasoning-controls";
import { getDashboardData } from "../../lib/api";

export default async function OperationsPage() {
  const { health, agentRuns } = await getDashboardData();
  const isOnline = health.status === "ok";
  const latestRun = agentRuns[0];

  return (
    <AdminShell
      eyebrow="Operations"
      title="Điều khiển suy luận"
      status={isOnline ? "API online" : "API offline"}
      isOnline={isOnline}
      tag="Rule Engine"
    >
      <section className="admin-grid two-one">
        <article className="admin-section">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">Rule Engine</p>
              <h2>Chạy reasoning</h2>
            </div>
            <span className="module-tag">R-ELV-CABLE-001</span>
          </div>
          <ReasoningControls />
          {latestRun ? (
            <div className="admin-note">
              <strong>Run mới nhất:</strong>
              <span>{latestRun.run_type} · {latestRun.status}</span>
            </div>
          ) : null}
        </article>

        <article className="admin-section">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">Agent runs</p>
              <h2>Lịch sử chạy</h2>
            </div>
            <span className="module-tag">{agentRuns.length} runs</span>
          </div>
          <div className="list-stack">
            {agentRuns.slice(0, 10).map((run) => (
              <div className="list-item vertical" key={run.id}>
                <strong>{run.run_type}</strong>
                <span>{run.status} · {run.started_at}</span>
              </div>
            ))}
            {!agentRuns.length ? <p className="empty-text">Chưa có agent run.</p> : null}
          </div>
        </article>
      </section>
    </AdminShell>
  );
}
