export interface Execution {
  success: boolean;
  columns: string[];
  rows: unknown[][];
  row_count: number;
  execution_time_ms: number;
  error?: string | null;
}

export interface AskResponse {
  question: string;
  sql: string;
  success: boolean;
  summary: string;
  generation_error?: string | null;
  inference_time_ms: number;
  execution?: Execution | null;
}

export interface TableInfo {
  name: string;
  ddl: string;
}

export interface HealthResponse {
  api: string;
  database: string;
  colab_configured: boolean;
  model: {
    status?: string;
    base_model?: string;
    lora_adapter?: string;
    cuda_available?: boolean;
    error?: string;
  };
}

export class ApiError extends Error {
  constructor(public code: string, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api/v1${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(
      "network",
      "Backend unreachable. Make sure the FastAPI server is running on :8000."
    );
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const d = body?.detail ?? body;
    throw new ApiError(
      d?.code ?? "error",
      d?.message ?? `Request failed (${res.status})`
    );
  }
  return body as T;
}

export const api = {
  health: () => request<HealthResponse>("/health"),
  schema: () => request<{ tables: TableInfo[] }>("/schema"),
  examples: () => request<{ examples: string[] }>("/examples"),
  ask: (question: string) =>
    request<AskResponse>("/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  execute: (sql: string) =>
    request<Execution>("/execute", {
      method: "POST",
      body: JSON.stringify({ sql }),
    }),
  setColabUrl: (colab_api_url: string) =>
    request<{ model: HealthResponse["model"] }>("/config", {
      method: "POST",
      body: JSON.stringify({ colab_api_url }),
    }),
};
