import { AdminShell } from "../../components/admin-shell";
import { getDashboardData } from "../../lib/api";

export default async function AssetsPage() {
  const { health, assets, selectedAsset } = await getDashboardData();
  const isOnline = health.status === "ok";

  return (
    <AdminShell
      eyebrow="Asset registry"
      title="Tài sản và linh kiện"
      status={isOnline ? "API online" : "API offline"}
      isOnline={isOnline}
      tag={`${assets.length} tài sản`}
    >
      <section className="admin-grid two-one">
        <article className="admin-section">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">Assets</p>
              <h2>Danh sách thang máy</h2>
            </div>
            <span className="module-tag">Registry</span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Mã tài sản</th>
                  <th>Tên</th>
                  <th>Vị trí</th>
                  <th>Linh kiện</th>
                  <th>Rủi ro</th>
                </tr>
              </thead>
              <tbody>
                {assets.map((asset) => {
                  const riskyComponents = asset.components.filter(
                    (component) => (component.remaining_lifetime_months ?? 999) <= 6,
                  );
                  return (
                    <tr key={asset.id}>
                      <td><strong>{asset.code}</strong></td>
                      <td>{asset.name}</td>
                      <td>{asset.location ?? "-"}</td>
                      <td>{asset.components.length}</td>
                      <td>
                        <span className={riskyComponents.length ? "badge danger" : "badge ok"}>
                          {riskyComponents.length ? `${riskyComponents.length} rủi ro` : "Ổn định"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </article>

        <article className="admin-section">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">Asset detail</p>
              <h2>{selectedAsset?.name ?? "Chưa có asset"}</h2>
            </div>
            <span className="module-tag">{selectedAsset?.code ?? "No asset"}</span>
          </div>
          <div className="list-stack">
            {selectedAsset?.components.map((component) => (
              <div className="list-item vertical" key={component.id}>
                <strong>{component.name}</strong>
                <span>Loại: {component.component_type}</span>
                <span>Tuổi thọ còn lại: {component.remaining_lifetime_months ?? "-"} tháng</span>
                <span>Phụ tùng: {component.spare_part_code ?? "-"}</span>
              </div>
            ))}
          </div>
        </article>
      </section>
    </AdminShell>
  );
}
