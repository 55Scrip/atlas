/**
 * Thin typed client for Portfolio Decision Synthesis (Atlas Decision
 * Layer Sprint 8, `atlas/alpha/portfolio_decision/api/`). Field names
 * mirror the backend's own `CamelModel` views exactly. `DecisionAlternativeView`
 * is reused verbatim from `../opportunityCost/opportunityCostApi` --
 * the exact same wire shape, never redeclared. This module adds no
 * logic of its own beyond the wire-format mapping.
 */
import type { DecisionAlternativeView } from "../opportunityCost/opportunityCostApi";

export type PortfolioDecisionCategory =
  | "supports_portfolio"
  | "neutral"
  | "requires_review"
  | "conflicts_with_portfolio"
  | "operationally_limited"
  | "unknown";
export type PortfolioDecisionReasonSource = "portfolio_fit" | "portfolio_intelligence" | "opportunity_cost" | "decision_reliability";
export type PortfolioDecisionReferenceKind = "finding" | "observation" | "reason_code" | "decision_snapshot";

export interface PortfolioDecisionReferenceView {
  kind: PortfolioDecisionReferenceKind;
  id: string;
}

export interface PortfolioDecisionReasonView {
  source: PortfolioDecisionReasonSource;
  reference: PortfolioDecisionReferenceView;
}

export interface PortfolioDecisionImpactView {
  isExistingHolding: boolean;
  currentWeightPercent: number | null;
  isLargestPosition: boolean;
  allocationRating: string | null;
  portfolioConcentrationLevel: string;
}

export interface CapitalCompetitionView {
  caseId: string;
  competingAlternatives: DecisionAlternativeView[];
  nonCompetingAlternatives: DecisionAlternativeView[];
}

export interface PortfolioDecisionView {
  caseId: string;
  action: string;
  category: PortfolioDecisionCategory;
  impact: PortfolioDecisionImpactView;
  capitalCompetition: CapitalCompetitionView;
  supportingReasons: PortfolioDecisionReasonView[];
  limitingReasons: PortfolioDecisionReasonView[];
  primaryLimitingReason: PortfolioDecisionReasonView | null;
  generatedAt: string;
}

export interface PortfolioDecisionChangeView {
  caseId: string;
  previousCategory: PortfolioDecisionCategory;
  currentCategory: PortfolioDecisionCategory;
  competitionChanged: boolean;
  newLimiting: PortfolioDecisionReasonView[];
  resolvedLimiting: PortfolioDecisionReasonView[];
  detectedAt: string;
}

export interface PortfolioDecisionComparisonView {
  a: PortfolioDecisionView;
  b: PortfolioDecisionView;
  betterPortfolioFitCaseId: string | null;
  sharedStrengths: PortfolioDecisionReferenceView[];
  sharedWeaknesses: PortfolioDecisionReferenceView[];
  sharedCompetitorCaseIds: string[];
}

export interface PortfolioSynthesisBreakdownView {
  supportsPortfolio: string[];
  highestCapitalCompetition: string[];
  conflictsWithPortfolio: string[];
  neutral: string[];
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchPortfolioDecision(caseId: string, signal?: AbortSignal): Promise<PortfolioDecisionView> {
  return getJson(`/api/portfolio-decision/${encodeURIComponent(caseId)}`, signal);
}

export function fetchPortfolioDecisionChange(caseId: string, signal?: AbortSignal): Promise<PortfolioDecisionChangeView | null> {
  return getJson(`/api/portfolio-decision/${encodeURIComponent(caseId)}/change`, signal);
}

export function fetchPortfolioSynthesisBreakdown(signal?: AbortSignal): Promise<PortfolioSynthesisBreakdownView> {
  return getJson("/api/portfolio-decision/portfolio/breakdown", signal);
}

export function comparePortfolioDecision(
  tickerA: string,
  tickerB: string,
  signal?: AbortSignal,
): Promise<PortfolioDecisionComparisonView | null> {
  return fetch(`/api/portfolio-decision/compare?tickerA=${encodeURIComponent(tickerA)}&tickerB=${encodeURIComponent(tickerB)}`, {
    signal: signal ?? null,
  }).then(async (response) => {
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
    return (await response.json()) as PortfolioDecisionComparisonView;
  });
}
