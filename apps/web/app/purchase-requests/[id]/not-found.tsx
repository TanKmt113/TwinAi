import Link from "next/link";
import { AdminShell } from "../../../components/admin-shell";
import { getApiHealth } from "../../../lib/api";

export default async function PurchaseRequestNotFound() {
  const health = await getApiHealth();
  const isOnline = health.status === "ok";
  return (
    <AdminShell
      eyebrow="Purchase request"
      title="Không tìm thấy"
      status={isOnline ? "API online" : "API offline"}
      isOnline={isOnline}
    >
      <p>Không có purchase request với id này (hoặc API không phản hồi).</p>
      <p>
        <Link href="/workflows">← Quay lại Task / Mua hàng</Link>
      </p>
    </AdminShell>
  );
}
