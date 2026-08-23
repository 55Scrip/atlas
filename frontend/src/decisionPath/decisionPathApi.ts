/**
 * Thin typed client for Decision Path & Required Progress (Atlas
 * Decision Layer Sprint 3, `atlas/alpha/decision_path/api/`). Field
 * names mirror the backend's own `CamelModel` views exactly. This
 * module adds no logic of its own beyond the wire-format mapping.
 */

export type RequiredProgressKind = "operational" | "evidence" | "coverage" | "readiness" | "dependency" | "decision";

export type ReachabilityStatus = "reachable" | "blocked" | "not_reachable";

export type DependencySource = "readiness_blocker" | "readiness_progress";

export type FinalReachableState = "already_reached" | "fully_reachable" | "partially_reachable" | "not_reachable";

export interface DecisionStepView {
  source: DependencySource;
  code: string;
  progressKind: RequiredProgressKind;
  reachability: ReachabilityStatus;
}

export interface DecisionPathView {
  caseId: string;
  currentAction: string;
  currentStrength: string;
  steps: DecisionStepView[];
  immediateBlocker: DecisionStepView | null;
  nextAchievableImprovement: DecisionStepView | null;
  finalReachableState: FinalReachableState;
  generatedAt: string;
}

export interface DecisionPathChangeView {
  caseId: string;
  previousFinalReachableState: FinalReachableState;
  currentFinalReachableState: FinalReachableState;
  resolvedSteps: DecisionStepView[];
  newSteps: DecisionStepView[];
  detectedAt: string;
}

export interface DecisionPathComparisonView {
  a: DecisionPathView;
  b: DecisionPathView;
  shorterPathCaseId: string | null;
  fewerRemainingBlockersCaseId: string | null;
  moreOperationallyDependentCaseId: string | null;
  moreEvidenceDependentCaseId: string | null;
}

export interface PortfolioDecisionPathBreakdownView {
  closestToInvestable: string[];
  operationallyBlocked: string[];
  requiringMoreEvidence: string[];
  requiringDependencyResolution: string[];
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchDecisionPath(caseId: string, signal?: AbortSignal): Promise<DecisionPathView> {
  return getJson(`/api/decision-path/${encodeURIComponent(caseId)}`, signal);
}

export function fetchDecisionPathChange(caseId: string, signal?: AbortSignal): Promise<DecisionPathChangeView | null> {
  return getJson(`/api/decision-path/${encodeURIComponent(caseId)}/change`, signal);
}

export function fetchPortfolioDecisionPathBreakdown(signal?: AbortSignal): Promise<PortfolioDecisionPathBreakdownView> {
  return getJson("/api/decision-path/portfolio/breakdown", signal);
}

export function compareDecisionPaths(
  tickerA: string,
  tickerB: string,
  signal?: AbortSignal,
): Promise<DecisionPathComparisonView | null> {
  return fetch(`/api/decision-path/compare?tickerA=${encodeURIComponent(tickerA)}&tickerB=${encodeURIComponent(tickerB)}`, {
    signal: signal ?? null,
  }).then(async (response) => {
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
    return (await response.json()) as DecisionPathComparisonView;
  });
}
