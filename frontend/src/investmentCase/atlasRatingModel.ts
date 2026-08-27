import type {
  AnalysisBusinessCategory,
  AnalysisBusinessStatus,
  AnalysisRiskStatus,
} from "../changeIntelligence/describeChange";
import type { AnalysisCoverageLevel, ConfidenceLevel, DecisionSupportLevel } from "../status/statusTone";
import type { FitRating } from "../portfolioFit/portfolioFitApi";

/**
 * Atlas UX Phase 7 (Product Simplification & User Mental Model) --
 * the shared rating vocabulary an investor actually thinks in (Company
 * / Investment / Portfolio / Evidence), meant to eventually appear
 * consistently everywhere Atlas shows a company, not only here on
 * Investment Case. This module owns exactly one thing: turning
 * already-real, already-computed categorical judgments (Business
 * Analysis findings, Decision Support, Portfolio Fit, Knowledge
 * Coverage/Confidence) into one comparable 0-10 number per pillar.
 *
 * **The number is real math over real inputs, never a felt judgment.**
 * Every mapping table below is a fixed, disclosed lookup from an
 * already-existing closed enum to a point value -- the exact same
 * "categorical in, categorical out, never invented" discipline this
 * whole codebase already applies everywhere else, extended one step
 * further so the *display* can be a single comparable number instead
 * of a wall of separate badges. No new backend call, no new analysis:
 * if a real judgment doesn't exist yet for enough of a pillar's inputs,
 * this returns `{ tier: "missing", score: null }` rather than a
 * falsely precise figure -- an investor should see "Not rated yet,"
 * never a confident-looking 6.3 built on data that isn't there.
 */

export type RatingTier = "excellent" | "good" | "fair" | "weak" | "poor";

export interface AtlasRating {
  /** `null` only for `"missing"` (not enough real evaluated input yet)
   * or `"not_applicable"` (the pillar doesn't apply to this case at
   * all -- e.g. Portfolio Rating for a candidate that isn't held). */
  score: number | null;
  tier: RatingTier | "missing" | "not_applicable";
}

const MISSING: AtlasRating = { score: null, tier: "missing" };
const NOT_APPLICABLE: AtlasRating = { score: null, tier: "not_applicable" };

function tierForScore(score: number): RatingTier {
  if (score >= 8.5) return "excellent";
  if (score >= 6.5) return "good";
  if (score >= 4.5) return "fair";
  if (score >= 2.5) return "weak";
  return "poor";
}

function round1(value: number): number {
  return Math.round(value * 10) / 10;
}

/**
 * Company Rating -- quality of the business itself. Averages every
 * `AnalysisBusinessCategory` finding Business Analysis has actually
 * evaluated (`business_model`, `competitive_position`, `management`,
 * `capital_allocation`, `growth`, `durability` -- the real six-category
 * vector `atlas.analysis_engine.business` already computes; together
 * they stand in for the brief's moat/management/capital allocation/
 * profitability/financial strength/competitive-advantage list, not a
 * seventh new dimension). `not_evaluated`/`insufficient_input`
 * categories are excluded from the average rather than scored as zero
 * -- an unevaluated dimension is an absence, not a failing grade.
 * `missing` only when literally none of the six have a real verdict
 * yet.
 */
const BUSINESS_STATUS_POINTS: Partial<Record<AnalysisBusinessStatus, number>> = {
  strong: 10,
  moderate: 6,
  weak: 2,
};

export function deriveCompanyRating(
  findings: { kind: AnalysisBusinessCategory; status: AnalysisBusinessStatus }[],
): AtlasRating {
  const points = findings
    .map((f) => BUSINESS_STATUS_POINTS[f.status])
    .filter((p): p is number => p !== undefined);
  if (points.length === 0) return MISSING;
  const score = round1(points.reduce((sum, p) => sum + p, 0) / points.length);
  return { score, tier: tierForScore(score) };
}

