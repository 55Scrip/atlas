/**
 * Thin typed client for Investment Decision Synthesis (Atlas Decision
 * Layer Sprint 1, `atlas/alpha/investment_decision/api/`). Field names
 * mirror the backend's own `CamelModel` views exactly. This module
 * adds no logic of its own beyond the wire-format mapping.
 */

import type { RecommendationReasoningView } from "./reasoningContract";

export type DecisionAction = "buy" | "add" | "hold" | "reduce" | "exit" | "wait" | "no_decision";

export type DecisionReasonSource = "readiness_blocker" | "readiness_support" | "stance";

export type DecisionQualifierKind =
  | "strong_decision"
  | "careful_decision"
  | "temporary_decision"
  | "operationally_delayed"
  | "evidence_limited"
  | "decision_blocked";

export interface DecisionReasonView {
  source: DecisionReasonSource;
  code: string;
}

export interface DecisionQualifierView {
  kind: DecisionQualifierKind;
}

export interface InvestmentDecisionView {
  caseId: string;
  action: DecisionAction;
  qualifiers: DecisionQualifierView[];
  supportingReasons: DecisionReasonView[];
  blockers: DecisionReasonView[];
  changeTrigger: DecisionReasonView | null;
  generatedAt: string;

  /**
   * The canonical analytical rationale the recommendation gate
   * produced, projected verbatim by the backend. Declared here because
   * it was always on the wire and never typed -- the boundary loss
   * that left every component re-explaining its own local state.
   *
   * `null` for a row that predates reasoning persistence, and for an
   * outcome the analysis engine never produced. It is NOT null merely
   * because the recommendation was withheld: a withheld outcome
   * carries the direction-independent half of the same rationale.
   * `action` remains the only field that states what Atlas
   * recommends; nothing in here may be read as a direction.
   *
   * `changeTrigger` above stays a readiness blocker kept for
   * compatibility, and is not a fallback for this field.
   */
  reasoning: RecommendationReasoningView | null;
}

export interface DecisionChangeView {
  caseId: string;
  previousAction: DecisionAction;
  currentAction: DecisionAction;
  previousQualifierKinds: DecisionQualifierKind[];
  currentQualifierKinds: DecisionQualifierKind[];
  detectedAt: string;
}

export interface DecisionComparisonView {
  a: InvestmentDecisionView;
  b: InvestmentDecisionView;
  differingQualifierKinds: DecisionQualifierKind[];
  sharedBlockerCodes: string[];
  sharedSupportingReasonCodes: string[];
}

export interface PortfolioActionDistributionView {
  buy: string[];
  add: string[];
  hold: string[];
  reduce: string[];
  exit: string[];
  wait: string[];
  noDecision: string[];
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchInvestmentDecision(caseId: string, signal?: AbortSignal): Promise<InvestmentDecisionView> {
  return getJson(`/api/investment-decision/${encodeURIComponent(caseId)}`, signal);
}

export function fetchInvestmentDecisionChange(caseId: string, signal?: AbortSignal): Promise<DecisionChangeView | null> {
  return getJson(`/api/investment-decision/${encodeURIComponent(caseId)}/change`, signal);
}

export function fetchPortfolioActionDistribution(signal?: AbortSignal): Promise<PortfolioActionDistributionView> {
  return getJson("/api/investment-decision/portfolio/distribution", signal);
}

export function compareInvestmentDecisions(
  tickerA: string,
  tickerB: string,
  signal?: AbortSignal,
): Promise<DecisionComparisonView | null> {
  return fetch(
    `/api/investment-decision/compare?tickerA=${encodeURIComponent(tickerA)}&tickerB=${encodeURIComponent(tickerB)}`,
    { signal: signal ?? null },
  ).then(async (response) => {
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
    return (await response.json()) as DecisionComparisonView;
  });
}
