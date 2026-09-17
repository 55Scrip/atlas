/**
 * How much a "since your last visit" change deserves the investor's
 * attention -- classification only, never new analysis.
 *
 * The audit that produced this module found eleven changes waiting on the
 * start surface: three holdings whose supported action had moved to
 * *reduce*, and eight European holdings whose portfolio meaning had gone
 * from unknown to operationally limited because Atlas had just ingested
 * their filings. All eleven rendered at the same weight, ordered
 * alphabetically by ticker, with the first three shown and the rest behind
 * a "8 more items" disclosure. Alphabetical order put AMZN's reduce in
 * front and left GOOG's and META's behind the collapse, underneath five
 * coverage diagnostics. A user could read the whole visible brief and miss
 * two of the three things on it that were actually about a decision.
 *
 * Nothing here computes anything. `reasonCode` and `value` already arrive
 * on every entry and already say exactly what kind of change happened; the
 * defect was that the product never asked. This turns those two existing
 * fields into an order.
 *
 * **This ranks kinds of change, never companies.** There is no "best
 * holding" here and must never be: two entries in the same tier are
 * separated by when they were detected and then by ticker, both of which
 * are facts about the event rather than judgements about the security.
 */

import type { ReasonCode } from "./dailyBriefAgendaApi";
import type { ChangeLogEntryView, TickerChangeGroupView } from "./dailyBriefChangeLogApi";

/** Ordered most to least decision-relevant; the numbers are the sort. */
export const SIGNIFICANCE_ORDER = ["action", "review", "information", "diagnostic"] as const;
export type ChangeSignificance = (typeof SIGNIFICANCE_ORDER)[number];

/**
 * The `investment_decision_transition` values that name something the
 * investor could actually do. `hold`, `wait` and `no_decision` are the
 * *absence* of an action and belong with everything else worth reading --
 * a Case going quiet is honest news, not a prompt. Keeping `no_decision`
 * out of this set is what stops a withheld recommendation from being
 * dressed up as urgency.
 */
const DIRECTIONAL_ACTIONS: ReadonlySet<string> = new Set(["buy", "add", "reduce", "exit"]);

/**
 * Everything else, by the kind of question it answers. A code absent from
 * this map is deliberately *not* an error -- see `classifyChange`.
 */
const SIGNIFICANCE_BY_REASON: Partial<Record<ReasonCode, ChangeSignificance>> = {
  // Atlas's own confidence or readiness in a conclusion moved. Worth
  // looking at; not itself a supported action.
  recommendation_conviction_transition: "review",
  decision_readiness_transition: "review",
  decision_reliability_transition: "review",
  decision_path_transition: "review",
  change_intelligence_thesis_impact: "review",
  case_condition_status: "review",
  assumption_status: "review",
  monitoring_change: "review",

  // Real things about the company or the portfolio that do not, on their
  // own, change what Atlas supports doing.
  business_quality: "information",
  executive_change: "information",
  management_credibility: "information",
  concentration: "information",
  large_unallocated_capital: "information",
  portfolio_fit_verdict: "information",
  // The eight European entries from the audit. "What this means for the
  // portfolio changed from unknown to operationally limited" is a true and
  // useful statement, and it is a consequence of evidence arriving rather
  // than of the business moving -- so it stays visible and stops competing
  // with a change in what Atlas supports doing.
  portfolio_decision_transition: "information",

  // Atlas talking about its own coverage and plumbing. Never hidden,
  // always quietest.
  workflow_gap: "diagnostic",
  missing_evidence: "diagnostic",
};

/**
 * Anything unrecognised lands here. It is deliberately not `action`: a
 * reason code this build has never seen is, by definition, one whose
 * urgency nobody has judged, and inventing urgency for it is the one
 * failure mode worse than under-ranking it.
 */
const UNKNOWN_SIGNIFICANCE: ChangeSignificance = "information";

export function classifyChange(entry: ChangeLogEntryView): ChangeSignificance {
  if (entry.reasonCode === "investment_decision_transition") {
    return entry.value !== null && DIRECTIONAL_ACTIONS.has(entry.value) ? "action" : "review";
  }
  return SIGNIFICANCE_BY_REASON[entry.reasonCode] ?? UNKNOWN_SIGNIFICANCE;
}

export function classifyGroup(group: TickerChangeGroupView): ChangeSignificance {
  return classifyChange(group.primary);
}

/**
 * Significance first, then most recently detected, then ticker.
 *
 * Ticker survives only as the last tie-break, where it does what it is
 * good for -- making the order stable between renders -- rather than
 * deciding what the investor sees first. Returns a new array; the caller's
 * payload is never sorted in place, so React sees a stable prop when
 * nothing changed.
 */
export function orderBySignificance(groups: readonly TickerChangeGroupView[]): TickerChangeGroupView[] {
  return [...groups].sort((left, right) => {
    const bySignificance =
      SIGNIFICANCE_ORDER.indexOf(classifyGroup(left)) - SIGNIFICANCE_ORDER.indexOf(classifyGroup(right));
    if (bySignificance !== 0) return bySignificance;
    const byRecency = right.primary.detectedAt.localeCompare(left.primary.detectedAt);
    if (byRecency !== 0) return byRecency;
    return left.ticker.localeCompare(right.ticker);
  });
}

/**
 * How many groups to show before the disclosure.
 *
 * The rule the audit's failure demands: **every action is visible.** The
 * old fixed three was not a bad number, it was a number applied before
 * anything had been ranked, so a collapse boundary that happened to fall
 * between two reduce transitions hid one. With the list ordered, the
 * boundary can only ever fall below the actions.
 *
 * `minimum` keeps a quiet day from looking broken: with no actions at all,
 * the most recent few review/information entries still show, exactly as
 * they did before.
 */
export function visibleCount(
  groups: readonly TickerChangeGroupView[],
  minimum: number,
): number {
  const actions = groups.filter((group) => classifyGroup(group) === "action").length;
  return Math.min(groups.length, Math.max(actions, minimum));
}
