/**
 * Which holding, if any, Portfolio may call today's biggest opportunity.
 *
 * The headline used to be `fitEvaluated[0]` -- the best-ranked Portfolio
 * Fit assessment and nothing else. Fit measures how well a holding suits
 * the portfolio; it is not a statement that Atlas supports doing anything.
 * So Portfolio announced "Today's biggest opportunity: ASSA-B" while
 * ASSA-B's own Investment Case said, in as many words, "There's nothing to
 * act on today" -- its recommendation is withheld for want of an industry
 * classification. Two surfaces, both faithful to their own inputs, telling
 * the investor opposite things.
 *
 * Worse, the answer was already in the data the page had fetched. Exactly
 * one holding carries a positive supported action (MA, `increase_supported`),
 * and it sat second in fit order, behind a Case Atlas cannot conclude on.
 * The rule was not missing information; it was not consulting it.
 *
 * So eligibility is now the Decision Layer's own word, and fit only orders
 * the holdings that pass. Nothing is recomputed here and nothing is ranked
 * by attractiveness: `decisionSupport.level` is read exactly as the engine
 * published it.
 */

import type { DecisionSupportLevel } from "../status/statusTone";

/**
 * The levels that mean Atlas supports putting more capital in.
 *
 * `thesis_intact` is deliberately absent. "The thesis still holds" is a
 * reason not to act, and calling it an opportunity would recreate the same
 * overstatement one rung lower. `insufficient_evidence` and
 * `no_action_supported` are absent for the same reason, more obviously.
 */
const POSITIVE_ACTIONS: ReadonlySet<DecisionSupportLevel> = new Set<DecisionSupportLevel>([
  "entry_supported",
  "increase_supported",
]);

export function supportsPositiveAction(level: DecisionSupportLevel | undefined): boolean {
  return level !== undefined && POSITIVE_ACTIONS.has(level);
}

/** Just enough of `PortfolioFitAssessmentView` to choose between them. */
interface RankedHolding {
  ticker: string;
}

export interface OpportunityHeadline<T extends RankedHolding> {
  /** The holding to name, or `null` when none qualifies and none should
   * be invented. */
  holding: T | null;
  /**
   * `supported_action` -- Atlas supports adding to this holding, and the
   * card may say so.
   *
   * `strongest_setup` -- nothing is actionable today. The best-fitting
   * holding is still worth naming, under wording that does not imply an
   * action, because "nothing to see" would be its own distortion.
   */
  kind: "supported_action" | "strongest_setup";
}

/**
 * `fitOrdered` arrives best-first from `/portfolio-fit/holdings`, already
 * filtered to evaluated holdings -- the same array the page renders below.
 * Order is preserved, never re-sorted: this picks, it does not rank.
 */
export function selectOpportunity<T extends RankedHolding>(
  fitOrdered: readonly T[],
  decisionSupportByTicker: ReadonlyMap<string, DecisionSupportLevel>,
): OpportunityHeadline<T> {
  const actionable = fitOrdered.find((holding) => supportsPositiveAction(decisionSupportByTicker.get(holding.ticker)));
  if (actionable) return { holding: actionable, kind: "supported_action" };
  return { holding: fitOrdered[0] ?? null, kind: "strongest_setup" };
}
