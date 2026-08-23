/**
 * Thin typed client for Decision Memory (Atlas Decision Layer Sprint
 * 5, `atlas/alpha/decision_memory/api/`). Field names mirror the
 * backend's own `CamelModel` views exactly. This module adds no logic
 * of its own beyond the wire-format mapping.
 */

export type ChangeDirection = "stronger" | "weaker" | "unchanged";

export interface DecisionSnapshotView {
  caseId: string;
  action: string;
  readinessStatus: string;
  blockerCodes: string[];
  convictionStrength: string;
  convictionStability: string;
  decisionPathStepCount: number;
  decisionPathFinalState: string;
  primaryAlternativeKind: string | null;
  alternativeCount: number;
  contentHash: string;
  recordedAt: string;
}

export interface DecisionMemoryChangeView {
  caseId: string;
  isBaseline: boolean;
  previousAction: string | null;
  currentAction: string;
  recommendationChanged: boolean;
  convictionDirection: ChangeDirection | null;
  readinessDirection: ChangeDirection | null;
  decisionPathDirection: ChangeDirection | null;
  blockersResolved: string[];
  blockersAdded: string[];
  alternativeChanged: boolean;
  detectedAt: string;
}

export interface DecisionTimelineEntryView {
  snapshot: DecisionSnapshotView;
  change: DecisionMemoryChangeView;
}

export interface DecisionTimelineView {
  caseId: string;
  entries: DecisionTimelineEntryView[];
}

export interface DecisionMemoryView {
  caseId: string;
  currentSnapshot: DecisionSnapshotView;
  previousSnapshot: DecisionSnapshotView | null;
  latestChange: DecisionMemoryChangeView | null;
  history: DecisionTimelineView;
}

export interface DecisionMemoryComparisonView {
  a: DecisionMemoryView;
  b: DecisionMemoryView;
  moreRecentlyChangedCaseId: string | null;
  moreStableCaseId: string | null;
  convictionChangedCaseId: string | null;
  blockersDisappearedCaseId: string | null;
}

export interface PortfolioDecisionMemoryBreakdownView {
  recentlyChanged: string[];
  stable: string[];
  recentlyStrengthened: string[];
  recentlyWeakened: string[];
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchDecisionMemory(caseId: string, signal?: AbortSignal): Promise<DecisionMemoryView> {
  return getJson(`/api/decision-memory/${encodeURIComponent(caseId)}`, signal);
}

export function fetchDecisionMemoryChange(caseId: string, signal?: AbortSignal): Promise<DecisionMemoryChangeView | null> {
  return getJson(`/api/decision-memory/${encodeURIComponent(caseId)}/change`, signal);
}

export function fetchPortfolioDecisionMemoryBreakdown(signal?: AbortSignal): Promise<PortfolioDecisionMemoryBreakdownView> {
  return getJson("/api/decision-memory/portfolio/breakdown", signal);
}

export function compareDecisionMemory(
  tickerA: string,
  tickerB: string,
  signal?: AbortSignal,
): Promise<DecisionMemoryComparisonView | null> {
  return fetch(`/api/decision-memory/compare?tickerA=${encodeURIComponent(tickerA)}&tickerB=${encodeURIComponent(tickerB)}`, {
    signal: signal ?? null,
  }).then(async (response) => {
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
    return (await response.json()) as DecisionMemoryComparisonView;
  });
}
