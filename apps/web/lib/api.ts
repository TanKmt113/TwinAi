export type HealthResponse = {
  status: string;
  service: string;
  version: string;
};

export type ServiceHealthEntry = {
  id: string;
  label: string;
  ok: boolean;
  detail: string;
  optional?: boolean;
};

export type SystemServicesResponse = {
  overall: "ok" | "degraded" | "critical" | "unknown";
  checked_at: string;
  services: ServiceHealthEntry[];
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

type ApiAsset = Omit<Asset, "components"> & {
  components?: Component[] | null;
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
  component_id: string;
  inventory_item_id: string;
  rule_id: string | null;
  reason: string;
  quantity_requested: number;
  status: string;
  approval_policy_code: string | null;
  final_approver: string | null;
  created_by_agent: boolean;
  created_at: string;
};

export type PurchaseRequestDetail = PurchaseRequest & {
  asset_id: string | null;
  asset_code: string | null;
  component_code: string | null;
};

export type AuditLogEntry = {
  id: string;
  actor_type: string;
  actor_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  before_json: Record<string, unknown> | null;
  after_json: Record<string, unknown> | null;
  reason: string | null;
  created_at: string;
};

export type OrgUnit = {
  id: string;
  code: string;
  name: string;
  level_kind: string;
  parent_id: string | null;
  sort_order: number;
};

export type OrgUser = {
  id: string;
  user_code: string;
  full_name: string;
  email: string | null;
  job_title: string | null;
  org_unit_id: string | null;
  org_unit_code: string | null;
  org_unit_name: string | null;
  manager_user_id: string | null;
  manager_user_code: string | null;
  role_tags: string[];
  is_active: boolean;
};

export type OrgUserBrief = {
  user_code: string;
  full_name: string;
  email: string;
  job_title: string | null;
  role_tags: string[];
};

export type AssetContacts = {
  asset_id: string;
  asset_code: string;
  asset_name: string;
  department_owner: string | null;
  primary_contact: OrgUserBrief | null;
  backup_contact: OrgUserBrief | null;
  escalation_policy_code: string | null;
  escalation_policy_name: string | null;
  contact_resolution?: {
    primary_source: string;
    backup_source: string;
  };
};

export type RuleNotificationTargets = {
  rule_id: string;
  rule_code: string;
  rule_name: string;
  suggested_approvers: OrgUserBrief[];
  suggested_operational_contacts: OrgUserBrief[];
  escalation_policy: { code: string; name: string; config: Record<string, unknown> } | null;
};

export type EscalationPolicyDetail = {
  id: string;
  code: string;
  name: string;
  config: Record<string, unknown>;
};

export type WorkflowActorBody = {
  actor_type?: string;
  actor_id?: string;
  note?: string | null;
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

export type Manual = {
  id: string;
  code: string;
  title: string;
  department_owner: string | null;
  file_name: string;
  file_type: string | null;
  version: string | null;
  status: string;
};

export type ManualChunk = {
  id: string;
  manual_id: string;
  chunk_index: number;
  heading: string | null;
  page_number: number | null;
  chunk_text: string;
  metadata_json: Record<string, unknown>;
};

export type ChatResponse = {
  intent: string;
  conclusion: string;
  evidence: string[];
  recommended_actions: string[];
  missing_data: string[];
  agent_mode?: string;
  tool_calls?: string[];
  citations: Array<{
    type: string;
    code: string;
    title: string;
  }>;
};

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

const fallbackSystemServices: SystemServicesResponse = {
  overall: "unknown",
  checked_at: "",
  services: [],
};

const serverBaseUrl = process.env.BACKEND_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function getApiHealth(): Promise<HealthResponse> {
  return getServerJson<HealthResponse>("/health", fallbackHealth);
}

export async function getSystemServicesHealth(): Promise<SystemServicesResponse> {
  return getServerJson<SystemServicesResponse>("/health/services", fallbackSystemServices);
}

export async function fetchOrgUnitsFromServer(): Promise<OrgUnit[]> {
  return getServerJson<OrgUnit[]>("/api/org/units", []);
}

export async function fetchOrgUsersFromServer(): Promise<OrgUser[]> {
  return getServerJson<OrgUser[]>("/api/org/users", []);
}

export async function getDashboardData() {
  const [health, systemServices, apiAssets, tasks, purchaseRequests, agentRuns, manuals] = await Promise.all([
    getApiHealth(),
    getSystemServicesHealth(),
    getServerJson<ApiAsset[]>("/api/assets", []),
    getServerJson<InspectionTask[]>("/api/inspection-tasks", []),
    getServerJson<PurchaseRequest[]>("/api/purchase-requests", []),
    getServerJson<AgentRun[]>("/api/agent-runs", []),
    getServerJson<Manual[]>("/api/manuals", []),
  ]);

  const assets = apiAssets.map(normalizeAsset);
  const selectedAsset = assets[0];
  const ontology = selectedAsset ? await getServerJson<OntologyContext>(`/api/assets/${selectedAsset.code}/ontology`, {}) : {};

  return {
    health,
    systemServices,
    assets,
    tasks,
    purchaseRequests,
    agentRuns,
    manuals,
    selectedAsset,
    ontology,
  };
}

function normalizeAsset(asset: ApiAsset): Asset {
  return {
    ...asset,
    components: Array.isArray(asset.components) ? asset.components : [],
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

export async function uploadManualFromBrowser(file: File): Promise<Manual> {
  const formData = new FormData();
  formData.set("file", file);
  formData.set("title", file.name);

  const response = await fetch("/api/backend/api/manuals/upload", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed with status ${response.status}`);
  }

  return response.json();
}

export async function parseManualFromBrowser(manualId: string): Promise<ManualChunk[]> {
  const response = await fetch(`/api/backend/api/manuals/${manualId}/parse`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`Parse failed with status ${response.status}`);
  }

  return response.json();
}

export async function queryChatFromBrowser(question: string): Promise<ChatResponse> {
  const response = await fetch("/api/backend/api/chat/query", {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    throw new Error(`Chat failed with status ${response.status}`);
  }

  return response.json();
}

async function postPurchaseWorkflowAction(
  requestId: string,
  action: "submit" | "approve" | "reject" | "cancel",
  body: WorkflowActorBody,
): Promise<PurchaseRequest> {
  const response = await fetch(`/api/backend/api/purchase-requests/${requestId}/${action}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      actor_type: body.actor_type ?? "user",
      actor_id: body.actor_id ?? "demo_user",
      note: body.note ?? null,
    }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${action} thất bại (${response.status}): ${detail}`);
  }
  return response.json();
}

export function submitPurchaseRequestFromBrowser(requestId: string, body: WorkflowActorBody = {}) {
  return postPurchaseWorkflowAction(requestId, "submit", body);
}

export function approvePurchaseRequestFromBrowser(requestId: string, body: WorkflowActorBody = {}) {
  return postPurchaseWorkflowAction(requestId, "approve", body);
}

export function rejectPurchaseRequestFromBrowser(requestId: string, body: WorkflowActorBody = {}) {
  return postPurchaseWorkflowAction(requestId, "reject", body);
}

export function cancelPurchaseRequestFromBrowser(requestId: string, body: WorkflowActorBody = {}) {
  return postPurchaseWorkflowAction(requestId, "cancel", body);
}

export async function fetchPurchaseRequestDetailFromServer(id: string): Promise<PurchaseRequestDetail | null> {
  return getServerJsonStrict<PurchaseRequestDetail>(`/api/purchase-requests/${encodeURIComponent(id)}`);
}

export async function fetchAuditLogsFromServer(params?: {
  entityType?: string;
  entityId?: string;
  limit?: number;
}): Promise<AuditLogEntry[]> {
  const q = new URLSearchParams();
  if (params?.entityType) {
    q.set("entity_type", params.entityType);
  }
  if (params?.entityId) {
    q.set("entity_id", params.entityId);
  }
  if (params?.limit) {
    q.set("limit", String(params.limit));
  }
  const suffix = q.toString() ? `?${q.toString()}` : "";
  const rows = await getServerJsonStrict<AuditLogEntry[]>(`/api/audit-logs${suffix}`);
  return rows ?? [];
}

export async function fetchAssetContactsFromServer(assetId: string): Promise<AssetContacts | null> {
  return getServerJsonStrict<AssetContacts>(`/api/assets/${encodeURIComponent(assetId)}/contacts`);
}

export async function fetchRuleNotificationTargetsFromServer(ruleId: string): Promise<RuleNotificationTargets | null> {
  return getServerJsonStrict<RuleNotificationTargets>(
    `/api/rules/${encodeURIComponent(ruleId)}/notification-targets`,
  );
}

export async function fetchEscalationPolicyFromServer(idOrCode: string): Promise<EscalationPolicyDetail | null> {
  return getServerJsonStrict<EscalationPolicyDetail>(
    `/api/escalation-policies/${encodeURIComponent(idOrCode)}`,
  );
}

async function getServerJsonStrict<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(`${serverBaseUrl}${path}`, { cache: "no-store" });
    if (!response.ok) {
      return null;
    }
    return response.json() as Promise<T>;
  } catch {
    return null;
  }
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
