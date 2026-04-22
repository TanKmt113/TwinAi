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

  const nodes = [
    { key: "asset", title: "Asset", value: asset?.name ?? "Chưa có asset", tone: "active" },
    { key: "component", title: "Component", value: component?.name ?? "Chưa có component", tone: "warn" },
    { key: "rule", title: "Rule", value: "R-ELV-CABLE-001", tone: "active" },
    { key: "manual", title: "Manual", value: "MAN-ELV-001", tone: "active" },
    { key: "spare", title: "Spare part", value: component?.spare_part_code ?? "Chưa có phụ tùng", tone: "danger" },
    { key: "purchase", title: "Purchase", value: purchase?.status ?? "Chưa tạo request", tone: purchase ? "active" : "neutral" },
    { key: "approver", title: "Approver", value: purchase?.final_approver ?? "Chưa xác định", tone: purchase ? "active" : "neutral" },
  ];

  return (
    <div>
      <div className="map-source">Nguồn ontology: {source}</div>
      <div className="ontology-map" aria-label="Ontology map">
        {nodes.map((node, index) => (
          <div className="map-segment" key={node.key}>
            <div className={`map-node ${node.tone}`}>
              <span>{node.title}</span>
              <strong>{node.value}</strong>
            </div>
            {index < nodes.length - 1 ? <div className="map-edge">→</div> : null}
          </div>
        ))}
      </div>
    </div>
  );
}

