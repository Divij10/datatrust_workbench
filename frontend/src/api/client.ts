import type { ApiErrorPayload, DatasetMetadata, DatasetProfile, QualityReport, RuleRecord, RuleStatus } from "../types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? "http://localhost:8000" : "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  if (response.ok) return (await response.json()) as T;
  let message = `Request failed (${response.status}).`;
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    message = payload.error?.message ?? message;
  } catch {
    // The HTTP status still provides useful feedback for a proxy error.
  }
  throw new Error(message);
}

export const api = {
  uploadDataset(file: File): Promise<DatasetMetadata> {
    const body = new FormData();
    body.append("file", file);
    return request<DatasetMetadata>("/api/v1/datasets", { method: "POST", body });
  },
  getProfile(datasetId: string): Promise<DatasetProfile> { return request<DatasetProfile>(`/api/v1/datasets/${datasetId}/profile`); },
  listRules(datasetId: string): Promise<RuleRecord[]> { return request<RuleRecord[]>(`/api/v1/datasets/${datasetId}/rules`); },
  suggestRules(datasetId: string): Promise<RuleRecord[]> { return request<RuleRecord[]>(`/api/v1/datasets/${datasetId}/rules/suggest`, { method: "POST" }); },
  updateRule(ruleId: string, status: Exclude<RuleStatus, "proposed">): Promise<RuleRecord> {
    return request<RuleRecord>(`/api/v1/rules/${ruleId}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }) });
  },
  evaluateDataset(datasetId: string): Promise<QualityReport> { return request<QualityReport>(`/api/v1/datasets/${datasetId}/evaluate`, { method: "POST" }); },
};
