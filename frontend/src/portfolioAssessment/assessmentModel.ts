import type { HypotheticalPortfolio } from "../portfolioSimulation/simulationModel";

/**
 * Portfolio Assessment v1 -- what changed in the portfolio, and why.
 *
 * This is the feedback half of portfolio exploration. Sprint 3 made a
 * hypothetical portfolio possible; this answers the question that makes
 * it useful: "what changed because of that?"
 *
 * It is an assessment, not a recommendation. It describes properties of
 * the portfolio. It never says buy, sell, increase or reduce -- those
 * are Decision Layer outputs about a security, and nothing here is
 * qualified to add to them.
 *
 * ONE FUNCTION, TWO PORTFOLIOS
 *
 *     assessPortfolio(current, evidence)      -> PortfolioAssessment
 *     assessPortfolio(hypothetical, evidence) -> PortfolioAssessment
 *     comparePortfolioAssessments(a, b)       -> comparison
 *
 * There is deliberately no separate "simulation" path: the current
 * portfolio is just the hypothetical one with no edits, so a difference
 * between the two can only come from the weights, never from two
 * implementations drifting apart.
 *
 * WHAT IS ASSESSED, AND WHAT IS NOT
 *
 * Three dimensions, each weight-aware and each built from evidence the
 * engine already publishes:
 *
 * - **Concentration**, reusing Atlas's own canonical thresholds from
 *   `atlas/domains/portfolio/calculations.py` verbatim rather than
 *   inventing new ones.
 * - **Valuation-risk exposure** and **financial-risk exposure**, each
 *   the share of portfolio value sitting in positions the risk engine
 *   has already rated high, moderate or low.
 *
 * Deliberately absent, because the data does not exist:
 *
 * - **Sector diversification** -- no sector or industry column exists
 *   anywhere in the database. Portfolio already omits its sector panel
 *   for exactly this reason, and inferring sector from a ticker is the
 *   fabrication that doctrine exists to prevent.
 * - **Geographic diversification** -- `canonical_securities.country`
 *   covers 14 of 25 holdings, 57.8% of weight, and is a *listing venue*
 *   rather than issuer domicile or economic exposure. Worse, the
 *   missing 42% is precisely the Nordic and European holdings, so a
 *   headline drawn from what is present would report a portfolio far
 *   more American than it is. Systematically biased partial coverage is
 *   not partial coverage; it is a wrong answer.
 * - **Expected return, volatility, AI dependency, rate sensitivity** --
 *   no return series, no causal model, no thematic classification. A
 *   number here would be invented, and valuation sensitivity is not an
 *   expected return however convenient the shape.
 *
 * CASH, AND THE DENOMINATOR
 *
 * Every measure is a share of *total portfolio value, cash included* --
 * the same denominator Atlas's own `total_portfolio_value` uses for
 * concentration. It is applied identically to the current and the
 * hypothetical portfolio, so the two are always comparable, and it
 * means moving a position into unallocated capital genuinely reduces
 * that position's risk exposure rather than hiding the change in a
 * shrinking denominator.
 */

/** A risk level as the engine publishes it. `insufficient_input` and
 * `not_applicable` are kept distinct from `low` and from each other:
 * evidence Atlas could not gather is not evidence of safety, and the
 * single most damaging thing this module could do is quietly turn a
 * gap into a clean bill of health. */
export type RiskLevel = "low" | "moderate" | "high" | "insufficient_input" | "not_applicable" | "not_evaluated";

/** One holding's already-published risk verdicts, keyed by the same
 * ticker the hypothetical portfolio uses. Supplied by the caller from
 * the cockpit report; this module never fetches and never re-derives a
 * risk level. */
export interface AssessmentEvidence {
  riskByTicker: Map<string, { valuation: RiskLevel; financial: RiskLevel }>;
}

export type ConcentrationLevel = "low" | "moderate" | "elevated" | "high";

