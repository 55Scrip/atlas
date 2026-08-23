/**
 * Thin typed client for Decision Reliability (Atlas Decision Layer
 * Sprint 7, `atlas/alpha/decision_reliability/api/`). Field names
 * mirror the backend's own `CamelModel` views exactly. This module
 * adds no logic of its own beyond the wire-format mapping.
 */

export type ReliabilityLevel = "high" | "moderate" | "limited" | "unavailable" | "unknown";
export type ReliabilitySource = "confidence" | "evidence_quality" | "readiness_blocker" | "readiness_support";
export type ReliabilityReferenceKind = "finding" | "observation" | "reason_code" | "decision_snapshot";
export type ChangeDirection = "stronger" | "weaker" | "unchanged";

export interface ReliabilityReferenceView {
  kind: ReliabilityReferenceKind;
  id: string;
}

export interface ReliabilityReasonView {
  source: ReliabilitySource;
  reference: ReliabilityReferenceView;
  count: number | null;
  total: number | null;
}

export interface DecisionReliabilityView {
  caseId: string;
  level: ReliabilityLevel;
  supportingReasons: ReliabilityReasonView[];
  limitingReasons: ReliabilityReasonView[];
  primaryLimitingReason: ReliabilityReasonView | null;
  generatedAt: string;
}

export interface DecisionReliabilitySummaryView {
  caseId: string;
  level: ReliabilityLevel;
  primaryLimitingReason: ReliabilityReasonView | null;
  generatedAt: string;
}

export interface ReliabilityChangeView {
  caseId: string;
  previousLevel: ReliabilityLevel;
  currentLevel: ReliabilityLevel;
  direction: ChangeDirection | null;
  newLimiting: ReliabilityReasonView[];
  resolvedLimiting: ReliabilityReasonView[];
  detectedAt: string;
}

export interface ReliabilityComparisonView {
  a: DecisionReliabilityView;
  b: DecisionReliabilityView;
  moreReliableCaseId: string | null;
  sharedLimiting: ReliabilityReferenceView[];
  differingLimitingA: ReliabilityReferenceView[];
  differingLimitingB: ReliabilityReferenceView[];
  sharedSupporting: ReliabilityReferenceView[];
}

export interface PortfolioReliabilityBreakdownView {
  mostReliable: string[];
  leastReliable: string[];
  recentlyImproved: string[];
  recentlyWeakened: string[];
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchDecisionReliability(caseId: string, signal?: AbortSignal): Promise<DecisionReliabilityView> {
  return getJson(`/api/decision-reliability/${encodeURIComponent(caseId)}`, signal);
}

export function fetchDecisionReliabilityChange(caseId: string, signal?: AbortSignal): Promise<ReliabilityChangeView | null> {
  return getJson(`/api/decision-reliability/${encodeURIComponent(caseId)}/change`, signal);
}

export function fetchPortfolioReliabilityBreakdown(signal?: AbortSignal): Promise<PortfolioReliabilityBreakdownView> {
  return getJson("/api/decision-reliability/portfolio/breakdown", signal);
}

export function compareDecisionReliability(
  tickerA: string,
  tickerB: string,
  signal?: AbortSignal,
): Promise<ReliabilityComparisonView | null> {
  return fetch(`/api/decision-reliability/compare?tickerA=${encodeURIComponent(tickerA)}&tickerB=${encodeURIComponent(tickerB)}`, {
    signal: signal ?? null,
  }).then(async (response) => {
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
    return (await response.json()) as ReliabilityComparisonView;
  });
}
