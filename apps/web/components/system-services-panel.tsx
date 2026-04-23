import type { SystemServicesResponse } from "../lib/api";

type Props = {
  data: SystemServicesResponse;
};

function overallLabel(overall: string): string {
  if (overall === "ok") {
    return "Tất cả dịch vụ đang phản hồi";
  }
  if (overall === "critical") {
    return "PostgreSQL không kết nối được — ưu tiên kiểm tra DB";
  }
  if (overall === "degraded") {
    return "Một hoặc nhiều dịch vụ phụ không phản hồi";
  }
  return "Không đọc được trạng thái từ API";
}

export function SystemServicesPanel({ data }: Props) {
  const hasRows = data.services.length > 0;
  const stamp = data.checked_at ? new Date(data.checked_at).toLocaleString("vi-VN") : null;

  return (
    <article className="admin-section system-services-section">
      <div className="section-title-row">
        <div>
          <p className="eyebrow">Hạ tầng</p>
          <h2>Trạng thái máy chủ / dịch vụ</h2>
        </div>
        <span className={`module-tag system-overall system-overall--${data.overall}`}>{data.overall}</span>
      </div>
      <p className="system-services-summary">{overallLabel(data.overall)}</p>
      {stamp ? (
        <p className="system-services-stamp text-muted">
          Cập nhật: {stamp}
        </p>
      ) : null}
      {!hasRows ? (
        <p className="empty-text">Không lấy được dữ liệu health từ backend (kiểm tra URL API hoặc mạng).</p>
      ) : (
        <div className="system-service-grid" role="list">
          {data.services.map((svc) => (
            <div
              className={`system-service-row ${svc.ok ? "ok" : "bad"}${svc.optional ? " optional" : ""}`}
              key={svc.id}
              role="listitem"
            >
              <div className="system-service-main">
                <strong>{svc.label}</strong>
                <span className="system-service-id">{svc.id}</span>
                <p className="system-service-detail">{svc.detail}</p>
              </div>
              <span className={`status-pill ${svc.ok ? "" : "warning"}`}>{svc.ok ? "Hoạt động" : "Lỗi"}</span>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
