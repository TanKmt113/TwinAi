import { getApiHealth } from "../lib/api";

export default async function Home() {
  const health = await getApiHealth();
  const isOnline = health.status === "ok";

  return (
    <main className="page">
      <header className="topbar">
        <div>
          <p className="eyebrow">Phase 01</p>
          <h1>TwinAI Agentic MVP</h1>
        </div>
        <span className={isOnline ? "status" : "status warning"}>
          {isOnline ? "API đang chạy" : "API chưa sẵn sàng"}
        </span>
      </header>

      <section className="grid">
        <article className="card">
          <p className="eyebrow">Backend health</p>
          <h2>{health.service}</h2>
          <p className="muted">Version: {health.version}</p>
          <p className="muted">Status: {health.status}</p>
        </article>

        <article className="card">
          <p className="eyebrow">Foundation services</p>
          <h2>Stack Phase 1</h2>
          <ul className="service-list">
            <li>
              <strong>PostgreSQL</strong>
              <span className="muted">business data + pgvector</span>
            </li>
            <li>
              <strong>Neo4j</strong>
              <span className="muted">Ontology graph</span>
            </li>
            <li>
              <strong>MinIO</strong>
              <span className="muted">manual file storage</span>
            </li>
            <li>
              <strong>n8n</strong>
              <span className="muted">workflow notification</span>
            </li>
          </ul>
        </article>

        <article className="card">
          <p className="eyebrow">Roadmap</p>
          <h2>Phase 2 đã sẵn sàng API lõi</h2>
          <ol className="phase-list">
            <li><code>GET /api/assets</code></li>
            <li><code>GET /api/assets/:id/ontology</code></li>
            <li><code>POST /api/reasoning/run</code></li>
            <li><code>GET /api/inspection-tasks</code></li>
            <li><code>GET /api/purchase-requests</code></li>
          </ol>
        </article>

        <article className="card">
          <p className="eyebrow">MVP focus</p>
          <h2>Use case thang máy</h2>
          <p className="muted">
            Backend đã seed dữ liệu Calidas 1, tạo schema nghiệp vụ, đồng bộ graph Neo4j khi có kết nối
            và chạy rule R-ELV-CABLE-001 qua API reasoning.
          </p>
        </article>
      </section>
    </main>
  );
}
