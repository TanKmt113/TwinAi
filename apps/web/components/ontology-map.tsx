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
    tone: "active" | "warn" | "danger" | "neutral";
  }> = [
    {
      key: "asset",
      className: "asset",
      label: "Asset",
      title: asset?.name ?? "Chưa có asset",
      detail: asset?.code ?? "No asset code",
      tone: "active",
    },
    {
      key: "component",
      className: "component",
      label: "Component",
      title: component?.name ?? "Chưa có component",
      detail: `${component?.remaining_lifetime_months ?? "-"} tháng còn lại`,
      tone: "warn",
    },
    {
      key: "rule",
      className: "rule",
      label: "Rule",
      title: "R-ELV-CABLE-001",
      detail: "remaining_lifetime <= 6",
      tone: "active",
    },
    {
      key: "manual",
      className: "manual",
      label: "Manual",
      title: textValue(manual, "code") ?? "MAN-ELV-001",
      detail: textValue(manual, "title") ?? "Nguồn kỹ thuật",
      tone: "active",
    },
    {
      key: "spare",
      className: "spare",
      label: "Spare part",
      title: component?.spare_part_code ?? "Chưa có phụ tùng",
      detail: "phụ tùng thay thế",
      tone: component?.spare_part_code ? "danger" : "neutral",
    },
    {
      key: "inventory",
      className: "inventory",
      label: "Inventory",
      title: textValue(inventory, "code") ?? component?.spare_part_code ?? "Chưa có tồn kho",
      detail: `quantity = ${textValue(inventory, "quantity_on_hand") ?? "0"}`,
      tone: "danger",
    },
    {
      key: "purchase",
      className: "purchase",
      label: "Purchase",
      title: purchase?.status ?? "Chưa tạo request",
      detail: purchase ? `qty ${purchase.quantity_requested}` : "draft sau reasoning",
      tone: purchase ? "active" : "neutral",
    },
    {
      key: "approver",
      className: "approver",
      label: "Approver",
      title: purchase?.final_approver ?? textValue(approver, "name") ?? "Chưa xác định",
      detail: purchase?.approval_policy_code ?? "approval policy",
      tone: purchase ? "active" : "neutral",
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
      <div className="ontology-graph" aria-label="Ontology relationship graph">
        <svg className="graph-lines" viewBox="0 0 1120 390" preserveAspectRatio="none" aria-hidden="true">
          <path d="M190 194 H250" />
          <path d="M400 174 C440 86 470 86 500 86" />
          <path d="M650 86 H720" />
          <path d="M400 214 C440 304 470 304 500 304" />
          <path d="M650 304 H720" />
          <path d="M870 304 C920 304 920 235 920 194" />
          <path d="M995 240 V270" />
        </svg>
        {nodes.map((node) => (
          <div className={`graph-node ${node.className} ${node.tone}`} key={node.key}>
            <span>{node.label}</span>
            <strong>{node.title}</strong>
            <small>{node.detail}</small>
          </div>
        ))}
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
