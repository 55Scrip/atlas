/**
 * Investment Case Hero (UX-020, APP-002, APP-003): pure, side-effect-free
 * derivation implementing a compressed pass of APP-003's Atlas Thought
 * Model -- Orient / Notice / Weigh / Locate Tension / Compare / Resolve /
 * Decide What To Say -- over data `GET /api/cases/{caseId}/analysis`
 * already returns. No new backend call, no new metric, no fabricated
 * analysis: every classification below reads only already-computed
 * categorical values (Growth/Capital Allocation status, Valuation status,
 * Risk findings, Change Intelligence) and turns them into which *kind* of
 * sentence the Hero paragraph should use -- never the sentence text
 * itself, per this codebase's own established convention
 * (`deriveExecutiveSummary.ts`). The caller renders the actual English/
 * Swedish copy via `t()`.
 *
 * "Weigh" and "Locate Tension" here are `DE-014`'s adopted composition
 * model, applied at the same two dimensions Outlook itself is built from
 * (business trajectory, valuation attractiveness) -- not a new judgment,
 * a frontend read of two categorical fields already on the wire.
 *
 * Full Analytical Standing View persistence (`APP-003` v1.1 §2) does not
 * exist in this codebase yet -- that is real, additive backend work,
 * explicitly out of this implementation's scope ("do not touch Decision
 * Engine logic... no API changes"). Until it exists, "has something
 * changed" below is read from the already-real, already-shipped Change
 * Intelligence feed (`latestChanges`/`isBaselineCase`) rather than a true
 * standing-view comparison -- an honest, available proxy, not a
 * fabrication of the missing infrastructure.
 */

import type {
  AnalysisBusinessStatus,
  AnalysisValuationStatus,
} from "../changeIntelligence/describeChange";
import type { RiskFindingLite } from "./deriveExecutiveSummary";

export type HeroTensionKind =
  | "aligned_positive"
  | "aligned_negative"
  | "business_strong_valuation_weak"
  | "business_weak_valuation_strong"
  | "insufficient";

export interface HeroTensionInput {
  growthStatus: AnalysisBusinessStatus | null;
  capitalAllocationStatus: AnalysisBusinessStatus | null;
  valuationStatus: AnalysisValuationStatus | null;
}

type Signal = "positive" | "negative" | "neutral" | null;

function businessSignal(status: AnalysisBusinessStatus | null): Signal {
  if (status === "strong") return "positive";
  if (status === "weak") return "negative";
  if (status === "moderate") return "neutral";
  return null; // insufficient_input / not_evaluated
}

function valuationSignal(status: AnalysisValuationStatus | null): Signal {
  if (status === "undervalued") return "positive";
  if (status === "expensive") return "negative";
  if (status === "fairly_valued") return "neutral";
  return null;
}

/**
 * Combines Growth and Capital Allocation into one business-trajectory
 * signal: positive if either is strong and neither is weak, negative if
 * either is weak and neither is strong. A genuinely mixed pair (one
 * strong, one weak) is deliberately treated the same as "no clean
 * signal" -- stating a confident business trajectory across a real,
 * internal disagreement would be exactly the collapse `DE-014` §1
 * rejects; the honest v1 scope here is to fall back to `insufficient`
 * rather than silently pick a side.
 */
function combinedBusinessSignal(growth: Signal, capitalAllocation: Signal): Signal {
  const signals = [growth, capitalAllocation].filter((s): s is Exclude<Signal, null> => s !== null);
  if (signals.length === 0) return null;
  const hasPositive = signals.includes("positive");
  const hasNegative = signals.includes("negative");
  if (hasPositive && hasNegative) return null; // genuine internal mix -- fall back honestly
  if (hasPositive) return "positive";
  if (hasNegative) return "negative";
  return "neutral";
}

/**
 * `DE-014`'s composition model (Weigh + Locate Tension), applied to the
 * two dimensions available on the wire today. Never collapses a genuine
 * disagreement into one word; never manufactures tension that isn't
 * there.
 */
export function deriveHeroTension(input: HeroTensionInput): HeroTensionKind {
  const business = combinedBusinessSignal(
    businessSignal(input.growthStatus),
    businessSignal(input.capitalAllocationStatus),
  );
  const valuation = valuationSignal(input.valuationStatus);

  if (business === null) return "insufficient";
  if (business === "positive" && valuation === "negative") return "business_strong_valuation_weak";
  if (business === "negative" && valuation === "positive") return "business_weak_valuation_strong";
  if (business === "positive") return "aligned_positive"; // valuation positive, neutral, or unknown
  if (business === "negative") return "aligned_negative";
  return "insufficient"; // business === "neutral"
}

export interface HeroChangeInput {
  isBaselineCase: boolean;
  latestChangeCount: number;
}

/**
 * "Notice" (`APP-003` step 2), read from the already-real Change
 * Intelligence feed rather than a persisted Analytical Standing View
 * (not yet built -- see file header). A baseline Case (nothing to
 * compare against yet) never claims stability, matching `APP-003` §3's
 * first-contact rule.
 */
export function deriveHeroHasNotableChange(input: HeroChangeInput): boolean {
  if (input.isBaselineCase) return false;
  return input.latestChangeCount > 0;
}

export { findMostSevereRisk } from "./deriveExecutiveSummary";
export type { RiskFindingLite };
