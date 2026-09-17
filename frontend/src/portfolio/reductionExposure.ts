/**
 * How much of the portfolio currently sits in positions Atlas supports
 * reducing.
 *
 * Atlas has always known this per holding: AMZN, GOOG, VST and META each
 * carry `reduction_supported`, each row says so, and each Case says so.
 * What Portfolio never said is the total -- and at 21% of value that is a
 * portfolio-level fact, not four unrelated position-level ones. Reading it
 * required scanning rows for one enum and adding four weights by hand.
 *
 * Nothing here decides anything. The Decision Layer already published
 * `reduction_supported`; this counts what it published, against the same
 * `weightPercent` the rest of the page already renders.
 *
 * **It is not a sell size.** 21% of the portfolio being held in positions
 * with a supported reduction is a different statement from Atlas
 * recommending that 21% of the portfolio be sold, and the copy this feeds
 * has to keep those apart. Atlas does not size trades anywhere, and this
 * number must never be read as the first one that does.
 */

import type { DecisionSupportLevel } from "../status/statusTone";

/**
 * The one level that counts. Deliberately a single member rather than a
 * "negative-ish" set: `insufficient_evidence` is Atlas declining to
 * conclude, `thesis_intact` is a reason not to act, and a poor Portfolio
 * Fit or a high Financial Risk are inputs to a conclusion rather than the
 * conclusion itself. None of them is a supported reduction, and folding
 * any of them in would inflate a number whose whole value is that it
 * states exactly what the Decision Layer decided.
 */
export function isReductionSupported(level: DecisionSupportLevel | null | undefined): boolean {
  return level === "reduction_supported";
}

interface HoldingLike {
  ticker: string;
  weightPercent: number;
  decisionSupport: { level: DecisionSupportLevel } | null;
}

export interface ReductionExposure {
  /** How many holdings, for the copy's own count grammar. */
  count: number;
  /** Percentage points, same convention as `weightPercent` -- 20.9932 for
   * today's portfolio, never 0.209932. The caller rounds for display. */
  weightPercent: number;
  /** In the order the portfolio supplied them; deliberately not ranked --
   * this answers "how much", never "which is worst". */
  tickers: string[];
}

/**
 * `holdings` must be the portfolio's own holdings list, once. A holding
 * seen twice -- the same ticker arriving through two Cases, or a list
 * concatenated with itself -- is counted once, because the question is
 * what share of the portfolio this is, and a position does not become
 * larger by being listed again.
 */
export function reductionExposure(holdings: readonly HoldingLike[]): ReductionExposure {
  const seen = new Set<string>();
  const tickers: string[] = [];
  let weightPercent = 0;
  for (const holding of holdings) {
    if (!isReductionSupported(holding.decisionSupport?.level)) continue;
    if (seen.has(holding.ticker)) continue;
    seen.add(holding.ticker);
    tickers.push(holding.ticker);
    weightPercent += holding.weightPercent;
  }
  return { count: tickers.length, weightPercent, tickers };
}
