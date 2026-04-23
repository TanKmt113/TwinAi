"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  approvePurchaseRequestFromBrowser,
  cancelPurchaseRequestFromBrowser,
  rejectPurchaseRequestFromBrowser,
  submitPurchaseRequestFromBrowser,
} from "../lib/api";

type PurchaseWorkflowActionsProps = {
  requestId: string;
  status: string;
};

export function PurchaseWorkflowActions({ requestId, status }: PurchaseWorkflowActionsProps) {
  const router = useRouter();
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const body = { actor_type: "user" as const, actor_id: "workflow_ui", note: note.trim() || null };
  const canSubmit = status === "draft";
  const canApproveReject = status === "waiting_for_approval";
  const canCancel = status === "draft" || status === "waiting_for_approval";
  const showNote = canSubmit || canApproveReject || canCancel;

  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await fn();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Thao tác thất bại.");
    } finally {
      setBusy(false);
    }
  }

  if (!canSubmit && !canApproveReject && !canCancel) {
    return null;
  }

  return (
    <div className="workflow-actions-block">
      {error ? <p className="error-text">{error}</p> : null}
      {showNote ? (
        <label className="workflow-note">
          <span>Ghi chú (tuỳ chọn)</span>
          <input
            type="text"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            disabled={busy}
            placeholder="Ví dụ: đã kiểm tra tồn kho"
          />
        </label>
      ) : null}
      <div className="workflow-actions">
        {canSubmit ? (
          <button className="primary-button" type="button" disabled={busy} onClick={() => run(() => submitPurchaseRequestFromBrowser(requestId, body))}>
            Gửi duyệt
          </button>
        ) : null}
        {canApproveReject ? (
          <>
            <button className="primary-button" type="button" disabled={busy} onClick={() => run(() => approvePurchaseRequestFromBrowser(requestId, body))}>
              Phê duyệt
            </button>
            <button className="secondary-button" type="button" disabled={busy} onClick={() => run(() => rejectPurchaseRequestFromBrowser(requestId, body))}>
              Từ chối
            </button>
          </>
        ) : null}
        {canCancel ? (
          <button className="secondary-button" type="button" disabled={busy} onClick={() => run(() => cancelPurchaseRequestFromBrowser(requestId, body))}>
            Huỷ đề xuất
          </button>
        ) : null}
      </div>
    </div>
  );
}
