/**
 * Thin typed client for Monitoring & Change Detection Operations
 * (Atlas Intelligence Sprint 7/8, `atlas/alpha/monitoring/api/`). Field
 * names mirror the backend's own `CamelModel` views exactly. This
 * module adds no logic of its own beyond the wire-format mapping.
 */

export type MonitoringChangeCategory =
  | "new_material_evidence"
  | "material_evidence_strengthened"
  | "material_evidence_weakened"
  | "evidence_became_stale"
  | "evidence_conflict_appeared"
  | "evidence_conflict_resolved"
  | "coverage_improved"
  | "coverage_deteriorated"
  | "confidence_improved"
  | "confidence_deteriorated"
  | "stance_strengthened"
  | "stance_weakened"
  | "stance_became_uncertain"
  | "material_risk_appeared"
  | "case_condition_triggered";

export type MonitoringMateriality = "material" | "minor";
export type MonitoringResultStatus =
  | "up_to_date"
  | "changed_review_suggested"
  | "changed_high_importance"
  | "waiting_for_better_evidence"
  | "unavailable";
export type MonitoringScope = "portfolio" | "watchlist";

/**
 * Sprint 8's own five-member operational vocabulary -- deliberately a
 * distinct type from `MonitoringResultStatus` above (investment
 * status). Never render one where the other is expected.
 */
export type OperationalMonitoringStatus = "up_to_date" | "running" | "pending" | "failed" | "unknown";

export interface MonitoringChangeView {
  id: string;
  category: MonitoringChangeCategory;
  materiality: MonitoringMateriality;
  direction: "positive" | "negative" | "neutral";
  reason: string;
  sourceCapability: string;
  evidenceReference: string | null;
}

export interface MonitoringResultView {
  caseId: string;
  ticker: string | null;
  scope: MonitoringScope;
  status: MonitoringResultStatus;
  changes: MonitoringChangeView[];
  stanceLevel: string | null;
  confidenceLevel: string | null;
  coverageLevel: string | null;
  latestMeaningfulEvidenceAt: string | null;
  recommendedAction: string | null;
  generatedAt: string;
}

export interface MonitoringRunView {
  generatedAt: string;
  results: MonitoringResultView[];
}

export interface MonitoringFailureView {
  caseId: string;
  ticker: string | null;
  error: string;
}

export interface PendingCaseView {
  caseId: string;
  ticker: string | null;
}

/**
 * Sprint 9, Deliverable 8/9 -- three-bucket aggregate for Portfolio's/
 * Watchlist's own "X waiting for analysis, Y no new data, Z need
 * attention" summary line. Computed server-side (`ScopeFreshnessSummary`)
 * so the bucket rule lives in exactly one place.
 */
export interface ScopeFreshnessSummaryView {
  waitingForAnalysis: number;
  noNewData: number;
  needsAttention: number;
}

export interface MonitoringOperationalStatusView {
  status: OperationalMonitoringStatus;
  lastRunStartedAt: string | null;
  lastRunCompletedAt: string | null;
  pendingCases: PendingCaseView[];
  failedCases: MonitoringFailureView[];
  portfolioFreshness: ScopeFreshnessSummaryView;
  watchlistFreshness: ScopeFreshnessSummaryView;
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchMonitoringStatus(signal?: AbortSignal): Promise<MonitoringOperationalStatusView> {
  return getJson("/api/monitoring/status", signal);
}

export function fetchMonitoringResults(signal?: AbortSignal): Promise<MonitoringRunView> {
  return getJson("/api/monitoring/results", signal);
}
