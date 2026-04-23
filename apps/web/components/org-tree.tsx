import type { ReactNode } from "react";
import type { OrgUnit } from "../lib/api";

type OrgTreeProps = {
  units: OrgUnit[];
};

function childrenByParent(units: OrgUnit[]) {
  const map = new Map<string | null, OrgUnit[]>();
  for (const u of units) {
    const p = u.parent_id ?? null;
    const list = map.get(p) ?? [];
    list.push(u);
    map.set(p, list);
  }
  for (const list of map.values()) {
    list.sort((a, b) => a.sort_order - b.sort_order || a.code.localeCompare(b.code));
  }
  return map;
}

export function OrgTree({ units }: OrgTreeProps) {
  if (!units.length) {
    return <p className="empty-text">Chưa có đơn vị tổ chức (seed API).</p>;
  }

  const byParent = childrenByParent(units);

  function renderLevel(parentId: string | null): ReactNode {
    const nodes = byParent.get(parentId) ?? [];
    if (!nodes.length) {
      return null;
    }
    return (
      <ul className="org-tree-list">
        {nodes.map((u) => (
          <li key={u.id}>
            <div className="org-tree-node">
              <strong>{u.code}</strong>
              <span className="org-tree-name">{u.name}</span>
              <span className="badge neutral">{u.level_kind}</span>
            </div>
            {renderLevel(u.id)}
          </li>
        ))}
      </ul>
    );
  }

  return <div className="org-tree-root">{renderLevel(null)}</div>;
}
