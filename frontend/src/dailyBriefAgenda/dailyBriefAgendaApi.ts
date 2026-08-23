/**
 * Thin typed client for the Daily Brief Agenda (Product Sprint 6,
 * `atlas/alpha/daily_brief_agenda/api/`). Field names mirror
 * `DailyBriefAgendaView`/`AgendaItemView` exactly (camelCase, via the
 * backend's own `CamelModel`). Every value here is read as the plain
 * string/number the backend already computed -- never recomputed.
 */

export type PriorityLevel = "critical" | "high" | "normal" | "low";

export type AgendaItemKind =
  | "review_investment_case"
  | "review_portfolio_position"
  | "review_watchlist_candidate"
  | "compare_candidate"
  | "revisit_assumption"
  | "evaluate_case_condition"
  | "portfolio_risk"
  | "portfolio_opportunity";

export type AgendaGroup = "portfolio" | "watchlist" | "discovery" | "system";

/** Fix Sprint 4 (Daily Brief Signal Quality) -- mirrors
 * `atlas.alpha.daily_brief_agenda.models.SignalNature` exactly. */
export type SignalNature = "change_event" | "persistent_condition";

export type AgendaSource =
  | "change_intelligence"
  | "portfolio_fit"
  | "case_condition"
  | "assumption"
  | "portfolio_status"
  | "portfolio_intelligence"
  | "monitoring"
  // Atlas Decision Layer Sprints 1-8 -- one member per Decision Layer
  // engine's own `change_for_case`-sourced signal (see each one's own
  // docstring on the backend `AgendaSource` enum). Real backend values
  // since each sprint landed; this union simply never grew to include
  // them until this fix -- a pure type-completeness gap, never a live
  // bug, since `item.source` is only ever compared as a plain string,
  // never exhaustively switched over (see `AgendaItemRow.tsx`).
  | "decision_readiness"
  | "investment_decision"
  | "recommendation_conviction"
  | "decision_path"
  | "opportunity_cost"
  | "decision_memory"
  | "decision_explanation"
  | "decision_reliability"
  | "portfolio_decision"
  // Product Intelligence Sprint 1 (Portfolio Intelligence Activation)
  // -- three real Investment Case capabilities newly wired into the
  // Daily Brief Agenda (see `atlas.alpha.daily_brief_agenda.models
  // .AgendaSource`'s own docstring for each).
  | "executive_change"
  | "management_credibility"
  | "business_quality";

export interface AgendaItemView {
  id: string;
  priority: PriorityLevel;
  kind: AgendaItemKind;
  group: AgendaGroup;
  source: AgendaSource;
  headline: string;
  reason: string[];
  /** Fix Sprint 4 -- the nature of the signal that decided `headline`/
   * `kind`/`priority`. */
  nature: SignalNature;
  /** Parallel to `reason` -- same length, same order. */
  reasonNature: SignalNature[];
  /** When the winning signal's own condition began; `null` when Atlas
   * has no real timestamp for it (honest absence, not every source
   * carries one -- see the backend's own `AgendaItem.since` docstring). */
  since: string | null;
  ticker: string | null;
  caseId: string | null;
  portfolioContext: string | null;
  generatedAt: string;
}

export interface PortfolioSummaryView {
  holdingsCount: number;
  criticalCount: number;
  highCount: number;
  watchlistOpportunityCount: number;
  cashWeightPercent: number | null;
  concentrationLevel: string | null;
}

export interface DailyBriefAgendaView {
  generatedAt: string;
  summary: PortfolioSummaryView;
  items: AgendaItemView[];
}

export async function fetchDailyBriefAgenda(signal?: AbortSignal): Promise<DailyBriefAgendaView> {
  const response = await fetch("/api/daily-brief-agenda", { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as DailyBriefAgendaView;
}
