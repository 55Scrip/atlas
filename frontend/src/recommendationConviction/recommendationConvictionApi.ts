/**
 * Thin typed client for Recommendation Conviction & Strength (Atlas
 * Decision Layer Sprint 2, `atlas/alpha/recommendation_conviction/api/`).
 * Field names mirror the backend's own `CamelModel` views exactly.
 * This module adds no logic of its own beyond the wire-format mapping.
 */

export type ConvictionStrength = "very_strong" | "strong" | "moderate" | "weak" | "very_weak" | "unavailable";

export type RecommendationStability =
  | "stable"
  | "fragile"
  | "waiting_for_evidence"
  | "operationally_blocked"
  | "evidence_limited";

export type ConvictionReasonSource = "readiness_blocker" | "readiness_support" | "analysis_conviction" | "evidence_graph";

export interface ConvictionReasonView {
  source: ConvictionReasonSource;
  code: string;
}

export interface RecommendationConvictionView {
  caseId: string;
  action: string;
  strength: ConvictionStrength;
  stability: RecommendationStability;
  supportingReasons: ConvictionReasonView[];
  limitingReasons: ConvictionReasonView[];
  strengtheningTrigger: ConvictionReasonView | null;
  generatedAt: string;
}

export interface ConvictionChangeView {
  caseId: string;
  previousStrength: ConvictionStrength;
  currentStrength: ConvictionStrength;
  previousStability: RecommendationStability;
  currentStability: RecommendationStability;
  newLimitingReasons: ConvictionReasonView[];
  resolvedLimitingReasons: ConvictionReasonView[];
  detectedAt: string;
}

export interface ConvictionComparisonView {
  a: RecommendationConvictionView;
  b: RecommendationConvictionView;
  strongerCaseId: string | null;
  moreEvidenceLimitedCaseId: string | null;
  moreOperationallyBlockedCaseId: string | null;
  moreStableCaseId: string | null;
}

export interface PortfolioConvictionBreakdownView {
  highestConviction: string[];
  lowestConviction: string[];
  evidenceLimited: string[];
  operationallyBlocked: string[];
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchRecommendationConviction(caseId: string, signal?: AbortSignal): Promise<RecommendationConvictionView> {
  return getJson(`/api/recommendation-conviction/${encodeURIComponent(caseId)}`, signal);
}

export function fetchRecommendationConvictionChange(
  caseId: string,
  signal?: AbortSignal,
): Promise<ConvictionChangeView | null> {
  return getJson(`/api/recommendation-conviction/${encodeURIComponent(caseId)}/change`, signal);
}

export function fetchPortfolioConvictionBreakdown(signal?: AbortSignal): Promise<PortfolioConvictionBreakdownView> {
  return getJson("/api/recommendation-conviction/portfolio/breakdown", signal);
}

export function compareRecommendationConviction(
  tickerA: string,
  tickerB: string,
  signal?: AbortSignal,
): Promise<ConvictionComparisonView | null> {
  return fetch(
    `/api/recommendation-conviction/compare?tickerA=${encodeURIComponent(tickerA)}&tickerB=${encodeURIComponent(tickerB)}`,
    { signal: signal ?? null },
  ).then(async (response) => {
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
    return (await response.json()) as ConvictionComparisonView;
  });
}
