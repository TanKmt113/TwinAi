export type HealthResponse = {
  status: string;
  service: string;
  version: string;
};

export type Component = {
  id: string;
  code: string;
  name: string;
  component_type: string;
  remaining_lifetime_months: number | null;
  spare_part_code: string | null;
  status: string;
};

export type Asset = {
  id: string;
  code: string;
  name: string;
  asset_type: string;
  location: string | null;
  department_owner: string | null;
  status: string;
  components: Component[];
};

export type InspectionTask = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  assigned_to: string | null;
  evidence_required_json: string[];
  created_by_agent: boolean;
};

export type PurchaseRequest = {
  id: string;
  reason: string;
  quantity_requested: number;
  status: string;
  approval_policy_code: string | null;
  final_approver: string | null;
  created_by_agent: boolean;
};

export type AgentRun = {
  id: string;
  run_type: string;
  status: string;
  input_snapshot: Record<string, unknown>;
  output_summary: Record<string, unknown>;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
};

export type OntologyContext = Record<string, unknown>;

export type ReasoningResponse = {
  run_id: string;
  status: string;
  findings: Array<Record<string, unknown>>;
  created_tasks: InspectionTask[];
  created_purchase_requests: PurchaseRequest[];
  audit_events: Array<Record<string, unknown>>;
};

const fallbackHealth: HealthResponse = {
  status: "unavailable",
  service: "TwinAI Agentic MVP API",
  version: "unknown",
};

const serverBaseUrl = process.env.BACKEND_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function getApiHealth(): Promise<HealthResponse> {
  return getServerJson<HealthResponse>("/health", fallbackHealth);
}

export async function getDashboardData() {
  const [health, assets, tasks, purchaseRequests, agentRuns] = await Promise.all([
    getApiHealth(),
    getServerJson<Asset[]>("/api/assets", []),
    getServerJson<InspectionTask[]>("/api/inspection-tasks", []),
    getServerJson<PurchaseRequest[]>("/api/purchase-requests", []),
    getServerJson<AgentRun[]>("/api/agent-runs", []),
  ]);

  const selectedAsset = assets[0];
  const ontology = selectedAsset ? await getServerJson<OntologyContext>(`/api/assets/${selectedAsset.code}/ontology`, {}) : {};

  return {
    health,
    assets,
    tasks,
    purchaseRequests,
    agentRuns,
    selectedAsset,
    ontology,
  };
}

export async function runReasoningFromBrowser(): Promise<ReasoningResponse> {
  const response = await fetch("/api/backend/api/reasoning/run", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Reasoning failed with status ${response.status}`);
  }

  return response.json();
}

async function getServerJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(`${serverBaseUrl}${path}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return fallback;
    }

    return response.json();
  } catch {
    return fallback;
  }
}

