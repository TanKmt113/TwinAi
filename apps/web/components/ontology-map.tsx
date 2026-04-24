import type { Asset, OntologyContext, PurchaseRequest } from "../lib/api";

type OntologyMapProps = {
  asset: Asset | undefined;
  ontology: OntologyContext;
  purchaseRequests: PurchaseRequest[];
};

type DrmNode = {
  id: string;
  labelEn: string;
  labelVi: string;
  detail: string;
  emphasis?: boolean;
};

type DrmCluster = {
  id: "people" | "application" | "process" | "infrastructure";
  titleEn: string;
  titleVi: string;
  nodes: DrmNode[];
};

/**
 * Bốn cạnh của lưới 2×2 (giống ảnh): trên / dưới / trái / phải — chỉ nằm trong khe giữa các ô.
 * viewBox 1000×520 khớp .drm-canvas khi preserveAspectRatio="none".
 */
const DRM_SVG_EDGES: Array<{ d: string; arrow?: boolean }> = [
  { d: "M 382 132 L 618 132", arrow: true },
  { d: "M 382 388 L 618 388", arrow: true },
  { d: "M 252 248 L 252 272", arrow: true },
  { d: "M 748 248 L 748 272", arrow: true },
];

export function OntologyMap({ asset, ontology, purchaseRequests }: OntologyMapProps) {
  const source = typeof ontology.source === "string" ? ontology.source : "neo4j_or_api_context";
  const clusters = buildDrmClusters({ asset, ontology, purchaseRequests });

  return (
    <div className="ontology-graph-wrap">
      <div className="graph-toolbar">
        <div className="map-source">Nguồn ontology: {source}</div>
        <div className="drm-legend" aria-label="Cụm dữ liệu">
          <span>
            <i className="drm-legend-swatch drm-legend-swatch--people" /> People
          </span>
          <span>
            <i className="drm-legend-swatch drm-legend-swatch--application" /> Application
          </span>
          <span>
            <i className="drm-legend-swatch drm-legend-swatch--process" /> Process
          </span>
          <span>
            <i className="drm-legend-swatch drm-legend-swatch--infrastructure" /> Infrastructure
          </span>
        </div>
      </div>

      <div className="drm-canvas" role="img" aria-label="Bản đồ quan hệ: People, Application, Process, Infrastructure">
        <svg className="drm-edges-svg" viewBox="0 0 1000 520" preserveAspectRatio="none" aria-hidden="true">
          <defs>
            <marker id="drm-arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
              <path d="M0,0 L0,6 L9,3 z" fill="#6b7c86" />
            </marker>
          </defs>
          {DRM_SVG_EDGES.map((edge, i) => (
            <path key={i} d={edge.d} className="drm-edge" markerEnd={edge.arrow ? "url(#drm-arrowhead)" : undefined} />
          ))}
        </svg>

        <div className="drm-cluster-grid">
          {clusters.map((c) => (
            <section className={`drm-cluster drm-cluster--${c.id}`} key={c.id} aria-label={c.titleEn}>
              <header className="drm-cluster-head">
                <h3 className="drm-cluster-title">{c.titleEn}</h3>
                <p className="drm-cluster-sub">{c.titleVi}</p>
              </header>
              <ul className="drm-node-list">
                {c.nodes.map((n) => (
                  <li className={n.emphasis ? "drm-node drm-node--emphasis" : "drm-node"} key={n.id}>
                    <span className="drm-node-en">{n.labelEn}</span>
                    <span className="drm-node-vi">{n.labelVi}</span>
                    <span className="drm-node-detail">{n.detail}</span>
                  </li>
                ))}
              </ul>
              <div className="drm-satellites" aria-hidden="true">
                <span />
                <span />
              </div>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}

function buildDrmClusters(ctx: OntologyMapProps): DrmCluster[] {
  const { asset, ontology, purchaseRequests } = ctx;
  const component = asset?.components?.[0];
  const purchase = purchaseRequests[0];
  const manual = firstRecord(ontology.manuals);
  const inventory = firstRecord(ontology.inventory_items);
  const approver = firstRecord(ontology.approvers);

  return [
    {
      id: "people",
      titleEn: "PEOPLE",
      titleVi: "Người & tổ chức",
      nodes: [
        {
          id: "org",
          labelEn: "ORGANIZATION",
          labelVi: "Tổ chức",
          detail: textValue(approver, "org_unit_name") ?? "OrgUnit / user (API /org)",
        },
        {
          id: "approval",
          labelEn: "APPROVAL",
          labelVi: "Phê duyệt",
          detail: purchase?.final_approver ?? textValue(approver, "name") ?? "Policy & approver chain",
        },
        {
          id: "ops",
          labelEn: "OPERATIONS",
          labelVi: "Vận hành",
          detail: "Điều hành thang · báo sự cố vận hành",
        },
        {
          id: "routing",
          labelEn: "ROUTING",
          labelVi: "Liên hệ & leo thang",
          detail: "Notification routing · escalation (Phase 5)",
        },
      ],
    },
    {
      id: "application",
      titleEn: "APPLICATION",
      titleVi: "Ứng dụng & tích hợp",
      nodes: [
        {
          id: "platform",
          labelEn: "PLATFORM",
          labelVi: "TwinAI core",
          detail: "FastAPI + Next.js admin",
          emphasis: true,
        },
        {
          id: "n8n",
          labelEn: "N8N",
          labelVi: "Tự động hoá",
          detail: "Webhook · workflow đồng bộ thông báo",
        },
        {
          id: "rag",
          labelEn: "MANUAL / RAG",
          labelVi: "Tri thức",
          detail: textValue(manual, "title") ?? textValue(manual, "code") ?? "Manual chunks & chat",
        },
      ],
    },
    {
      id: "process",
      titleEn: "PROCESS",
      titleVi: "Quy trình & quy tắc",
      nodes: [
        {
          id: "rules",
          labelEn: "RULE ENGINE",
          labelVi: "Quy tắc",
          detail: "R-ELV-CABLE-001 · lifetime & evidence",
        },
        {
          id: "purchase",
          labelEn: "PURCHASE WORKFLOW",
          labelVi: "Mua hàng",
          detail: purchase ? `${purchase.status} · qty ${purchase.quantity_requested}` : "Draft / approval gate",
        },
        {
          id: "incident",
          labelEn: "INCIDENT LIFECYCLE",
          labelVi: "Sự cố vận hành",
          detail: "open → acknowledged → resolved",
        },
        {
          id: "audit",
          labelEn: "AUDIT",
          labelVi: "Minh bạch",
          detail: "Audit log · notification_sent",
        },
      ],
    },
    {
      id: "infrastructure",
      titleEn: "INFRASTRUCTURE",
      titleVi: "Tài sản & lưu trữ",
      nodes: [
        {
          id: "asset",
          labelEn: "ASSET",
          labelVi: "Thang / tài sản",
          detail: asset ? `${asset.code} · ${asset.name}` : "Chưa chọn asset",
        },
        {
          id: "component",
          labelEn: "COMPONENT",
          labelVi: "Linh kiện",
          detail: component ? `${component.name} · ${component.remaining_lifetime_months ?? "?"} tháng` : "Cable / cabin…",
        },
        {
          id: "db",
          labelEn: "POSTGRES",
          labelVi: "CSDL quan hệ",
          detail: "Asset · incident · purchase · audit",
        },
        {
          id: "stock",
          labelEn: "INVENTORY",
          labelVi: "Tồn kho",
          detail: `SL ${textValue(inventory, "quantity_on_hand") ?? "0"} · ${textValue(inventory, "code") ?? component?.spare_part_code ?? "spare"}`,
        },
      ],
    },
  ];
}

function firstRecord(value: unknown): Record<string, unknown> | undefined {
  if (!Array.isArray(value)) {
    return undefined;
  }
  const first = value[0];
  return first && typeof first === "object" ? (first as Record<string, unknown>) : undefined;
}

function textValue(record: Record<string, unknown> | undefined, key: string): string | undefined {
  const value = record?.[key];
  if (value === undefined || value === null) {
    return undefined;
  }
  return String(value);
}
