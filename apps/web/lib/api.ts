type HealthResponse = {
  status: string;
  service: string;
  version: string;
};

const fallbackHealth: HealthResponse = {
  status: "unavailable",
  service: "TwinAI Agentic MVP API",
  version: "unknown",
};

export async function getApiHealth(): Promise<HealthResponse> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  try {
    const response = await fetch(`${baseUrl}/health`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return fallbackHealth;
    }

    return response.json();
  } catch {
    return fallbackHealth;
  }
}

