import type { AnalysisCoverageLevel, DecisionSupportLevel } from "../status/statusTone";

/**
 * The Watchlist list-composition contract
 * (`GET /api/alpha-watchlist/summary`).
 *
 * Every field is projected from already-persisted Atlas state. This
 * exists because the page previously read company identity from
 * `GET /api/cases/{caseId}/analysis` -- once per entry -- and that
 * endpoint depends on the Alpha Vantage price provider, the quota
 * tracker and the price refresh coordinator, writes an evidence
 * snapshot on every call, and can schedule a background price refresh.
 * Twenty prospects meant twenty provider-touching calls to draw a
 * list.
 *
 * The wire carries canonical enum values, never rendered text, so one
 * canonical state keeps one investor-facing label across Portfolio,
 * Watchlist and Investment Case. Translating them is this layer's job,
 * not the backend's.
 */
export interface WatchlistEntrySummaryView {
  ticker: string;
  caseId: string;
  addedAt: string;
  /** `null` when no company-profile record has been ingested -- the
   * honest absence the backend already expresses, never a guess. */
  companyName: string | null;
  sector: string | null;
  decisionSupportLevel: DecisionSupportLevel;
  analysisCoverageLevel: AnalysisCoverageLevel;
}

export async function fetchWatchlistSummary(signal?: AbortSignal): Promise<WatchlistEntrySummaryView[]> {
  const response = await fetch("/api/alpha-watchlist/summary", { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as WatchlistEntrySummaryView[];
}
