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
          <h2>Thứ tự phát triển</h2>
          <ol className="phase-list">
            <li>Nền tảng kiến trúc.</li>
            <li>Data + Neo4j + Rule Engine.</li>
            <li>Dashboard + Ontology Map.</li>
            <li>Manual + RAG + Chat.</li>
            <li>Approval + Notification + Audit.</li>
          </ol>
        </article>

        <article className="card">
          <p className="eyebrow">MVP focus</p>
          <h2>Use case thang máy</h2>
          <p className="muted">
            Phase 1 chỉ dựng nền. Phase 2 sẽ seed dữ liệu Calidas 1, tạo graph Neo4j và chạy rule
            R-ELV-CABLE-001.
          </p>
        </article>
      </section>
    </main>
  );
}

