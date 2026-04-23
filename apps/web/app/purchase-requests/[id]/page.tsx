import Link from "next/link";
import { notFound } from "next/navigation";
import { AdminShell } from "../../../components/admin-shell";
import { AuditLogTable } from "../../../components/audit-log-table";
import { PurchaseWorkflowActions } from "../../../components/purchase-workflow-actions";
import {
  fetchAssetContactsFromServer,
  fetchAuditLogsFromServer,
  fetchEscalationPolicyFromServer,
  fetchPurchaseRequestDetailFromServer,
  fetchRuleNotificationTargetsFromServer,
  getApiHealth,
} from "../../../lib/api";

type PageProps = {
  params: Promise<{ id: string }>;
};

function JsonCard({ eyebrow, title, data }: { eyebrow: string; title: string; data: unknown }) {
  return (
    <article className="admin-section">
      <div className="section-title-row">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
        </div>
      </div>
      <pre className="json-block">{JSON.stringify(data, null, 2)}</pre>
    </article>
  );
}

export default async function PurchaseRequestDetailPage({ params }: PageProps) {
  const { id } = await params;
  const health = await getApiHealth();
  const isOnline = health.status === "ok";
  const detail = await fetchPurchaseRequestDetailFromServer(id);
  if (!detail) {
    notFound();
  }

  const [logs, contacts, ruleTargets] = await Promise.all([
    fetchAuditLogsFromServer({ entityType: "purchase_request", entityId: detail.id, limit: 120 }),
    detail.asset_id ? fetchAssetContactsFromServer(detail.asset_id) : Promise.resolve(null),
    detail.rule_id ? fetchRuleNotificationTargetsFromServer(detail.rule_id) : Promise.resolve(null),
  ]);

  const policyCode = contacts?.escalation_policy_code ?? ruleTargets?.escalation_policy?.code ?? null;
  const policyDetail = policyCode ? await fetchEscalationPolicyFromServer(policyCode) : null;

  return (
    <AdminShell
      eyebrow="Purchase request"
      title={`Đề xuất · ${detail.asset_code ?? detail.id.slice(0, 8)}`}
      status={isOnline ? "API online" : "API offline"}
      isOnline={isOnline}
      tag={detail.status}
    >
      <p className="breadcrumb">
        <Link href="/workflows">← Task / Mua hàng</Link>
        {" · "}
        <Link href={`/audit-logs?entity_type=purchase_request&entity_id=${encodeURIComponent(detail.id)}`}>Audit theo entity</Link>
      </p>

      <section className="admin-grid one-two">
        <article className="admin-section">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">Tóm tắt</p>
              <h2>Trạng thái & chính sách</h2>
            </div>
          </div>
          <div className="list-stack">
            <div className="list-item vertical">
              <strong>Status</strong>
              <span>{detail.status}</span>
            </div>
            <div className="list-item vertical">
              <strong>Lý do</strong>
              <span>{detail.reason}</span>
            </div>
            <div className="list-item vertical">
              <strong>Số lượng · Policy · Approver</strong>
              <span>
                {detail.quantity_requested} · {detail.approval_policy_code ?? "—"} · {detail.final_approver ?? "—"}
              </span>
            </div>
            <div className="list-item vertical">
              <strong>Component · Inventory · Rule</strong>
              <span>
                {detail.component_code ?? detail.component_id} · {detail.inventory_item_id}
                {detail.rule_id ? ` · rule ${detail.rule_id.slice(0, 8)}…` : ""}
              </span>
            </div>
          </div>
          <PurchaseWorkflowActions requestId={detail.id} status={detail.status} />
        </article>

        <article className="admin-section">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">Audit</p>
              <h2>Lịch sử theo purchase request</h2>
            </div>
          </div>
          <AuditLogTable logs={logs} />
        </article>
      </section>

      <section className="admin-grid one-two">
        {contacts ? (
          <JsonCard eyebrow="Asset" title="Liên hệ & escalation gợi ý (org routing MVP)" data={contacts} />
        ) : null}
        {ruleTargets ? <JsonCard eyebrow="Rule" title="Notification targets theo rule" data={ruleTargets} /> : null}
      </section>

      {policyDetail ? (
        <section className="admin-grid">
          <JsonCard eyebrow="Policy" title="Escalation policy (chi tiết)" data={policyDetail} />
        </section>
      ) : null}
    </AdminShell>
  );
}