/**
 * Investment Rating -- attractiveness of buying today. Reads Atlas's
 * own single, already-authoritative evidence-support conclusion
 * (`atlas.alpha.decision_support`, the real engine that already
 * weighs valuation, growth, and risk together into one of seven
 * ordered states) rather than re-averaging valuation/growth/risk a
 * second, competing way -- one real signal, one score, never two
 * independent judgments that could disagree. `insufficient_evidence`
 * (Recommendation Withheld) is the one state with no real ordering to
 * place on the scale, so it reports `missing`, exactly matching what
 * the Recommendation badge itself already discloses.
 */
const DECISION_SUPPORT_POINTS: Partial<Record<DecisionSupportLevel, number>> = {
  entry_supported: 9.5,
  increase_supported: 8,
  thesis_intact: 6,
  no_action_supported: 5,
  reduction_supported: 3,
  exit_supported: 1,
};

export function deriveInvestmentRating(level: DecisionSupportLevel): AtlasRating {
  const score = DECISION_SUPPORT_POINTS[level];
  if (score === undefined) return MISSING;
  return { score, tier: tierForScore(score) };
}

/**
 * Portfolio Rating -- how well this investment fits *this* investor's
 * actual portfolio. Reads the real, already-computed Portfolio Fit
 * verdict (`atlas.alpha.portfolio_fit`, the same engine Portfolio's
 * own Opportunities/Weaknesses sections read) verbatim -- never a
 * second fit judgment computed here. `null` (no Portfolio Fit
 * assessment at all -- a candidate that isn't a portfolio holding)
 * is `not_applicable`, a different, more honest fact than "missing
 * evidence": the pillar genuinely doesn't apply yet, since fit is
 * relative to a portfolio the investor doesn't hold this into.
 * `unavailable` (held, but Portfolio Fit itself couldn't evaluate it)
 * is `missing` -- it does apply, Atlas just doesn't have enough yet.
 */
const FIT_RATING_POINTS: Partial<Record<FitRating, number>> = {
  excellent: 9.5,
  good: 7.5,
  neutral: 5.5,
  weak: 3,
  poor: 1,
};

export function derivePortfolioRating(overall: FitRating | null): AtlasRating {
  if (overall === null) return NOT_APPLICABLE;
  const score = FIT_RATING_POINTS[overall];
  if (score === undefined) return MISSING;
  return { score, tier: tierForScore(score) };
}

/**
 * Evidence Rating -- how reliable Atlas's own conclusions are here.
 * Averages Knowledge Coverage's two already-real summary judgments
 * (`overallCoverage`, `overallConfidence` -- `atlas.alpha.coverage`),
 * exactly the two facts `EvidenceCoverageCard` already renders
 * separately. `no_coverage` reports `missing` outright rather than a
 * low-but-defined score: zero coverage means there is nothing yet to
 * rate the reliability *of*, not a rated-and-found-wanting evidence
 * base.
 */
const COVERAGE_POINTS: Partial<Record<AnalysisCoverageLevel, number>> = {
  substantial_coverage: 9,
  partial_coverage: 5,
};

const CONFIDENCE_POINTS: Record<ConfidenceLevel, number> = {
  high: 9,
  moderate: 6,
  limited: 3,
  very_limited: 1,
};

export function deriveEvidenceRating(
  overallCoverage: AnalysisCoverageLevel,
  overallConfidence: ConfidenceLevel,
): AtlasRating {
  const coveragePoints = COVERAGE_POINTS[overallCoverage];
  if (coveragePoints === undefined) return MISSING;
  const score = round1((coveragePoints + CONFIDENCE_POINTS[overallConfidence]) / 2);
  return { score, tier: tierForScore(score) };
}

/**
 * Phase 7A -- Upside and Risk are deliberately *not* 0-10 ratings: the
 * brief's own spec displays them as four qualitative levels
 * (Low/Moderate/High/Very High), independent of each other -- a
 * company can carry Very High Upside and Very High Risk at once. Both
 * are still deterministic reads of real, already-computed data, never
 * a felt judgment.
 */
export type QualitativeLevel = "low" | "moderate" | "high" | "very_high";

export interface AtlasQualitative {
  level: QualitativeLevel | "missing";
}

const QUALITATIVE_MISSING: AtlasQualitative = { level: "missing" };

