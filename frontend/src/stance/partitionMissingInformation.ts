import type { Translate } from "../changeIntelligence/describeChange";
import { coverageDimensionLabel } from "../coverage/describeCoverage";

/**
 * Data Coverage & Decision Honesty.
 *
 * "Atlas is still missing: FCF Yield (Relative), Valuation, Thesis
 * risk" reads as three things Atlas lacks *about this company*. For
 * `thesis_risk` that is not true of any company: `RiskAnalysisResult`
 * reports it `insufficient_input` for 48 of 48 bound Cases, because no
 * evaluator for it exists yet. Telling an investor that Vistra --
 * or Microsoft, or Meta -- is individually short of thesis-risk
 * evidence states a company fact that is really a gap in Atlas.
 *
 * The two are kept apart rather than one being hidden: a company gap
 * may close when the next refresh runs, and a capability gap will not
 * close until Atlas implements the evaluator. An investor reading
 * "still missing" is entitled to know which kind they are looking at.
 *
 * This list is deliberately explicit and deliberately small. It is not
 * a general mechanism, and it carries an obligation: **when an
 * evaluator ships for one of these dimensions, delete it from here in
 * the same change.** A dimension left here after it becomes real would
 * hide a genuine company-specific gap -- the mirror of the defect this
 * exists to fix. `partitionMissingInformation.test.ts` states that
 * obligation as a test.
 */
export const DIMENSIONS_ATLAS_CANNOT_YET_EVALUATE: readonly string[] = ["thesis_risk"];

export interface PartitionedMissingInformation {
  /** Missing for this company, and obtainable: another refresh, a
   * filing, a price Atlas has not fetched yet. */
  companySpecific: string[];
  /** Not missing for this company in particular -- Atlas has no
   * evaluator for it at all, for anyone. */
  engineUnsupported: string[];
}

export function partitionMissingInformation(missingInformation: readonly string[]): PartitionedMissingInformation {
  const companySpecific: string[] = [];
  const engineUnsupported: string[] = [];
  for (const dimension of missingInformation) {
    (DIMENSIONS_ATLAS_CANNOT_YET_EVALUATE.includes(dimension) ? engineUnsupported : companySpecific).push(dimension);
  }
  return { companySpecific, engineUnsupported };
}

export function describeDimensions(dimensions: readonly string[], t: Translate): string {
  return dimensions.map((dimension) => coverageDimensionLabel(dimension, t)).join(", ");
}
