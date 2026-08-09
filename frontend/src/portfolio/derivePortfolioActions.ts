/**
 * ATLAS UI Sprint (Portfolio Action Center): a pure, side-effect-free
 * derivation over data `PortfolioPage.tsx` already fetches from the
 * existing `/api/alpha-portfolio/status` and `/api/alpha-portfolio
 * /intelligence` endpoints — the same "cross-reference what already
 * exists, client-side" pattern `activity/deriveActivity.ts` established
 * for History/Dashboard. No new backend endpoint, no new persisted
 * concept, no new workflow type, and no severity/priority computation
 * that doesn't already exist in some form server-side:
 *
 * - `ReviewQueueItem.topCategory`/`reasonCount` (`portfolio_status
 *   /service.py._build_review_queue`) is already a deduplicated,
 *   counted, deterministically-ordered per-ticker aggregate — this
 *   module reads it as the primary action source rather than
 *   re-deriving anything from the raw `attentionItems` array itself.
 * - `MissingEvidenceItem`/`KeyFinding` are read verbatim; only their
 *   grouping and severity *tier label* (an existing three-level
 *   hierarchy request, not a new numeric score) are computed here.
 *
 * **What "severity" means here.** A fixed, three-tier mapping from
 * each `AttentionCategory` (backend enum, unchanged) to a presentation
 * tier — never a new business rule about what's "risky": pending
 * workflow items that represent unresolved real-world actions
 * (a Decision with no Outcome, an Outcome with no execution recorded,
 * a trade awaiting reconciliation) rank above data-completeness gaps
 * (no Case, evidence gaps, an Observation with no Decision), which
 * rank above staleness/portfolio-structure considerations (an old
 * Case, concentration, unallocated capital). This ordering mirrors
 * `atlas/alpha/portfolio_status/service.py`'s own iteration order for
 * `AttentionItem`s within a holding (decisions checked before
 * observations, before staleness, before reconciliation) — codifying
 * an ordering the backend already implies, not inventing a new one.
 *
 * **One action per ticker.** If the same ticker has both a pending
 * workflow item and an evidence gap (or a concentration finding), this
 * module surfaces exactly one `PortfolioAction` for it — the higher-
 * severity one — with item counts combined, rather than showing the
 * same company more than once (the sprint's own explicit "avoid
 * repeating the same company multiple times" rule).
 */

export type ActionSeverity = "highest" | "high" | "medium";
export type ActionKind = "workflow" | "evidence" | "concentration" | "allocation";

export type AttentionCategory =
  | "MISSING_CASE"
  | "DECISION_WITHOUT_OUTCOME"
  | "OUTCOME_WITHOUT_EXECUTION"
  | "AWAITING_RECONCILIATION"
  | "VERY_OLD_CASE"
  | "OBSERVATION_WITHOUT_DECISION";

export interface ReviewQueueItemLite {
  ticker: string;
  caseId: string | null;
  reasonCount: number;
  topCategory: AttentionCategory;
}

export interface MissingEvidenceItemLite {
  ticker: string;
  caseId: string;
}

/** `age_days` lives on `AttentionItem`, not `ReviewQueueItem`
 * (`atlas/alpha/portfolio_status/models.py`) -- already fetched
 * alongside `reviewQueue` on the same `PortfolioStatusView`, so a
 * `VERY_OLD_CASE` action's reason text can cite the real day count
 * instead of a vague "a while ago." */
export interface AttentionItemLite {
  ticker: string;
  category: AttentionCategory;
  ageDays: number | null;
}

export type ConcentrationFindingKind = "high_concentration" | "elevated_concentration";

export interface KeyFindingLite {
  kind:
    | ConcentrationFindingKind
    | "large_unallocated"
    | "multiple_missing_cases"
    | "multiple_stale_cases"
    | "multiple_evidence_gaps";
  count: number;
  tickers: string[];
}

export interface PortfolioAction {
  id: string;
  severity: ActionSeverity;
  kind: ActionKind;
  ticker: string | null;
  caseId: string | null;
  /** Combined count of underlying items this action represents (pending
   * workflow items, evidence gaps, or both) — `0` for portfolio-level
   * actions that have no per-item count concept (allocation). */
  itemCount: number;
  /** Only set for `kind === "workflow"` — which `AttentionCategory` the
   * action's reason text should describe (the ticker's own
   * `topCategory`, i.e. the first, most-recently-blocking reason found
   * for it). */
  reasonCategory: AttentionCategory | null;
  /** Only meaningful when `reasonCategory === "VERY_OLD_CASE"` — the
   * real age already computed server-side, cross-referenced from the
   * same `PortfolioStatusView.attentionItems` this page already
   * fetches (see `AttentionItemLite`). */
  ageDays: number | null;
  /** Only set for `kind === "concentration"` — which of the two
   * concentration findings applies, so the caller can reuse the
   * existing `portfolio.intelligence.keyFindings.*` translation. */
  concentrationFindingKind: ConcentrationFindingKind | null;
  /** Only set for `kind === "allocation"` — the real unallocated
   * percentage already computed server-side
   * (`PortfolioSummaryMetrics.unallocatedPercent`), never recomputed
   * here. */
  unallocatedPercent: number | null;
}

