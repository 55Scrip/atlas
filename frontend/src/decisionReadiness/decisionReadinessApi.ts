/**
 * Thin typed client for Decision Readiness (Atlas Intelligence Sprint
 * 11, `atlas/alpha/decision_readiness/api/`). Field names mirror the
 * backend's own `CamelModel` views exactly. This module adds no logic
 * of its own beyond the wire-format mapping.
 */

export type DecisionReadinessStatus = "ready" | "almost_ready" | "waiting" | "blocked" | "unavailable" | "unknown";

export type DecisionBlockerKind =
  | "never_evaluated"
  | "monitoring_failed"
  | "no_data_source"
  | "conflicting_evidence"
  | "critical_dependency_unresolved"
  | "monitoring_pending"
  | "operational_freshness_outdated"
  | "coverage_incomplete"
  | "insufficient_evidence"
  | "unknown_valuation"
  | "missing_observation"
  | "missing_thesis_evidence"
  | "avoid_decision_signal";

export type DecisionReadinessReasonKind =
  | "substantial_coverage_reached"
  | "confidence_established"
  | "no_conflicts_found"
  | "monitoring_current"
  | "decision_support_reached"
  | "no_critical_dependencies";

export interface DecisionBlockerView {
  kind: DecisionBlockerKind;
  detail: number | null;
}

export interface DecisionReadinessReasonView {
  kind: DecisionReadinessReasonKind;
  detail: number | null;
}

export interface DecisionReadinessView {
  caseId: string;
  status: DecisionReadinessStatus;
  blockers: DecisionBlockerView[];
  supportingReasons: DecisionReadinessReasonView[];
  generatedAt: string;
}

export interface DecisionReadinessSummaryView {
  caseId: string;
  status: DecisionReadinessStatus;
  primaryBlocker: DecisionBlockerView | null;
  primarySupportingReason: DecisionReadinessReasonView | null;
  generatedAt: string;
}

export interface DecisionReadinessChangeView {
  caseId: string;
  previousStatus: DecisionReadinessStatus;
  currentStatus: DecisionReadinessStatus;
  newBlockers: DecisionBlockerKind[];
  resolvedBlockers: DecisionBlockerKind[];
  detectedAt: string;
}

export interface DecisionReadinessComparisonView {
  a: DecisionReadinessView;
  b: DecisionReadinessView;
  closerCaseId: string | null;
  differingBlockerKinds: DecisionBlockerKind[];
}

export interface PortfolioReadinessBreakdownView {
  ready: string[];
  almostReady: string[];
  waiting: string[];
  blocked: string[];
  unavailable: string[];
  unknown: string[];
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchDecisionReadiness(caseId: string, signal?: AbortSignal): Promise<DecisionReadinessView> {
  return getJson(`/api/decision-readiness/${encodeURIComponent(caseId)}`, signal);
}

export function fetchDecisionReadinessChange(caseId: string, signal?: AbortSignal): Promise<DecisionReadinessChangeView | null> {
  return getJson(`/api/decision-readiness/${encodeURIComponent(caseId)}/change`, signal);
}

export function fetchPortfolioReadinessBreakdown(signal?: AbortSignal): Promise<PortfolioReadinessBreakdownView> {
  return getJson("/api/decision-readiness/portfolio/breakdown", signal);
}

export function compareDecisionReadiness(
  tickerA: string,
  tickerB: string,
  signal?: AbortSignal,
): Promise<DecisionReadinessComparisonView | null> {
  return fetch(`/api/decision-readiness/compare?tickerA=${encodeURIComponent(tickerA)}&tickerB=${encodeURIComponent(tickerB)}`, {
    signal: signal ?? null,
  }).then(async (response) => {
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
    return (await response.json()) as DecisionReadinessComparisonView;
  });
}
