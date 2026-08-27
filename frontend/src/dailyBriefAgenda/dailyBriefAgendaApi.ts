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

/** Localization fix (Portfolio live-verification follow-up) -- mirrors
 * `atlas.alpha.portfolio_status.models.AttentionCategory` exactly (six
 * members). Only ever present on a workflow-sourced item
 * (`source === "portfolio_status"`); every other item leaves
 * `attentionCategory`/`attentionCount` on `AgendaItemView` `null`. */
export type AttentionCategory =
  | "MISSING_CASE"
  | "DECISION_WITHOUT_OUTCOME"
  | "OUTCOME_WITHOUT_EXECUTION"
  | "AWAITING_RECONCILIATION"
  | "VERY_OLD_CASE"
  | "OBSERVATION_WITHOUT_DECISION";

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

/** Implementation Sprint B1.1 (Backend Language Cleanup) -- mirrors
 * `atlas.alpha.daily_brief_agenda.reason_facts.ReasonCode` exactly.
 * One member per distinct semantic fact shape the backend has
 * converted; see that module's own docstring for exactly which
 * sources that is, and why the rest still return `null` here. */
export type ReasonCode =
  | "workflow_gap"
  | "missing_evidence"
  | "concentration"
  | "large_unallocated_capital"
  | "executive_change"
  | "management_credibility"
  | "business_quality"
  | "case_condition_status"
  | "assumption_status"
  // Implementation Sprint B1.2 (Engine Reason Localization Contract)
  | "change_intelligence_thesis_impact"
  | "portfolio_fit_verdict"
  | "monitoring_change"
  | "decision_readiness_transition"
  | "investment_decision_transition"
  | "recommendation_conviction_transition"
  | "decision_path_transition"
  | "decision_reliability_transition"
  | "portfolio_decision_transition";

/** A semantic reason payload, never a rendered sentence --
 * `value`/`secondaryValue` are always a closed enum's own value
 * (translate via `describeReasonFact.ts`'s own key maps); `label` is
 * real, already-real free text (a person's name, an investor's own
 * words) that was never system language and must never be
 * translated -- render it verbatim. */
export interface ReasonFactView {
  code: ReasonCode;
  entity: string;
  value: string | null;
  secondaryValue: string | null;
  label: string | null;
  count: number | null;
}

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
  /** Localization fix -- only populated for a workflow-sourced item;
   * see `agendaItemHeadline` in `describeAgendaHeadline.ts` for how
   * this is used to compose a translated `headline` instead of
   * showing the backend's raw English sentence verbatim. */
  attentionCategory: AttentionCategory | null;
  attentionCount: number | null;
  /** Implementation Sprint B1.1 -- parallel to `reason`, same length,
   * same order. `null` at a given index means that reason's own
   * source has not been converted to the semantic-reason-code
   * contract yet; see `describeReasonFact.ts` for how a present entry
   * is translated instead of showing the backend's raw English
   * sentence verbatim. */
  reasonFacts: (ReasonFactView | null)[];
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

/**
 * `userId` is optional and additive (Daily Brief 2.0) -- passing it is
 * what lets the backend durably record any eligible change this call
 * observes into the change log (`dailyBriefChangeLogApi.ts`), since
 * building the agenda is the one moment a real transition is visible
 * before the upstream engines' own diff state self-erases. Omitting it
 * returns the identical `DailyBriefAgendaView` this endpoint has
 * always returned, with no recording side effect.
 */
export async function fetchDailyBriefAgenda(signal?: AbortSignal, userId?: string): Promise<DailyBriefAgendaView> {
  const url = userId ? `/api/daily-brief-agenda?userId=${encodeURIComponent(userId)}` : "/api/daily-brief-agenda";
  const response = await fetch(url, { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as DailyBriefAgendaView;
}
