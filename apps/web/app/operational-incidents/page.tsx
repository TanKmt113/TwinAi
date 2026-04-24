import Link from "next/link";
import { AdminShell } from "../../components/admin-shell";
import { OperationalIncidentsPanel } from "../../components/operational-incidents-panel";
import { fetchOperationalIncidentsFromServer, getApiHealth, getDashboardData } from "../../lib/api";

export default async function OperationalIncidentsPage() {
  const [health, { assets }, incidents] = await Promise.all([
    getApiHealth(),
    getDashboardData(),
    fetchOperationalIncidentsFromServer({ limit: 200 }),
  ]);
  const isOnline = health.status === "ok";
  const openCount = incidents.filter((i) => i.status === "open").length;

  return (
    <AdminShell
      eyebrow="Phase 5 · vận hành"
      title="Sự cố vận hành"
      status={isOnline ? "API online" : "API offline"}
      isOnline={isOnline}
      tag={`${openCount} đang mở`}
    >
      <p className="breadcrumb">
        <Link href="/workflows">← Task / Mua hàng</Link>
        {" · "}
        <Link href="/operations">Vận hành</Link>
      </p>
      <OperationalIncidentsPanel incidents={incidents} assets={assets} />
    </AdminShell>
  );
}
