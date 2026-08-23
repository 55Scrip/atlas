/**
 * Thin typed client for the Evidence Quality Engine (Atlas Intelligence
 * Sprint 4, `atlas/alpha/evidence_quality/api/`). Field names mirror
 * `EvidenceQualityReportView` exactly (camelCase, via the backend's own
 * `CamelModel`). This module adds no logic of its own beyond the
 * wire-format mapping.
 */

export type EvidenceFreshness = "fresh" | "recent" | "old" | "stale" | "not_applicable";
export type EvidenceDominance = "single_source" | "corroborated" | "not_applicable";
export type EvidenceConflictStatus = "consistent" | "conflicting" | "not_applicable";
export type EvidenceQualityLevel =
  | "fresh"
  | "recent"
  | "old"
  | "stale"
  | "superseded"
  | "conflicting"
  | "incomplete"
  | "unsupported"
  | "not_applicable";

export type EvidenceWarningCode =
  | "conflicting_source_values"
  | "evidence_stale"
  | "single_source_dependency"
  | "conclusion_without_support"
  | "partial_coverage"
  | "no_evidence";

export interface EvidenceConflictView {
  factKind: string;
  period: string;
  unit: string;
  values: number[];
  sourceRecordIds: string[];
}

export interface FactQualityView {
  factKind: string;
  freshness: EvidenceFreshness;
  dominance: EvidenceDominance;
  latestPeriod: string | null;
  latestPublishedAt: string | null;
  sourceRecordCount: number;
}

export interface UnsupportedFindingView {
  category: string;
  status: string;
}

export interface EvidenceQualityReportView {
  quality: EvidenceQualityLevel;
  conflictStatus: EvidenceConflictStatus;
  freshness: EvidenceFreshness;
  dominance: EvidenceDominance;
  warnings: EvidenceWarningCode[];
  facts: FactQualityView[];
  conflicts: EvidenceConflictView[];
  unsupportedFindings: UnsupportedFindingView[];
}

export interface TickerEvidenceQualityView {
  ticker: string;
  report: EvidenceQualityReportView;
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T | null> {
  const response = await fetch(url, { signal: signal ?? null });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchEvidenceQualityForCase(caseId: string, signal?: AbortSignal): Promise<EvidenceQualityReportView | null> {
  return getJson(`/api/evidence-quality/case/${encodeURIComponent(caseId)}`, signal);
}

export function fetchEvidenceQualityForTicker(ticker: string, signal?: AbortSignal): Promise<EvidenceQualityReportView | null> {
  return getJson(`/api/evidence-quality/ticker/${encodeURIComponent(ticker)}`, signal);
}

export async function fetchEvidenceQualityForHoldings(signal?: AbortSignal): Promise<TickerEvidenceQualityView[]> {
  const response = await fetch("/api/evidence-quality/holdings", { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as TickerEvidenceQualityView[];
}

export async function fetchEvidenceQualityForCandidates(signal?: AbortSignal): Promise<TickerEvidenceQualityView[]> {
  const response = await fetch("/api/evidence-quality/candidates", { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as TickerEvidenceQualityView[];
}