const SEVERITY_RANK: Record<ActionSeverity, number> = { highest: 3, high: 2, medium: 1 };

/** Mirrors `portfolio_status/service.py`'s own per-holding check order
 * (decisions/outcomes/reconciliation before staleness) — see module
 * docstring. */
const WORKFLOW_SEVERITY: Record<AttentionCategory, ActionSeverity> = {
  DECISION_WITHOUT_OUTCOME: "highest",
  OUTCOME_WITHOUT_EXECUTION: "highest",
  AWAITING_RECONCILIATION: "highest",
  MISSING_CASE: "high",
  OBSERVATION_WITHOUT_DECISION: "high",
  VERY_OLD_CASE: "medium",
};

function mergeAction(byTicker: Map<string, PortfolioAction>, ticker: string, candidate: PortfolioAction): void {
  const existing = byTicker.get(ticker);
  if (!existing) {
    byTicker.set(ticker, candidate);
    return;
  }
  const combinedCount = existing.itemCount + candidate.itemCount;
  const winner = SEVERITY_RANK[candidate.severity] > SEVERITY_RANK[existing.severity] ? candidate : existing;
  const loser = winner === candidate ? existing : candidate;
  byTicker.set(ticker, { ...winner, itemCount: combinedCount, caseId: winner.caseId ?? loser.caseId });
}

/**
 * Groups already-fetched review-queue, evidence-gap, and portfolio-
 * level findings into a deduplicated, severity-ranked action list.
 * `unallocatedPercent` comes from the existing `PortfolioSummaryMetrics`
 * (only read when a `large_unallocated` finding is present — that
 * finding's own presence already encodes the backend's existing
 * threshold decision; this module never re-implements that check).
 */
export function derivePortfolioActions(
  reviewQueue: ReviewQueueItemLite[],
  missingEvidence: MissingEvidenceItemLite[],
  keyFindings: KeyFindingLite[],
  unallocatedPercent: number | null,
  attentionItems: AttentionItemLite[] = [],
): PortfolioAction[] {
  const byTicker = new Map<string, PortfolioAction>();

  const ageDaysByTicker = new Map<string, number>();
  for (const item of attentionItems) {
    if (item.category === "VERY_OLD_CASE" && item.ageDays !== null) {
      ageDaysByTicker.set(item.ticker, item.ageDays);
    }
  }

  for (const item of reviewQueue) {
    byTicker.set(item.ticker, {
      id: `workflow:${item.ticker}`,
      severity: WORKFLOW_SEVERITY[item.topCategory],
      kind: "workflow",
      ticker: item.ticker,
      caseId: item.caseId,
      itemCount: item.reasonCount,
      reasonCategory: item.topCategory,
      ageDays: ageDaysByTicker.get(item.ticker) ?? null,
      concentrationFindingKind: null,
      unallocatedPercent: null,
    });
  }

  const evidenceByTicker = new Map<string, { count: number; caseId: string }>();
  for (const item of missingEvidence) {
    const existing = evidenceByTicker.get(item.ticker);
    evidenceByTicker.set(item.ticker, { count: (existing?.count ?? 0) + 1, caseId: item.caseId });
  }
  for (const [ticker, { count, caseId }] of evidenceByTicker) {
    mergeAction(byTicker, ticker, {
      id: `evidence:${ticker}`,
      severity: "high",
      kind: "evidence",
      ticker,
      caseId,
      itemCount: count,
      reasonCategory: null,
      ageDays: null,
      concentrationFindingKind: null,
      unallocatedPercent: null,
    });
  }

  for (const finding of keyFindings) {
    if (finding.kind === "large_unallocated") {
      byTicker.set("__portfolio_allocation__", {
        id: "allocation",
        severity: "medium",
        kind: "allocation",
        ticker: null,
        caseId: null,
        itemCount: 0,
        reasonCategory: null,
        ageDays: null,
        concentrationFindingKind: null,
        unallocatedPercent,
      });
    } else if (finding.kind === "high_concentration" || finding.kind === "elevated_concentration") {
      const ticker = finding.tickers[0];
      if (!ticker) continue;
      mergeAction(byTicker, ticker, {
        id: `concentration:${ticker}`,
        severity: "medium",
        kind: "concentration",
        ticker,
        caseId: null,
        itemCount: 0,
        reasonCategory: null,
        ageDays: null,
        concentrationFindingKind: finding.kind,
        unallocatedPercent: null,
      });
    }
    // multiple_missing_cases / multiple_stale_cases / multiple_evidence_gaps
    // are aggregate statistics over per-ticker facts already represented
    // above (via reviewQueue / missingEvidence) -- deliberately not
    // turned into a second, duplicate action here. They remain visible,
    // condensed, in the Key Findings section.
  }

  const actions = [...byTicker.values()];
  actions.sort((a, b) => {
    const rankDiff = SEVERITY_RANK[b.severity] - SEVERITY_RANK[a.severity];
    if (rankDiff !== 0) return rankDiff;
    if (b.itemCount !== a.itemCount) return b.itemCount - a.itemCount;
    return (a.ticker ?? "").localeCompare(b.ticker ?? "");
  });
  return actions;
}
