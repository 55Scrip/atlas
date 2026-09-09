import { describe, expect, it } from "vitest";
import {
  DIMENSIONS_ATLAS_CANNOT_YET_EVALUATE,
  partitionMissingInformation,
} from "./partitionMissingInformation";

/**
 * Data Coverage & Decision Honesty. "Atlas is still missing X" is a
 * claim about a company. It may only be made about things Atlas can
 * actually evaluate for some other company.
 */
describe("partitionMissingInformation", () => {
  it("keeps a genuine company gap as a company gap", () => {
    const result = partitionMissingInformation(["fcf_yield_relative", "valuation_risk"]);
    expect(result.companySpecific).toEqual(["fcf_yield_relative", "valuation_risk"]);
    expect(result.engineUnsupported).toEqual([]);
  });

  /** Measured: `thesis_risk` is `insufficient_input` for 48 of 48 bound
   * Cases, because no evaluator exists. Saying Vistra is short of
   * thesis-risk evidence states a company fact that is really a gap in
   * Atlas. */
  it("does not report a capability Atlas lacks for everyone as a gap in this company", () => {
    const result = partitionMissingInformation(["thesis_risk"]);
    expect(result.companySpecific).toEqual([]);
    expect(result.engineUnsupported).toEqual(["thesis_risk"]);
  });

  it("separates the two rather than hiding either", () => {
    const result = partitionMissingInformation(["fcf_yield_relative", "thesis_risk", "valuation_risk"]);
    expect(result.companySpecific).toEqual(["fcf_yield_relative", "valuation_risk"]);
    expect(result.engineUnsupported).toEqual(["thesis_risk"]);
    // Nothing is dropped: every dimension is still accounted for.
    expect([...result.companySpecific, ...result.engineUnsupported].sort()).toEqual([
      "fcf_yield_relative",
      "thesis_risk",
      "valuation_risk",
    ]);
  });

  it("says nothing when nothing is missing", () => {
    expect(partitionMissingInformation([])).toEqual({ companySpecific: [], engineUnsupported: [] });
  });

  /** The obligation this list carries. It exists only because these
   * dimensions have no evaluator; each one must be deleted from it in
   * the same change that implements one. A dimension left here after
   * it becomes real would hide a genuine company gap. */
  it("names only dimensions Atlas has no evaluator for, and stays small", () => {
    expect(DIMENSIONS_ATLAS_CANNOT_YET_EVALUATE).toEqual(["thesis_risk"]);
  });
});
