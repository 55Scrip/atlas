import type { TranslationKey } from "../i18n";

/**
 * Sprint 4 (Decision Continuity & History): pure, side-effect-free
 * derivations over data every page already fetches from the existing
 * `/api/decisions`, `/api/outcomes`, `/api/alpha-portfolio/trade-log`,
 * and `/api/alpha-portfolio` endpoints. No new backend endpoint, no new
 * persisted concept — this module only cross-references records that
 * already exist, the same way `InvestmentCasePage.tsx` has always
 * cross-referenced Evidence to Observations client-side.
 *
 * Shared by `HistoryPage.tsx` and `InvestmentCasePage.tsx`'s own
 * Decision Timeline, so the definition of "what happened" and "what
 * still needs attention" lives in exactly one place rather than
 * several slightly-different copies. (`DashboardPage.tsx` also shared
 * this module before it was retired in the Alpha Integration Fix, One
 * Product Pass -- it produced no fact not already owned by Portfolio,
 * Daily Brief, or History.)
 *
 * Deliberately absent: no persisted reconciliation *event* exists
 * anywhere in the backend (`AlphaPortfolioState` carries a single
 * portfolio-level `updatedAt` and each holding a current
 * `reconciliationStatus` — never a dated log of past reconciliations,
 * see `atlas/alpha/portfolio/models.py`). "Portfolio reconciled" is
 * therefore never synthesized as a dated History/Timeline row here —
 * only ever shown as current status, which is the only truthful thing
 * this data supports.
 */

export interface DecisionRecord {
  id: string;
  caseId: string;
  decisionType: string;
  subject: string;
  reason: string;
  confidence: number;
  decidedAt: string;
  recordedAt: string;
}

export interface OutcomeRecord {
  id: string;
  caseId: string;
  decisionId: string;
  statement: string;
  note: string | null;
  occurredAt: string;
  recordedAt: string;
}

export interface TradeLogEntry {
  outcomeId: string;
  decisionId: string;
  security: string;
  transactionType: string;
  quantity: number;
  executionPrice: number;
  fees: number | null;
  executedAt: string;
}

export interface HoldingLite {
  ticker: string;
  caseId: string | null;
  reconciliationStatus: "NONE" | "UPDATED" | "AWAITING_RECONCILIATION";
}

export type ActivityKind = "decision" | "outcome" | "trade";
export type ActivityStatus = "open" | "completed";

export interface ActivityEvent {
  kind: ActivityKind;
  id: string;
  caseId: string | null;
  /** Resolved from the linked holding's ticker when one exists, falling
   * back to the Decision's own recorded `subject` (real, investor-typed
   * text — never invented) when the case isn't (or isn't currently)
   * linked to a portfolio holding. */
  security: string;
  /** BUY / SELL / HOLD / WATCH / PASS — the event's own type for a
   * Decision, or the parent Decision's type for an Outcome, or the raw
   * BUY/SELL transaction type for a Trade. `null` only if a Trade or
   * Outcome references a Decision id this page's own fetch didn't
   * return (never expected in practice, since every list is fetched
   * unfiltered). */
  decisionType: string | null;
  /** ISO timestamp used for sorting and display — decidedAt for a
   * Decision, occurredAt for an Outcome, executedAt for a Trade. */
  date: string;
  status: ActivityStatus;
  /** Existing stored text only: a Decision's own `reason`, an Outcome's
   * own `statement`, or — for a Trade, which has no free-text field at
   * all — a deterministic composition of its own stored quantity and
   * execution price. Never AI-generated. */
  summary: string;
}

/** Every Decision, Outcome, and Trade in the system, cross-referenced
 * into one chronological shape. Callers filter by `caseId` (Investment
 * Case Timeline) or leave unfiltered (History, Dashboard). */
export function deriveActivity(
  decisions: DecisionRecord[],
  outcomes: OutcomeRecord[],
  trades: TradeLogEntry[],
  holdings: HoldingLite[],
): ActivityEvent[] {
  const holdingByCaseId = new Map(
    holdings.filter((h): h is HoldingLite & { caseId: string } => h.caseId !== null).map((h) => [h.caseId, h]),
  );
  const decisionById = new Map(decisions.map((d) => [d.id, d]));
  const outcomeCountByDecisionId = new Map<string, number>();
  for (const o of outcomes) {
    outcomeCountByDecisionId.set(o.decisionId, (outcomeCountByDecisionId.get(o.decisionId) ?? 0) + 1);
  }
  const tradeByOutcomeId = new Map(trades.map((t) => [t.outcomeId, t]));

  const events: ActivityEvent[] = [];

  for (const d of decisions) {
    const holding = holdingByCaseId.get(d.caseId);
    events.push({
      kind: "decision",
      id: `decision:${d.id}`,
      caseId: d.caseId,
      security: holding?.ticker ?? d.subject,
      decisionType: d.decisionType,
      date: d.decidedAt,
      status: (outcomeCountByDecisionId.get(d.id) ?? 0) > 0 ? "completed" : "open",
      summary: d.reason,
    });
  }

  for (const o of outcomes) {
    const decision = decisionById.get(o.decisionId);
    const holding = decision ? holdingByCaseId.get(decision.caseId) : undefined;
    events.push({
      kind: "outcome",
      id: `outcome:${o.id}`,
      caseId: o.caseId,
      security: holding?.ticker ?? decision?.subject ?? o.caseId,
      decisionType: decision?.decisionType ?? null,
      date: o.occurredAt,
      status: "completed",
      summary: o.statement,
    });
  }

  for (const t of trades) {
    const decision = decisionById.get(t.decisionId);
    const holding = holdingByCaseId.get(decision?.caseId ?? "") ?? holdings.find((h) => h.ticker === t.security);
    events.push({
      kind: "trade",
      id: `trade:${t.outcomeId}`,
      caseId: decision?.caseId ?? null,
      security: t.security,
      decisionType: t.transactionType,
      date: t.executedAt,
      status: holding?.reconciliationStatus === "AWAITING_RECONCILIATION" ? "open" : "completed",
      summary: `${t.quantity} @ ${t.executionPrice}`,
    });
  }

  return events;
}

