import type { AuditLogEntry } from "../lib/api";

type AuditLogTableProps = {
  logs: AuditLogEntry[];
};

export function AuditLogTable({ logs }: AuditLogTableProps) {
  if (!logs.length) {
    return <p className="empty-text">Chưa có bản ghi audit.</p>;
  }

  return (
    <div className="table-scroll">
      <table className="audit-table">
        <thead>
          <tr>
            <th>Thời điểm</th>
            <th>Hành động</th>
            <th>Actor</th>
            <th>Lý do / ghi chú</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((row) => (
            <tr key={row.id}>
              <td>{row.created_at}</td>
              <td>{row.action}</td>
              <td>
                {row.actor_type}
                {row.actor_id ? ` · ${row.actor_id}` : ""}
              </td>
              <td>{row.reason ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