export interface ConcentrationAssessment {
  level: ConcentrationLevel;
  largestTicker: string | null;
  largestWeightPercent: number;
  topFiveWeightPercent: number;
}

/**
 * A risk exposure is reported as numbers, not as a band.
 *
 * Concentration carries a qualitative label because Atlas already has
 * one: the 35/25/75 ladder in `atlas/domains/portfolio/calculations.py`
 * is existing product doctrine. These two exposures have no such
 * doctrine, and inventing "elevated above 15%" here would have created
 * portfolio-risk vocabulary out of a threshold chosen in an afternoon.
 * The share of the portfolio in high-rated holdings is a fact; what
 * counts as too much of it is a judgement Atlas has not made.
 *
 * So the dimension states its numbers and its coverage, and the
 * comparison reads the numeric delta. That is strictly more
 * informative than a band and cannot mislead about a standard that
 * does not exist.
 */
export interface RiskExposureAssessment {
  /** Share of total portfolio value in positions rated high. The
   * headline number, and the one a comparison reads. */
  highWeightPercent: number;
  moderateWeightPercent: number;
  lowWeightPercent: number;
  /** Weight Atlas could not rate -- insufficient evidence or a measure
   * that does not apply. Never folded into `low`. */
  unassessedWeightPercent: number;
  /** Share of portfolio the numbers rest on, as a percentage of total
   * value -- the same denominator as the bands above, so the four add
   * up to the invested share. */
  assessedWeightPercent: number;
  /** Assessed share of *invested* capital. Cash is not an unevaluated
   * holding: it is capital Atlas knows carries no company risk, so
   * parking money there must not read as losing the evidence to assess
   * the portfolio. Reported so a reader can weigh the numbers above
   * against how much of the portfolio they actually describe -- never
   * used to withhold them. */
  coveragePercentOfInvested: number;
  /** Highest-weight positions rated high, largest first. Used for
   * attribution, never for a recommendation. */
  highContributors: { ticker: string; weightPercent: number }[];
}

export interface PortfolioAssessment {
  concentration: ConcentrationAssessment;
  valuationRisk: RiskExposureAssessment;
  financialRisk: RiskExposureAssessment;
}

/**
 * Atlas's own concentration thresholds, from
 * `atlas/domains/portfolio/calculations.py::concentration_level`,
 * reproduced exactly rather than reinvented. Largest position first,
 * top-five as the fallback test, cash inside the denominator.
 */
const LARGEST_HIGH = 35;
const LARGEST_ELEVATED = 25;
const TOP_FIVE_MODERATE = 75;

function assessConcentration(portfolio: HypotheticalPortfolio): ConcentrationAssessment {
  const ranked = [...portfolio.holdings]
    .filter((h) => h.hypotheticalWeightPercent > 0)
    .sort((a, b) => b.hypotheticalWeightPercent - a.hypotheticalWeightPercent);
  const largest = ranked[0] ?? null;
  const largestWeightPercent = largest ? largest.hypotheticalWeightPercent : 0;
  const topFiveWeightPercent = ranked.slice(0, 5).reduce((sum, h) => sum + h.hypotheticalWeightPercent, 0);

  // Atlas's own ladder, in its own order. A position removed in the
  // simulation holds zero and is filtered out above, so it cannot go on
  // counting toward concentration it no longer creates.
  let level: ConcentrationLevel;
  if (largestWeightPercent >= LARGEST_HIGH) level = "high";
  else if (largestWeightPercent >= LARGEST_ELEVATED) level = "elevated";
  else if (topFiveWeightPercent >= TOP_FIVE_MODERATE) level = "moderate";
  else level = "low";

  return {
    level,
    largestTicker: largest ? largest.ticker : null,
    largestWeightPercent,
    topFiveWeightPercent,
  };
}