/**
 * Upside -- reads Long-Term Outlook's own real bull-case return
 * percent (`atlas.analysis_engine.outlook`, the identical figure the
 * Hero's own "Upside/Downside" field already shows) and buckets it
 * into the brief's four tiers. `missing` whenever Long-Term Outlook
 * has no real scenario for this case yet (gapped) -- never a guessed
 * tier standing in for absent evidence. Bucket edges are a disclosed,
 * fixed lookup, not a felt judgment: doubling the position (>=100%)
 * is Very High, a real 1.5x (>=50%) is High, a real 1.2x (>=20%) is
 * Moderate, anything real below that is Low.
 */
export function deriveUpside(bullReturnPercent: number | null): AtlasQualitative {
  if (bullReturnPercent === null) return QUALITATIVE_MISSING;
  if (bullReturnPercent >= 100) return { level: "very_high" };
  if (bullReturnPercent >= 50) return { level: "high" };
  if (bullReturnPercent >= 20) return { level: "moderate" };
  return { level: "low" };
}

/**
 * Risk -- the *worst* real risk finding across Atlas's own four
 * categories (`business_risk`/`financial_risk`/`valuation_risk`/
 * `thesis_risk`), never an average: one severe risk is what an
 * investor needs to see, never diluted by three unrelated calm ones.
 * `"very_high"` is a disclosed aggregation rule over real data, not a
 * fourth backend severity being invented -- the real
 * `AnalysisRiskStatus` enum only has three real levels
 * (low/moderate/high); two or more categories independently landing
 * on `high` at once is what earns the escalation. `missing` only when
 * no category has been evaluated at all.
 */
export function deriveRisk(findings: { status: AnalysisRiskStatus }[]): AtlasQualitative {
  const evaluated = findings.filter(
    (f): f is { status: "low" | "moderate" | "high" } =>
      f.status === "low" || f.status === "moderate" || f.status === "high",
  );
  if (evaluated.length === 0) return QUALITATIVE_MISSING;
  const highCount = evaluated.filter((f) => f.status === "high").length;
  if (highCount >= 2) return { level: "very_high" };
  if (highCount === 1) return { level: "high" };
  if (evaluated.some((f) => f.status === "moderate")) return { level: "moderate" };
  return { level: "low" };
}

/**
 * Horizon -- "when does Atlas expect the thesis to play out," read
 * from Outlook's own real per-horizon month range
 * (`HorizonOutlookView.expectedReturn.horizonMonthsLow/High`), never a
 * fabricated "3-4 quarters." Long-Term is preferred when it has a real
 * (non-gapped) range -- the more durable thesis timeframe -- falling
 * back to Short-Term's own range only when Long-Term itself has none.
 * `missing` when neither horizon clears its own eligibility gate.
 * Evolves for free: this is a read of Outlook's current output, not a
 * persisted value, so the next analysis automatically produces the
 * next Horizon.
 */
export type HorizonBucket = "near_term" | "one_to_two_quarters" | "one_to_two_years" | "three_to_five_years" | "long_term";

export interface AtlasHorizon {
  bucket: HorizonBucket | "missing";
  monthsLow: number | null;
  monthsHigh: number | null;
}

const HORIZON_MISSING: AtlasHorizon = { bucket: "missing", monthsLow: null, monthsHigh: null };

function bucketForMonths(monthsLow: number): HorizonBucket {
  if (monthsLow < 3) return "near_term";
  if (monthsLow < 6) return "one_to_two_quarters";
  if (monthsLow < 24) return "one_to_two_years";
  if (monthsLow < 60) return "three_to_five_years";
  return "long_term";
}

export function deriveHorizon(
  longTermRange: { monthsLow: number; monthsHigh: number } | null,
  shortTermRange: { monthsLow: number; monthsHigh: number } | null,
): AtlasHorizon {
  const chosen = longTermRange ?? shortTermRange;
  if (!chosen) return HORIZON_MISSING;
  return { bucket: bucketForMonths(chosen.monthsLow), monthsLow: chosen.monthsLow, monthsHigh: chosen.monthsHigh };
}
