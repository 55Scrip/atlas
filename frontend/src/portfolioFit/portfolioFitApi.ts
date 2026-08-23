/**
 * Thin typed client for the Portfolio Fit Engine (Product Sprint 4,
 * `atlas/alpha/portfolio_fit/api/`). Every field name below mirrors
 * `PortfolioFitAssessmentView`/`FitComparisonView` exactly (camelCase,
 * via the backend's own `CamelModel`). This module adds no logic of its
 * own beyond the wire-format mapping -- ratings are read as the plain
 * strings the backend already computed, never recomputed here.
 */
import type { CoverageAssessmentView } from "../coverage/coverageApi";

export type FitRating = "excellent" | "good" | "neutral" | "weak" | "poor" | "unavailable";

export type FitDimensionKind =
  | "business"
  | "valuation"
  | "risk"
  | "allocation"
  | "expected_contribution"
  | "cash_impact";

export type FitTrend = "improving" | "declining" | "mixed" | "unchanged" | "unavailable";

export interface FitDimensionView {
  kind: FitDimensionKind;
  rating: FitRating;
  reasoning: string[];
  unavailableReason: string | null;
}

export interface PortfolioFitAssessmentView {
  caseId: string;
  ticker: string;
  isExistingHolding: boolean;
  currentWeightPercent: number | null;
  overall: FitRating;
  overallReasoning: string[];
  dimensions: FitDimensionView[];
  trend: FitTrend;
  dataGaps: string[];
  /** Atlas Intelligence Sprint 1 (Data Coverage & Confidence Engine):
   * the same `CoverageAssessmentView` every other surface exposes for
   * this Case -- never read by, or fed into, `overall`/`dimensions`
   * above (presentation only, per that Sprint's own "never ranking,
   * never recommendation" instruction). */
  coverage: CoverageAssessmentView;
  generatedAt: string;
}

export interface FitComparisonView {
  assessmentA: PortfolioFitAssessmentView;
  assessmentB: PortfolioFitAssessmentView;
  preferredTicker: string | null;
  reasoning: string[];
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T | null> {
  const response = await fetch(url, { signal: signal ?? null });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchPortfolioFitForCase(caseId: string, signal?: AbortSignal): Promise<PortfolioFitAssessmentView | null> {
  return getJson(`/api/portfolio-fit/case/${encodeURIComponent(caseId)}`, signal);
}

export function fetchPortfolioFitForTicker(ticker: string, signal?: AbortSignal): Promise<PortfolioFitAssessmentView | null> {
  return getJson(`/api/portfolio-fit/ticker/${encodeURIComponent(ticker)}`, signal);
}

export function comparePortfolioFit(tickerA: string, tickerB: string, signal?: AbortSignal): Promise<FitComparisonView | null> {
  return getJson(
    `/api/portfolio-fit/compare?tickerA=${encodeURIComponent(tickerA)}&tickerB=${encodeURIComponent(tickerB)}`,
    signal,
  );
}

export async function fetchPortfolioFitForHoldings(signal?: AbortSignal): Promise<PortfolioFitAssessmentView[]> {
  const response = await fetch("/api/portfolio-fit/holdings", { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as PortfolioFitAssessmentView[];
}

export async function fetchPortfolioFitForCandidates(signal?: AbortSignal): Promise<PortfolioFitAssessmentView[]> {
  const response = await fetch("/api/portfolio-fit/candidates", { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as PortfolioFitAssessmentView[];
}