function assessRiskExposure(
  portfolio: HypotheticalPortfolio,
  levelOf: (ticker: string) => RiskLevel | undefined,
): RiskExposureAssessment {
  let high = 0;
  let moderate = 0;
  let low = 0;
  let unassessed = 0;
  const highContributors: { ticker: string; weightPercent: number }[] = [];

  for (const holding of portfolio.holdings) {
    const weight = holding.hypotheticalWeightPercent;
    // A position taken to zero contributes nothing to any exposure. It
    // is not a holding with a risk any more; it is capital sitting in
    // unallocated.
    if (weight <= 0) continue;
    const level = levelOf(holding.ticker);
    switch (level) {
      case "high":
        high += weight;
        highContributors.push({ ticker: holding.ticker, weightPercent: weight });
        break;
      case "moderate":
        moderate += weight;
        break;
      case "low":
        low += weight;
        break;
      default:
        // `insufficient_input`, `not_applicable`, `not_evaluated`, and
        // a holding with no evidence at all. All unassessed, none of
        // them low.
        unassessed += weight;
    }
  }

  const assessed = high + moderate + low;
  const invested = assessed + unassessed;
  /* Two denominators, each stated and each applied identically to the
     current and the hypothetical portfolio:
       - the exposure bands are shares of TOTAL value, cash included, so
         moving a position into unallocated capital genuinely lowers its
         exposure rather than hiding the change in a shrinking base;
       - coverage is a share of INVESTED value, because the question it
         answers is "of the positions Atlas is assessing, how many does
         it have evidence for" -- and cash is not a position. */
  const coveragePercentOfInvested = invested > 0 ? (assessed / invested) * 100 : 0;
  highContributors.sort((a, b) => b.weightPercent - a.weightPercent);

  return {
    highWeightPercent: high,
    moderateWeightPercent: moderate,
    lowWeightPercent: low,
    unassessedWeightPercent: unassessed,
    assessedWeightPercent: assessed,
    coveragePercentOfInvested,
    highContributors,
  };
}

/** The whole assessment, as one pure function of a portfolio and the
 * evidence already published about its holdings. Nothing is fetched,
 * nothing is cached, and no component state is read. */
export function assessPortfolio(
  portfolio: HypotheticalPortfolio,
  evidence: AssessmentEvidence,
): PortfolioAssessment {
  return {
    concentration: assessConcentration(portfolio),
    valuationRisk: assessRiskExposure(portfolio, (t) => evidence.riskByTicker.get(t)?.valuation),
    financialRisk: assessRiskExposure(portfolio, (t) => evidence.riskByTicker.get(t)?.financial),
  };
}

export type AssessmentDimension = "concentration" | "valuationRisk" | "financialRisk";
export type ChangeDirection = "improved" | "worsened" | "unchanged" | "not_comparable";

export interface DimensionChange {
  dimension: AssessmentDimension;
  direction: ChangeDirection;
  /** The measure the direction is read from, in percentage points of
   * portfolio weight: largest position for concentration, high-risk
   * share for the exposures. */
  currentMeasure: number;
  afterMeasure: number;
  delta: number;
  /** The qualitative band, for the one dimension that has real Atlas
   * doctrine behind it. `null` for the risk exposures, which report
   * numbers instead of a standard Atlas has never set. Never the thing
   * `direction` is computed from -- see `MEANINGFUL_DELTA_PERCENT`. */
  currentLabel: string | null;
  afterLabel: string | null;
  labelChanged: boolean;
}

export interface PortfolioAssessmentComparison {
  current: PortfolioAssessment;
  hypothetical: PortfolioAssessment;
  changes: DimensionChange[];
}

/**
 * How far a measure must move before it is reported as a change.
 *
 * A tenth of a percentage point of portfolio weight. Direction is read
 * from the numeric measure and never from the band, so a shift that
 * happens to tip a label across a threshold without moving the
 * portfolio in any meaningful way reports `unchanged` -- and the two
 * labels are still both shown, so nothing is hidden. Without this, a
 * 0.01pp move could render as a triumphant "improved".
 */
