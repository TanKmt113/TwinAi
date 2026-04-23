import { AdminShell } from "../../components/admin-shell";
import { ManualChatPanel } from "../../components/manual-chat-panel";
import { getDashboardData } from "../../lib/api";

export default async function ManualsPage() {
  const { health, manuals } = await getDashboardData();
  const isOnline = health.status === "ok";

  return (
    <AdminShell
      eyebrow="Knowledge operations"
      title="Manual, RAG và Chat"
      status={isOnline ? "API online" : "API offline"}
      isOnline={isOnline}
      tag={`${manuals.length} manual`}
    >
      <section className="admin-section">
        <div className="section-title-row">
          <div>
            <p className="eyebrow">Manual library</p>
            <h2>Upload, parse và hỏi đáp</h2>
          </div>
          <span className="module-tag">Rule linked manual</span>
        </div>
        <ManualChatPanel manuals={manuals} />
      </section>
    </AdminShell>
  );
}
