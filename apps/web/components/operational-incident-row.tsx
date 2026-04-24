"use client";

import Link from "next/link";
import type { OperationalIncident } from "../lib/api";

type OperationalIncidentRowProps = {
  row: OperationalIncident;
  busyId: string | null;
  onAck: (id: string) => void;
  onResolve: (id: string) => void;
};

export function OperationalIncidentRow({ row, busyId, onAck, onResolve }: OperationalIncidentRowProps) {
  const canAck = row.status === "open";
  const canResolve = row.status === "open" || row.status === "acknowledged";
  return (
    <div className="list-item vertical">
      <strong>
        {row.severity} · {row.status} · {row.incident_kind}
      </strong>
      <span>
        {row.asset_code ?? row.asset_id}: {row.title}
      </span>
      {row.description ? <span className="muted-hint">{row.description}</span> : null}
      <div className="workflow-actions">
        <Link
          className="secondary-button link-as-button"
          href={`/audit-logs?entity_type=operational_incident&entity_id=${row.id}`}
        >
          Audit
        </Link>
        {canAck ? (
          <button type="button" className="secondary-button" disabled={busyId === row.id} onClick={() => onAck(row.id)}>
            Tiếp nhận
          </button>
        ) : null}
        {canResolve ? (
          <button
            type="button"
            className="secondary-button"
            disabled={busyId === row.id}
            onClick={() => onResolve(row.id)}
          >
            Đóng sự cố
          </button>
        ) : null}
      </div>
    </div>
  );
}
