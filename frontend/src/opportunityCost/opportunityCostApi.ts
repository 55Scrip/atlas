/**
 * Thin typed client for Decision Alternatives & Opportunity Cost
 * (Atlas Decision Layer Sprint 4, `atlas/alpha/opportunity_cost/api/`).
 * Field names mirror the backend's own `CamelModel` views exactly.
 * This module adds no logic of its own beyond the wire-format mapping.
 *
 * `AlternativeComparisonView` reuses Sprint 2's/Sprint 3's own already-
 * real wire types (`ConvictionComparisonView`/`DecisionPathComparisonView`)
 * directly, mirroring the backend's own identical reuse.
 */
import type { ConvictionComparisonView } from "../recommendationConviction/recommendationConvictionApi";
import type { DecisionPathComparisonView } from "../decisionPath/decisionPathApi";

export type AlternativeKind = "increase_existing_holding" | "open_new_position" | "wait" | "no_action" | "keep_cash";

export type AlternativeReasonSource = "readiness_blocker" | "readiness_support" | "readiness_progress" | "stance";

export interface AlternativeReasonView {
  source: AlternativeReasonSource;
  code: string;
}

export interface DecisionAlternativeView {
  kind: AlternativeKind;
  caseId: string | null;
  ticker: string | null;
  action: string | null;
  strength: string | null;
  reason: AlternativeReasonView;
}

export interface AlternativeComparisonView {
  conviction: ConvictionComparisonView;
  path: DecisionPathComparisonView;
  moreDependencyBlockedCaseId: string | null;
}

export interface DecisionTradeoffView {
  alternative: DecisionAlternativeView;
  comparison: AlternativeComparisonView | null;
}

export interface OpportunityCostView {
  caseId: string;
  currentAction: string;
  tradeoffs: DecisionTradeoffView[];
  generatedAt: string;
}

export interface OpportunityCostChangeView {
  caseId: string;
  newAlternatives: DecisionAlternativeView[];
  disappearedAlternatives: DecisionAlternativeView[];
  strengthenedAlternatives: DecisionAlternativeView[];
  weakenedAlternatives: DecisionAlternativeView[];
  primaryAlternativeChanged: boolean;
  detectedAt: string;
}

export interface PortfolioOpportunityCostBreakdownView {
  holdingsCompetingForCapital: string[];
  watchlistCompetingWithHoldings: string[];
  waitingPreferable: string[];
  noActionAppropriate: string[];
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchOpportunityCost(caseId: string, signal?: AbortSignal): Promise<OpportunityCostView> {
  return getJson(`/api/opportunity-cost/${encodeURIComponent(caseId)}`, signal);
}

export function fetchOpportunityCostChange(caseId: string, signal?: AbortSignal): Promise<OpportunityCostChangeView | null> {
  return getJson(`/api/opportunity-cost/${encodeURIComponent(caseId)}/change`, signal);
}

export function fetchPortfolioOpportunityCostBreakdown(signal?: AbortSignal): Promise<PortfolioOpportunityCostBreakdownView> {
  return getJson("/api/opportunity-cost/portfolio/breakdown", signal);
}

export function compareOpportunityCost(
  tickerA: string,
  tickerB: string,
  signal?: AbortSignal,
): Promise<AlternativeComparisonView | null> {
  return fetch(`/api/opportunity-cost/compare?tickerA=${encodeURIComponent(tickerA)}&tickerB=${encodeURIComponent(tickerB)}`, {
    signal: signal ?? null,
  }).then(async (response) => {
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
    return (await response.json()) as AlternativeComparisonView;
  });
}
