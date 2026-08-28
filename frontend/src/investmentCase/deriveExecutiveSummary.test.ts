import { describe, expect, it } from "vitest";
import { deriveRecommendationDrivers } from "./deriveExecutiveSummary";

describe("deriveRecommendationDrivers", () => {
  it("returns an empty list when nothing is decisive", () => {
    expect(deriveRecommendationDrivers({ strengthKinds: [], challengeKinds: [] })).toEqual([]);
  });

  it("tags strengths as supporting and risks as challenging", () => {
    const result = deriveRecommendationDrivers({
      strengthKinds: ["growth"],
      challengeKinds: ["financial_risk"],
    });
    expect(result).toEqual([
      { kind: "growth", direction: "supports" },
      { kind: "financial_risk", direction: "challenges" },
    ]);
  });

  it("caps the combined list at 5, never fabricating or dropping the count silently beyond the cap", () => {
    const result = deriveRecommendationDrivers({
      strengthKinds: ["growth", "capital_allocation", "valuation"],
      challengeKinds: ["business_risk", "financial_risk", "valuation_risk"],
    });
    expect(result).toHaveLength(5);
    expect(result[4]).toEqual({ kind: "financial_risk", direction: "challenges" });
  });

  it("preserves strengths before challenges in the combined ranking", () => {
    const result = deriveRecommendationDrivers({
      strengthKinds: ["valuation"],
      challengeKinds: ["business_risk"],
    });
    expect(result.map((d) => d.direction)).toEqual(["supports", "challenges"]);
  });
});
