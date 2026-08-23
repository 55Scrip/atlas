/**
 * Thin typed client for `GET /evidence-graph/portfolio/shared-weak-
 * points` (Atlas Intelligence Sprint 10, Deliverable 7).
 */

export interface SharedWeakPointView {
  signature: string;
  caseIds: string[];
  tickers: string[];
}

export interface PortfolioSharedWeakPointsView {
  sharedWeakAssumptions: SharedWeakPointView[];
  sharedConditions: SharedWeakPointView[];
  sharedMissingEvidence: SharedWeakPointView[];
}

export async function fetchPortfolioSharedWeakPoints(signal?: AbortSignal): Promise<PortfolioSharedWeakPointsView> {
  const response = await fetch("/api/evidence-graph/portfolio/shared-weak-points", { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as PortfolioSharedWeakPointsView;
}
