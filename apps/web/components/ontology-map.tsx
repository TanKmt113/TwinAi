import type { Asset, OntologyContext, PurchaseRequest } from "../lib/api";

type OntologyMapProps = {
  asset: Asset | undefined;
  ontology: OntologyContext;
  purchaseRequests: PurchaseRequest[];
};

export function OntologyMap({ asset, ontology, purchaseRequests }: OntologyMapProps) {
  const component = asset?.components?.[0];
  const purchase = purchaseRequests[0];
  const source = typeof ontology.source === "string" ? ontology.source : "neo4j_or_api_context";
  const manual = firstRecord(ontology.manuals);
  const inventory = firstRecord(ontology.inventory_items);
  const approver = firstRecord(ontology.approvers);

  const nodes: Array<{
    key: string;
    className: string;
    label: string;
    title: string;
    detail: string;
    tone: "asset" | "component" | "rule" | "manual" | "supply" | "purchase" | "person" | "context";
  }> = [
    {
      key: "asset",
      className: "asset",
      label: "ASSET",
      title: asset?.name ?? "Chưa có asset",
      detail: asset?.code ?? "No asset code",
      tone: "asset",
    },
    {
      key: "component",
      className: "component",
      label: "CABLE",
      title: component?.name ?? "Chưa có component",
      detail: `${component?.remaining_lifetime_months ?? "-"} tháng còn lại`,
      tone: "component",
    },
    {
      key: "rule",
      className: "rule",
      label: "RULE",
      title: "R-ELV-CABLE-001",
      detail: "remaining_lifetime <= 6",
      tone: "rule",
    },
    {
      key: "manual",
      className: "manual",
      label: "MANUAL",
      title: textValue(manual, "code") ?? "MAN-ELV-001",
      detail: textValue(manual, "title") ?? "Nguồn kỹ thuật",
      tone: "manual",
    },
    {
      key: "spare",
      className: "spare",
      label: "SPARE",
      title: component?.spare_part_code ?? "Chưa có phụ tùng",
      detail: "phụ tùng thay thế",
      tone: "supply",
    },
    {
      key: "inventory",
      className: "inventory",
      label: "STOCK",
      title: textValue(inventory, "code") ?? component?.spare_part_code ?? "Chưa có tồn kho",
      detail: `quantity = ${textValue(inventory, "quantity_on_hand") ?? "0"}`,
      tone: "supply",
    },
    {
      key: "purchase",
      className: "purchase",
      label: "PURCHASE",
      title: purchase?.status ?? "Chưa tạo request",
      detail: purchase ? `qty ${purchase.quantity_requested}` : "draft sau reasoning",
      tone: "purchase",
    },
    {
      key: "approver",
      className: "approver",
      label: "APPROVER",
      title: purchase?.final_approver ?? textValue(approver, "name") ?? "Chưa xác định",
      detail: purchase?.approval_policy_code ?? "approval policy",
      tone: "person",
    },
    {
      key: "task",
      className: "task",
      label: "TASK",
      title: "Inspection",
      detail: "technical evidence",
      tone: "context",
    },
    {
      key: "risk",
      className: "risk",
      label: "RISK",
      title: "Cable lifetime",
      detail: "5 <= 6 months",
      tone: "component",
    },
  ];

  return (
    <div className="ontology-graph-wrap">
      <div className="graph-toolbar">
        <div className="map-source">Nguồn ontology: {source}</div>
        <div className="graph-legend" aria-label="Graph legend">
          <span><i className="legend-dot active" /> Dữ liệu chính</span>
          <span><i className="legend-dot warn" /> Cần chú ý</span>
          <span><i className="legend-dot danger" /> Rủi ro vận hành</span>
        </div>
      </div>
      <div className="ontology-graph bubble-graph" aria-label="Ontology relationship graph">
        <svg className="graph-lines" viewBox="0 0 1120 390" preserveAspectRatio="none" aria-hidden="true">
          <defs>
            <marker id="arrow" markerHeight="10" markerWidth="10" orient="auto" refX="8" refY="3">
              <path d="M0,0 L0,6 L9,3 z" />
            </marker>
          </defs>
          <path d="M210 150 L320 170" />
          <path d="M430 170 L555 112" markerEnd="url(#arrow)" />
          <path d="M685 112 L790 112" markerEnd="url(#arrow)" />
          <path d="M435 205 L560 254" markerEnd="url(#arrow)" />
          <path d="M675 260 L780 250" markerEnd="url(#arrow)" />
          <path d="M890 242 L950 178" markerEnd="url(#arrow)" />
          <path d="M1005 190 L1028 270" markerEnd="url(#arrow)" />
          <path d="M370 130 L410 72" />
          <path d="M180 178 L95 250" markerEnd="url(#arrow)" />
          <path d="M535 92 L455 64" />
          <path d="M770 132 L710 190" />
          <path d="M760 276 L710 330" />
          <path d="M930 150 L875 75" />
        </svg>
        <div className="graph-group-label asset-group">DIGITAL TWIN</div>
        <div className="graph-group-label knowledge-group">KNOWLEDGE</div>
        <div className="graph-group-label supply-group">SUPPLY</div>
        <div className="graph-group-label workflow-group">WORKFLOW</div>
        {nodes.map((node) => (
          <div className={`graph-node bubble-node ${node.className} ${node.tone}`} key={node.key}>
            <span>{node.label}</span>
            <strong>{node.title}</strong>
            <small>{node.detail}</small>
          </div>
        ))}
        <div className="satellite sat-a" />
        <div className="satellite sat-b" />
        <div className="satellite sat-c" />
        <div className="satellite sat-d" />
      </div>
    </div>
  );
}

function firstRecord(value: unknown): Record<string, unknown> | undefined {
  if (!Array.isArray(value)) {
    return undefined;
  }
  const first = value[0];
  return first && typeof first === "object" ? first as Record<string, unknown> : undefined;
}

function textValue(record: Record<string, unknown> | undefined, key: string): string | undefined {
  const value = record?.[key];
  if (value === undefined || value === null) {
    return undefined;
  }
  return String(value);
}
