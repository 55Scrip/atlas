/**
 * Thin typed client for the Stance Engine (Atlas Intelligence Sprint 2,
 * `atlas/alpha/stance/api/`). Field names mirror `StanceView`/
 * `StanceComparisonView` exactly (camelCase, via the backend's own
 * `CamelModel`). This module adds no logic of its own beyond the
 * wire-format mapping.
 *
 * `StanceLevel` deliberately never appears alongside a share count or
 * trade verb anywhere in this codebase -- `increase`/`reduce` name the
 * *direction* of Atlas's current view (strengthening/weakening), never
 * a position-size recommendation. See `atlas.alpha.stance`'s own
 * module docstring.
 */

export type StanceLevel = "increase" | "maintain" | "reduce" | "review" | "wait" | "avoid_decision" | "no_recommendation";

export type StanceReasonCode =
  | "no_company_data"
  | "contradicting_evidence_present"
  | "conviction_insufficient"
  | "confidence_very_limited"
  | "confidence_limited"
  | "confidence_moderate"
  | "thesis_strengthened"
  | "thesis_weakened"
  | "thesis_mixed"
  | "thesis_unchanged"
  | "decision_support_favorable"
  | "decision_support_unfavorable"
  | "decision_support_neutral"
  | "portfolio_fit_weak"
  | "portfolio_fit_favorable"
  | "high_risk_present"
  | "no_high_risk";

export interface StanceReasonView {
  code: StanceReasonCode;
}

export interface StanceView {
  level: StanceLevel;
  reasoning: StanceReasonView[];
  supportingSignals: StanceReasonView[];
  limitingSignals: StanceReasonView[];
  confidence: "high" | "moderate" | "limited" | "very_limited";
  missingInformation: string[];
}

export type StanceComparisonReasonCode =
  | "preferred_has_a_more_favorable_stance"
  | "both_stances_tied"
  | "one_or_both_too_uncertain_to_compare";

export interface StanceComparisonReasonView {
  code: StanceComparisonReasonCode;
  ticker: string | null;
}

export interface StanceComparisonView {
  tickerA: string;
  stanceA: StanceView;
  tickerB: string;
  stanceB: StanceView;
  preferredTicker: string | null;
  reasoning: StanceComparisonReasonView[];
}

export interface TickerStanceView {
  ticker: string;
  stance: StanceView;
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T | null> {
  const response = await fetch(url, { signal: signal ?? null });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchStanceForCase(caseId: string, signal?: AbortSignal): Promise<StanceView | null> {
  return getJson(`/api/stance/case/${encodeURIComponent(caseId)}`, signal);
}

export function fetchStanceForTicker(ticker: string, signal?: AbortSignal): Promise<StanceView | null> {
  return getJson(`/api/stance/ticker/${encodeURIComponent(ticker)}`, signal);
}

export function compareStance(tickerA: string, tickerB: string, signal?: AbortSignal): Promise<StanceComparisonView | null> {
  return getJson(
    `/api/stance/compare?tickerA=${encodeURIComponent(tickerA)}&tickerB=${encodeURIComponent(tickerB)}`,
    signal,
  );
}

export async function fetchStanceForHoldings(signal?: AbortSignal): Promise<TickerStanceView[]> {
  const response = await fetch("/api/stance/holdings", { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as TickerStanceView[];
}

export async function fetchStanceForCandidates(signal?: AbortSignal): Promise<TickerStanceView[]> {
  const response = await fetch("/api/stance/candidates", { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as TickerStanceView[];
}
