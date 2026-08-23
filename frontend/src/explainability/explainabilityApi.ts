import type { ConfidenceReasonView, DimensionCoverageView } from "../coverage/coverageApi";
import type { StanceReasonView } from "../stance/stanceApi";

/**
 * Thin typed client for the Explainability Engine (Atlas Intelligence
 * Sprint 3, `atlas/alpha/explainability/api/`). Field names mirror
 * `ExplanationView`/`ComparisonEvidenceView` exactly (camelCase, via
 * the backend's own `CamelModel`). Reuses `DimensionCoverageView`/
 * `ConfidenceReasonView` (Sprint 1, `../coverage/coverageApi`) and
 * `StanceReasonView` (Sprint 2, `../stance/stanceApi`) verbatim -- this
 * codebase's own "shared, lower-level presentation types are declared
 * once, not per-package" frontend convention (see `coverageApi.ts`'s
 * own module docstring).
 */
export interface ExplanationView {
  supportingEvidence: StanceReasonView[];
  contradictingEvidence: StanceReasonView[];
  limitingFactors: StanceReasonView[];
  missingEvidence: DimensionCoverageView[];
  confidenceDrivers: ConfidenceReasonView[];
  mostValuableMissingInformation: DimensionCoverageView | null;
}

export interface ComparisonEvidenceView {
  favoringA: StanceReasonView[];
  favoringB: StanceReasonView[];
  shared: StanceReasonView[];
  missingForBoth: string[];
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T | null> {
  const response = await fetch(url, { signal: signal ?? null });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchExplanationForCase(caseId: string, signal?: AbortSignal): Promise<ExplanationView | null> {
  return getJson(`/api/explainability/case/${encodeURIComponent(caseId)}`, signal);
}

export function fetchExplanationForTicker(ticker: string, signal?: AbortSignal): Promise<ExplanationView | null> {
  return getJson(`/api/explainability/ticker/${encodeURIComponent(ticker)}`, signal);
}

export function compareExplanations(
  tickerA: string,
  tickerB: string,
  signal?: AbortSignal,
): Promise<ComparisonEvidenceView | null> {
  return getJson(
    `/api/explainability/compare?tickerA=${encodeURIComponent(tickerA)}&tickerB=${encodeURIComponent(tickerB)}`,
    signal,
  );
}
