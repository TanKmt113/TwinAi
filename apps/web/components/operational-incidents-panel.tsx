"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { Asset, OperationalIncident } from "../lib/api";
import {
  acknowledgeOperationalIncidentFromBrowser,
  resolveOperationalIncidentFromBrowser,
} from "../lib/api";
import { OperationalIncidentReportForm } from "./operational-incident-report-form";
import { OperationalIncidentRow } from "./operational-incident-row";

type OperationalIncidentsPanelProps = {
  incidents: OperationalIncident[];
  assets: Asset[];
};

export function OperationalIncidentsPanel({ incidents, assets }: OperationalIncidentsPanelProps) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function runMutation(id: string, fn: (x: string) => Promise<unknown>) {
    setError(null);
    setBusyId(id);
    try {
      await fn(id);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Thao tác thất bại.");
    } finally {
      setBusyId(null);
    }
  }

  if (!assets.length) {
    return <p className="empty-text">Chưa có tài sản trong registry — không thể gắn sự cố.</p>;
  }

  return (
    <div className="admin-grid one-two">
      <article className="admin-section">
        <div className="section-title-row">
          <div>
            <p className="eyebrow">Báo cáo</p>
            <h2>Ghi nhận sự cố vận hành</h2>
          </div>
        </div>
        <OperationalIncidentReportForm
          assets={assets}
          busy={busyId === "new"}
          onBusyChange={(v) => setBusyId(v ? "new" : null)}
          onSuccess={() => router.refresh()}
          error={error}
          onError={setError}
        />
        <p className="muted-hint" style={{ marginTop: "1rem" }}>
          Sau khi gửi, hệ thống ghi audit và bắn event <code>operational_incident_reported</code> (routing liên hệ theo tài sản).
        </p>
      </article>

      <article className="admin-section">
        <div className="section-title-row">
          <div>
            <p className="eyebrow">Danh sách</p>
            <h2>Sự cố gần đây</h2>
          </div>
          <span className="module-tag">{incidents.length} bản ghi</span>
        </div>
        <div className="list-stack">
          {incidents.map((row) => (
            <OperationalIncidentRow
              key={row.id}
              row={row}
              busyId={busyId}
              onAck={(id) => runMutation(id, acknowledgeOperationalIncidentFromBrowser)}
              onResolve={(id) => runMutation(id, resolveOperationalIncidentFromBrowser)}
            />
          ))}
          {!incidents.length ? <p className="empty-text">Chưa có sự cố nào được ghi nhận.</p> : null}
        </div>
      </article>
    </div>
  );
}
