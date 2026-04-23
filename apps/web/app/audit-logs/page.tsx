import Link from "next/link";
import { AdminShell } from "../../components/admin-shell";
import { AuditLogTable } from "../../components/audit-log-table";
import { fetchAuditLogsFromServer, getApiHealth } from "../../lib/api";

type Search = {
  entity_type?: string;
  entity_id?: string;
};

export default async function AuditLogsPage({ searchParams }: { searchParams: Promise<Search> }) {
  const sp = await searchParams;
  const health = await getApiHealth();
  const isOnline = health.status === "ok";
  const logs = await fetchAuditLogsFromServer({
    entityType: sp.entity_type,
    entityId: sp.entity_id,
    limit: 200,
  });

  const filterLabel =
    sp.entity_type && sp.entity_id
      ? `${sp.entity_type} / ${sp.entity_id}`
      : sp.entity_type
        ? String(sp.entity_type)
        : "Tất cả (giới hạn 200 bản ghi mới nhất)";

  return (
    <AdminShell
      eyebrow="Audit"
      title="Nhật ký thao tác"
      status={isOnline ? "API online" : "API offline"}
      isOnline={isOnline}
      tag={filterLabel}
    >
      <p className="breadcrumb">
        <Link href="/workflows">← Task / Mua hàng</Link>
      </p>
      <p className="muted-hint">
        Lọc qua query: <code>entity_type</code>, <code>entity_id</code> (ví dụ từ trang chi tiết purchase request).
      </p>
      <section className="admin-section">
        <AuditLogTable logs={logs} />
      </section>
    </AdminShell>
  );
}
