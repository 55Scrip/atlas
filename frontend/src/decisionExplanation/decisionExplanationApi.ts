/**
 * Thin typed client for Decision Explanation (Atlas Decision Layer
 * Sprint 6, `atlas/alpha/decision_explanation/api/`). Field names
 * mirror the backend's own `CamelModel` views exactly. This module
 * adds no logic of its own beyond the wire-format mapping.
 */

export type ExplanationReferenceKind = "finding" | "observation" | "reason_code" | "decision_snapshot";
export type ExplanationLayer =
  | "investment_decision"
  | "recommendation_conviction"
  | "decision_readiness"
  | "decision_path"
  | "evidence_graph";
export type ChangeDirection = "stronger" | "weaker" | "unchanged";

export interface ExplanationReferenceView {
  kind: ExplanationReferenceKind;
  id: string;
}

export interface SupportingFindingView {
  reference: ExplanationReferenceView;
  namedBy: ExplanationLayer[];
}

export interface BlockingFindingView {
  reference: ExplanationReferenceView;
  namedBy: ExplanationLayer[];
  isChangeTrigger: boolean;
}

export interface ExplanationSectionView {
  kind: "supporting" | "blocking" | "dependency" | "historical";
  itemCount: number;
}

export interface ExplanationChainView {
  caseId: string;
  order: ExplanationSectionView[];
  supporting: SupportingFindingView[];
  blocking: BlockingFindingView[];
  dependencySteps: ExplanationReferenceView[];
  historicalReference: ExplanationReferenceView | null;
}

export interface DecisionExplanationView {
  caseId: string;
  action: string;
  convictionStrength: string;
  chain: ExplanationChainView;
  primarySupporting: SupportingFindingView | null;
  primaryBlocking: BlockingFindingView | null;
  generatedAt: string;
}

export interface DecisionExplanationChangeView {
  caseId: string;
  newSupporting: SupportingFindingView[];
  resolvedBlocking: BlockingFindingView[];
  newBlocking: BlockingFindingView[];
  evidenceExpanded: boolean;
  convictionDirection: ChangeDirection | null;
  detectedAt: string;
}

export interface DecisionExplanationComparisonView {
  a: DecisionExplanationView;
  b: DecisionExplanationView;
  sharedSupporting: ExplanationReferenceView[];
  differingBlockingA: ExplanationReferenceView[];
  differingBlockingB: ExplanationReferenceView[];
  sharedDependencies: ExplanationReferenceView[];
}

export interface PortfolioDecisionExplanationBreakdownView {
  recentlyChanged: string[];
  newSupportingFindings: string[];
  resolvedBlockers: string[];
  recentlyStrengthened: string[];
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchDecisionExplanation(caseId: string, signal?: AbortSignal): Promise<DecisionExplanationView> {
  return getJson(`/api/decision-explanation/${encodeURIComponent(caseId)}`, signal);
}

export function fetchDecisionExplanationChange(
  caseId: string,
  signal?: AbortSignal,
): Promise<DecisionExplanationChangeView | null> {
  return getJson(`/api/decision-explanation/${encodeURIComponent(caseId)}/change`, signal);
}

export function fetchPortfolioDecisionExplanationBreakdown(
  signal?: AbortSignal,
): Promise<PortfolioDecisionExplanationBreakdownView> {
  return getJson("/api/decision-explanation/portfolio/breakdown", signal);
}

export function compareDecisionExplanation(
  tickerA: string,
  tickerB: string,
  signal?: AbortSignal,
): Promise<DecisionExplanationComparisonView | null> {
  return fetch(`/api/decision-explanation/compare?tickerA=${encodeURIComponent(tickerA)}&tickerB=${encodeURIComponent(tickerB)}`, {
    signal: signal ?? null,
  }).then(async (response) => {
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
    return (await response.json()) as DecisionExplanationComparisonView;
  });
}
