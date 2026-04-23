import { AdminShell } from "../../components/admin-shell";
import { OntologyMap } from "../../components/ontology-map";
import { getDashboardData } from "../../lib/api";

export default async function OntologyPage() {
  const { health, selectedAsset, ontology, purchaseRequests } = await getDashboardData();
  const isOnline = health.status === "ok";

  return (
    <AdminShell
      eyebrow="Ontology graph"
      title="Bản đồ quan hệ dữ liệu"
      status={isOnline ? "API online" : "API offline"}
      isOnline={isOnline}
      tag="Neo4j"
    >
      <section className="admin-section">
        <div className="section-title-row">
          <div>
            <p className="eyebrow">Graph context</p>
            <h2>{selectedAsset?.name ?? "Chưa có asset"}</h2>
          </div>
          <span className="module-tag">Asset / Component / Rule / Manual / Purchase</span>
        </div>
        <OntologyMap asset={selectedAsset} ontology={ontology} purchaseRequests={purchaseRequests} />
      </section>

      <section className="admin-grid two-one">
        <article className="admin-section">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">Ontology source</p>
              <h2>Context trả về từ API</h2>
            </div>
            <span className="module-tag">/api/assets/:id/ontology</span>
          </div>
          <pre className="json-panel">{JSON.stringify(ontology, null, 2)}</pre>
        </article>
        <article className="admin-section">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">Purchase links</p>
              <h2>Request liên quan</h2>
            </div>
            <span className="module-tag">{purchaseRequests.length} request</span>
          </div>
          <div className="list-stack">
            {purchaseRequests.map((request) => (
              <div className="list-item vertical" key={request.id}>
                <strong>{request.status} · {request.final_approver ?? "-"}</strong>
                <span>{request.reason}</span>
              </div>
            ))}
            {!purchaseRequests.length ? <p className="empty-text">Chưa có purchase request.</p> : null}
          </div>
        </article>
      </section>
    </AdminShell>
  );
}