export const MEANINGFUL_DELTA_PERCENT = 0.1;

/** Lower is better for all three dimensions in v1: less concentration,
 * less weight in high valuation risk, less weight in high financial
 * risk. Stated explicitly rather than assumed, because a future
 * dimension (diversification, say) will not share it. */
function directionFor(delta: number): ChangeDirection {
  if (Math.abs(delta) < MEANINGFUL_DELTA_PERCENT) return "unchanged";
  return delta < 0 ? "improved" : "worsened";
}

function compareDimension(
  dimension: AssessmentDimension,
  currentMeasure: number,
  afterMeasure: number,
  currentLabel: string | null,
  afterLabel: string | null,
  comparable: boolean,
): DimensionChange {
  const delta = afterMeasure - currentMeasure;
  return {
    dimension,
    // A dimension that cannot be assessed on either side is not
    // "unchanged" -- there is nothing to compare, and saying otherwise
    // would read as a verdict that it held steady.
    direction: comparable ? directionFor(delta) : "not_comparable",
    currentMeasure,
    afterMeasure,
    delta,
    currentLabel,
    afterLabel,
    labelChanged: currentLabel !== afterLabel,
  };
}

export function comparePortfolioAssessments(
  current: PortfolioAssessment,
  hypothetical: PortfolioAssessment,
): PortfolioAssessmentComparison {
  return {
    current,
    hypothetical,
    changes: [
      compareDimension(
        "concentration",
        current.concentration.largestWeightPercent,
        hypothetical.concentration.largestWeightPercent,
        current.concentration.level,
        hypothetical.concentration.level,
        true,
      ),
      /* No band, so no label. Comparable whenever Atlas has rated
         anything at all on both sides: "0% high" out of nothing rated
         is an absence of evidence, not a clean portfolio, and must not
         read as one. */
      compareDimension(
        "valuationRisk",
        current.valuationRisk.highWeightPercent,
        hypothetical.valuationRisk.highWeightPercent,
        null,
        null,
        current.valuationRisk.assessedWeightPercent > 0 && hypothetical.valuationRisk.assessedWeightPercent > 0,
      ),
      compareDimension(
        "financialRisk",
        current.financialRisk.highWeightPercent,
        hypothetical.financialRisk.highWeightPercent,
        null,
        null,
        current.financialRisk.assessedWeightPercent > 0 && hypothetical.financialRisk.assessedWeightPercent > 0,
      ),
    ],
  };
}

/**
 * Which edited holding moved a dimension most, for attribution.
 *
 * Arithmetic only: the changed position whose own weight change was
 * largest among those that could affect this dimension. It says "this
 * position moved most", never "this is why" in any causal sense --
 * there is no causal model here and this must not imply one.
 *
 * `null` when nothing was edited, or when no edited holding is relevant
 * to the dimension, in which case the row simply offers no attribution
 * rather than reaching for the nearest plausible name.
 */
export function mainContributor(
  portfolio: HypotheticalPortfolio,
  dimension: AssessmentDimension,
  evidence: AssessmentEvidence,
): { ticker: string; baseWeightPercent: number; hypotheticalWeightPercent: number } | null {
  const relevant = portfolio.holdings.filter((holding) => {
    if (!holding.isChanged) return false;
    if (dimension === "concentration") return true;
    const risk = evidence.riskByTicker.get(holding.ticker);
    const level = dimension === "valuationRisk" ? risk?.valuation : risk?.financial;
    // Only a position the engine actually rated high can be named as
    // the mover of a high-risk exposure.
    return level === "high";
  });
  if (relevant.length === 0) return null;
  const top = relevant.reduce((best, h) =>
    Math.abs(h.deltaWeightPercent) > Math.abs(best.deltaWeightPercent) ? h : best,
  );
  return {
    ticker: top.ticker,
    baseWeightPercent: top.baseWeightPercent,
    hypotheticalWeightPercent: top.hypotheticalWeightPercent,
  };
}
