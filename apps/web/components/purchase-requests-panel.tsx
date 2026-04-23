"use client";

import Link from "next/link";
import { useState } from "react";
import type { PurchaseRequest } from "../lib/api";
import { PurchaseWorkflowActions } from "./purchase-workflow-actions";

type PurchaseRequestsPanelProps = {
  requests: PurchaseRequest[];
};

export function PurchaseRequestsPanel({ requests }: PurchaseRequestsPanelProps) {
  const [openId, setOpenId] = useState<string | null>(null);

  return (
    <div className="list-stack">
      {requests.map((request) => (
        <div className="list-item vertical" key={request.id}>
          <strong>
            {request.status} · Approver: {request.final_approver ?? "-"}
          </strong>
          <span>{request.reason}</span>
          <span>
            Policy: {request.approval_policy_code ?? "-"} · Qty: {request.quantity_requested}
          </span>
          <div className="workflow-actions">
            <Link className="secondary-button link-as-button" href={`/purchase-requests/${request.id}`}>
              Chi tiết & audit
            </Link>
            <button
              className="secondary-button"
              type="button"
              onClick={() => setOpenId((v) => (v === request.id ? null : request.id))}
            >
              {openId === request.id ? "Ẩn thao tác" : "Thao tác nhanh"}
            </button>
          </div>
          {openId === request.id ? <PurchaseWorkflowActions requestId={request.id} status={request.status} /> : null}
        </div>
      ))}
      {!requests.length ? <p className="empty-text">Chưa có purchase request. Hãy chạy suy luận.</p> : null}
    </div>
  );
}
