import { describe, expect, it } from "vitest";
import { deriveHeroTension } from "./deriveHeroNarrative";

describe("deriveHeroTension -- Status/Explanation Language stabilization", () => {
  it("a genuinely moderate business signal (both dimensions 'moderate') is 'neutral', not 'insufficient'", () => {
    expect(
      deriveHeroTension({ growthStatus: "moderate", capitalAllocationStatus: "moderate", valuationStatus: "fairly_valued" }),
    ).toBe("neutral");
  });

  it("truly missing business data (both dimensions null) stays 'insufficient' -- unchanged, this is a real data gap", () => {
    expect(
      deriveHeroTension({ growthStatus: null, capitalAllocationStatus: null, valuationStatus: "fairly_valued" }),
    ).toBe("insufficient");
  });

  it("one dimension moderate, the other genuinely missing, is still 'neutral' -- a real moderate signal exists, so this is not a pure data gap", () => {
    expect(
      deriveHeroTension({ growthStatus: "moderate", capitalAllocationStatus: null, valuationStatus: "fairly_valued" }),
    ).toBe("neutral");
  });

  it("a genuine strong/weak mix (real internal disagreement) still falls back to 'insufficient', not 'neutral' -- distinct from a plain moderate reading", () => {
    expect(
      deriveHeroTension({ growthStatus: "strong", capitalAllocationStatus: "weak", valuationStatus: "fairly_valued" }),
    ).toBe("insufficient");
  });

  it("valuation status has no bearing on the neutral/insufficient split -- unchanged for a strong business signal", () => {
    expect(
      deriveHeroTension({ growthStatus: "strong", capitalAllocationStatus: "moderate", valuationStatus: "undervalued" }),
    ).toBe("aligned_positive");
  });
});
