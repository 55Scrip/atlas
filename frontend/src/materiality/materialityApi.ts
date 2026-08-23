import type { DimensionCoverageView } from "../coverage/coverageApi";
import type { StanceReasonView } from "../stance/stanceApi";

/**
 * Thin typed client for the Materiality Engine (Atlas Intelligence
 * `atlas/alpha/materiality/api/`). Field names mirror
 * `MaterialityAssessmentView` exactly (camelCase, via the backend's own
 * `CamelModel`). Reuses `DimensionCoverageView` (Sprint 1) and
 * `StanceReasonView` (Sprint 2) verbatim rather than redeclaring them --
 * this codebase's own "shared, lower-level presentation types are
 * declared once, not per-package" frontend convention.
 */
export type MaterialityLevel = "critical" | "high" | "medium" | "low" | "background" | "unknown";

export interface MaterialEvidenceView {
  reason: StanceReasonView;
  materiality: MaterialityLevel;
}

export interface MaterialityAssessmentView {
  supportingEvidence: MaterialEvidenceView[];
  contradictingEvidence: MaterialEvidenceView[];
  limitingFactors: MaterialEvidenceView[];
  topSupportingEvidence: MaterialEvidenceView | null;
  topContradictingEvidence: MaterialEvidenceView | null;
  topLimitingFactor: MaterialEvidenceView | null;
  topMissingEvidence: DimensionCoverageView | null;
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T | null> {
  const response = await fetch(url, { signal: signal ?? null });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchMaterialityForCase(caseId: string, signal?: AbortSignal): Promise<MaterialityAssessmentView | null> {
  return getJson(`/api/materiality/case/${encodeURIComponent(caseId)}`, signal);
}

export function fetchMaterialityForTicker(ticker: string, signal?: AbortSignal): Promise<MaterialityAssessmentView | null> {
  return getJson(`/api/materiality/ticker/${encodeURIComponent(ticker)}`, signal);
}
