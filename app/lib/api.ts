const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// ---------- Types ----------

export type Company = {
  id: string;
  name: string;
  website: string | null;
  status: string;
  created_at: string | null;
  fit_score: number | null;
};

export type Research = {
  summary?: string;
  gaps?: string | string[];
  raw?: {
    what_they_do?: string;
    audience?: string;
    gaps?: string[];
    confidence?: string;
  };
};

export type Score = {
  fit_score: number;
  reasoning?: string;
  matched_services?: string[];
};

export type Draft = {
  id: string;
  company_id: string;
  company_name?: string;
  company_website?: string | null;
  fit_score?: number | null;
  score_reasoning?: string | null;
  subject: string;
  body: string;
  approval_status: string;
  created_at?: string | null;
};

export type CompanyDetail = {
  company: Company;
  research: Research | null;
  score: Score | null;
  draft: Draft | null;
};

export type DashboardStats = {
  total: number;
  by_status: Record<string, number>;
  avg_score: number | null;
  waiting: number;
  approved: number;
  rejected: number;
  approval_rate: number | null;
};

// ---------- Request helper ----------

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      cache: "no-store",
    });
  } catch {
    throw new Error(
      "Cannot connect to ClientPilot's backend. Make sure FastAPI is running."
    );
  }

  if (!response.ok) {
    let message = `Request failed (${response.status})`;

    try {
      const data = await response.json();
      message =
        typeof data.detail === "string"
          ? data.detail
          : JSON.stringify(data.detail ?? data);
    } catch {
      // Keep the default message if the response isn't JSON.
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

// ---------- Companies ----------

export function listCompanies() {
  return request<Company[]>("/companies");
}

export function companyDetail(id: string) {
  return request<CompanyDetail>(
    `/companies/${encodeURIComponent(id)}`
  );
}

export function bulkAdd(companies: { name: string; website: string }[]) {
  return request<{ added: number; skipped: number }>("/companies/bulk", {
    method: "POST",
    body: JSON.stringify({ companies }),
  });
}

// ---------- Pipeline ----------

export function runPipeline(id: string, force = false) {
  return request<{
    company?: string;
    final_status?: string;
    score?: number | null;
    decision?: string;
    subject?: string | null;
    error?: string | null;
    log?: string[];
  }>(
    `/pipeline/${encodeURIComponent(id)}?force=${force}`,
    { method: "POST" }
  );
}

export function runBatch(limit = 3) {
  return request<unknown>(
    `/pipeline-batch?limit=${limit}`,
    { method: "POST" }
  );
}

// ---------- Draft approval queue ----------

export function listDrafts(
  view: "waiting" | "approved" | "rejected" = "waiting"
) {
  return request<Draft[]>(
    `/drafts?view=${encodeURIComponent(view)}`
  );
}

export function editDraft(
  id: string,
  subject: string,
  body: string
) {
  return request<{ id: string; approval_status: string }>(
    `/drafts/${encodeURIComponent(id)}`,
    {
      method: "PATCH",
      body: JSON.stringify({ subject, body }),
    }
  );
}

export function approveDraft(id: string) {
  return request<{ id: string; approval_status: string }>(
    `/drafts/${encodeURIComponent(id)}/approve`,
    { method: "POST" }
  );
}

export function rejectDraft(id: string) {
  return request<{ id: string; approval_status: string }>(
    `/drafts/${encodeURIComponent(id)}/reject`,
    { method: "POST" }
  );
}

// ---------- Analytics ----------

export function getStats() {
  return request<DashboardStats>("/stats");
}