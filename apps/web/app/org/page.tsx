import { AdminShell } from "../../components/admin-shell";
import { OrgTree } from "../../components/org-tree";
import { fetchOrgUnitsFromServer, fetchOrgUsersFromServer, getApiHealth } from "../../lib/api";

export default async function OrganizationPage() {
  const [health, units, users] = await Promise.all([
    getApiHealth(),
    fetchOrgUnitsFromServer(),
    fetchOrgUsersFromServer(),
  ]);
  const isOnline = health.status === "ok";

  return (
    <AdminShell
      eyebrow="Organization"
      title="Cơ cấu tổ chức & người dùng"
      status={isOnline ? "API online" : "API offline"}
      isOnline={isOnline}
      tag={`${units.length} đơn vị · ${users.length} người`}
    >
      <section className="admin-grid one-two">
        <article className="admin-section">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">Org units</p>
              <h2>Cây đơn vị</h2>
            </div>
            <span className="module-tag">PostgreSQL</span>
          </div>
          <p className="muted-hint">Dữ liệu từ <code>GET /api/org/units</code> (cấp: holding → branch → department → team).</p>
          <OrgTree units={units} />
        </article>

        <article className="admin-section">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">Org users</p>
              <h2>Người dùng nội bộ</h2>
            </div>
            <span className="module-tag">role_tags</span>
          </div>
          <p className="muted-hint">Dữ liệu từ <code>GET /api/org/users</code>.</p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Mã</th>
                  <th>Họ tên</th>
                  <th>Đơn vị</th>
                  <th>Quản lý</th>
                  <th>Vai trò</th>
                  <th>Hoạt động</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>
                      <strong>{u.user_code}</strong>
                    </td>
                    <td>
                      {u.full_name}
                      <div className="table-sub">{u.email ?? "—"}</div>
                      <div className="table-sub">{u.job_title ?? ""}</div>
                    </td>
                    <td>
                      {u.org_unit_code ?? "—"}
                      <div className="table-sub">{u.org_unit_name ?? ""}</div>
                    </td>
                    <td>{u.manager_user_code ?? "—"}</td>
                    <td>
                      <span className="tag-list">{u.role_tags.length ? u.role_tags.join(", ") : "—"}</span>
                    </td>
                    <td>
                      <span className={u.is_active ? "badge ok" : "badge danger"}>{u.is_active ? "active" : "off"}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!users.length ? <p className="empty-text">Chưa có người dùng org (seed API).</p> : null}
        </article>
      </section>
    </AdminShell>
  );
}
