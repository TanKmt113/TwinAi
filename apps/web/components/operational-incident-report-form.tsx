"use client";

import { type FormEvent, useState } from "react";
import type { Asset } from "../lib/api";
import { reportOperationalIncidentFromBrowser } from "../lib/api";

const KIND_OPTIONS: { value: string; label: string }[] = [
  { value: "door_fault", label: "Lỗi cửa" },
  { value: "elevator_trap", label: "Kẹt cabin / mắc kẹt" },
  { value: "vibration", label: "Rung bất thường" },
  { value: "power_loss", label: "Mất điện / nguồn" },
  { value: "unusual_noise", label: "Tiếng ồn lạ" },
  { value: "overspeed", label: "Quá tốc" },
  { value: "controller_fault", label: "Lỗi bộ điều khiển" },
  { value: "other", label: "Khác" },
];

type OperationalIncidentReportFormProps = {
  assets: Asset[];
  busy: boolean;
  onBusyChange: (v: boolean) => void;
  onSuccess: () => void;
  error: string | null;
  onError: (msg: string | null) => void;
};

export function OperationalIncidentReportForm({
  assets,
  busy,
  onBusyChange,
  onSuccess,
  error,
  onError,
}: OperationalIncidentReportFormProps) {
  const [assetId, setAssetId] = useState(assets[0]?.id ?? "");
  const [kind, setKind] = useState("elevator_trap");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState("warning");

  async function onReport(ev: FormEvent) {
    ev.preventDefault();
    onError(null);
    if (!assetId || !title.trim()) {
      onError("Chọn tài sản và nhập tiêu đề.");
      return;
    }
    onBusyChange(true);
    try {
      await reportOperationalIncidentFromBrowser({
        asset_id: assetId,
        incident_kind: kind,
        title: title.trim(),
        description: description.trim() || null,
        severity,
      });
      setTitle("");
      setDescription("");
      onSuccess();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Không gửi được báo cáo.");
    } finally {
      onBusyChange(false);
    }
  }

  return (
    <>
      {error ? <p className="status warning">{error}</p> : null}
      <form className="form-stack" onSubmit={onReport}>
        <label>
          Tài sản
          <select value={assetId} onChange={(e) => setAssetId(e.target.value)}>
            {assets.map((a) => (
              <option key={a.id} value={a.id}>
                {a.code} — {a.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Loại sự cố
          <select value={kind} onChange={(e) => setKind(e.target.value)}>
            {KIND_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Mức độ
          <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
            <option value="info">info</option>
            <option value="warning">warning</option>
            <option value="critical">critical</option>
          </select>
        </label>
        <label>
          Tiêu đề
          <input value={title} onChange={(e) => setTitle(e.target.value)} required minLength={3} />
        </label>
        <label>
          Mô tả (tuỳ chọn)
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
        </label>
        <button type="submit" className="primary-button" disabled={busy}>
          {busy ? "Đang gửi…" : "Báo sự cố & gửi thông báo"}
        </button>
      </form>
    </>
  );
}