export function sortActivity(events: ActivityEvent[], direction: "newest" | "oldest"): ActivityEvent[] {
  const sorted = [...events].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  return direction === "newest" ? sorted.reverse() : sorted;
}

export type OutstandingWorkKind = "outcome-missing" | "trade-missing" | "reconciliation-needed";

export interface OutstandingWorkItem {
  kind: OutstandingWorkKind;
  id: string;
  caseId: string | null;
  security: string;
  date: string;
}

/**
 * Three deterministic state checks — no scoring, no prioritization, no
 * AI. Each is a direct read of an existing field:
 *
 * - `outcome-missing`: a BUY/SELL Decision with no Outcome recorded yet
 *   (HOLD/WATCH/PASS never expect a trade, so never appear here).
 * - `trade-missing`: an Outcome with no corresponding trade-log entry
 *   (`AlphaTradeLogEntry.outcome_id` is unique per Outcome — its plain
 *   absence is the only signal needed, nothing inferred).
 * - `reconciliation-needed`: a holding whose own
 *   `reconciliationStatus` is already `AWAITING_RECONCILIATION` — an
 *   existing field, read verbatim, not recomputed.
 */
export function deriveOutstandingWork(
  decisions: DecisionRecord[],
  outcomes: OutcomeRecord[],
  trades: TradeLogEntry[],
  holdings: HoldingLite[],
): OutstandingWorkItem[] {
  const holdingByCaseId = new Map(
    holdings.filter((h): h is HoldingLite & { caseId: string } => h.caseId !== null).map((h) => [h.caseId, h]),
  );
  const outcomesByDecisionId = new Map<string, OutcomeRecord[]>();
  for (const o of outcomes) {
    const list = outcomesByDecisionId.get(o.decisionId) ?? [];
    list.push(o);
    outcomesByDecisionId.set(o.decisionId, list);
  }
  const tradeByOutcomeId = new Map(trades.map((t) => [t.outcomeId, t]));

  const items: OutstandingWorkItem[] = [];

  for (const d of decisions) {
    if (d.decisionType !== "BUY" && d.decisionType !== "SELL") continue;
    const holding = holdingByCaseId.get(d.caseId);
    if ((outcomesByDecisionId.get(d.id) ?? []).length === 0) {
      items.push({
        kind: "outcome-missing",
        id: `outcome-missing:${d.id}`,
        caseId: d.caseId,
        security: holding?.ticker ?? d.subject,
        date: d.decidedAt,
      });
    }
  }

  for (const o of outcomes) {
    if (tradeByOutcomeId.has(o.id)) continue;
    const decision = decisions.find((d) => d.id === o.decisionId);
    if (!decision || (decision.decisionType !== "BUY" && decision.decisionType !== "SELL")) continue;
    const holding = holdingByCaseId.get(o.caseId);
    items.push({
      kind: "trade-missing",
      id: `trade-missing:${o.id}`,
      caseId: o.caseId,
      security: holding?.ticker ?? decision.subject,
      date: o.occurredAt,
    });
  }

  for (const h of holdings) {
    if (h.reconciliationStatus === "AWAITING_RECONCILIATION") {
      items.push({
        kind: "reconciliation-needed",
        id: `reconciliation-needed:${h.ticker}`,
        caseId: h.caseId,
        security: h.ticker,
        date: "",
      });
    }
  }

  return items;
}

/**
 * A deterministic, factual date computation — not AI interpretation.
 * Deliberately caps at whole months (Alpha has no data older than a few
 * months yet); a year-scale bucket can be added the same way if that
 * ever becomes real.
 */
export function formatRelativeTime(
  iso: string,
  t: (key: TranslationKey, params?: Record<string, string | number>) => string,
): string {
  const diffDays = Math.floor((Date.now() - new Date(iso).getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays <= 0) return t("relativeTime.today");
  if (diffDays === 1) return t("relativeTime.oneDayAgo");
  if (diffDays < 7) return t("relativeTime.daysAgo", { count: diffDays });
  const weeks = Math.floor(diffDays / 7);
  if (diffDays < 30) return weeks === 1 ? t("relativeTime.oneWeekAgo") : t("relativeTime.weeksAgo", { count: weeks });
  const months = Math.floor(diffDays / 30);
  return months <= 1 ? t("relativeTime.oneMonthAgo") : t("relativeTime.monthsAgo", { count: months });
}
