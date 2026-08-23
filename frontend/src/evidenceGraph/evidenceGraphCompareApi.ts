/**
 * Thin typed client for `GET /evidence-graph/compare` (Atlas
 * Intelligence Sprint 10, Deliverable 9).
 */

export interface EvidenceGraphComparisonSideView {
  ticker: string;
  caseId: string;
  independentObservationChains: number;
  criticalDependencyCount: number;
  weakLinkCount: number;
}

export interface EvidenceGraphComparisonView {
  a: EvidenceGraphComparisonSideView;
  b: EvidenceGraphComparisonSideView;
}

export async function compareEvidenceGraph(
  tickerA: string,
  tickerB: string,
  signal?: AbortSignal,
): Promise<EvidenceGraphComparisonView | null> {
  const response = await fetch(
    `/api/evidence-graph/compare?tickerA=${encodeURIComponent(tickerA)}&tickerB=${encodeURIComponent(tickerB)}`,
    { signal: signal ?? null },
  );
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as EvidenceGraphComparisonView;
}
