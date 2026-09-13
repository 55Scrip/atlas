import { describe, expect, it } from "vitest";
import {
  deriveCompanyRating,
  deriveEvidenceRating,
  deriveHorizon,
  deriveInvestmentRating,
  derivePortfolioRating,
  deriveRisk,
  deriveUpside,
} from "./atlasRatingModel";

describe("deriveCompanyRating -- Atlas Product Lock rating specification", () => {
  it("averages every real, evaluated business category and rounds to one decimal", () => {
    const rating = deriveCompanyRating([
      { kind: "growth", status: "strong" },
      { kind: "capital_allocation", status: "moderate" },
    ]);
    expect(rating).toEqual({ score: 8, tier: "good" });
  });

  it("excludes not_evaluated/insufficient_input categories from the average rather than scoring them as zero", () => {
    const rating = deriveCompanyRating([
      { kind: "growth", status: "strong" },
      { kind: "management", status: "not_evaluated" },
      { kind: "durability", status: "insufficient_input" },
    ]);
    expect(rating).toEqual({ score: 10, tier: "excellent" });
  });

  it("is missing only when literally no category has a real verdict yet", () => {
    expect(
      deriveCompanyRating([
        { kind: "growth", status: "not_evaluated" },
        { kind: "management", status: "insufficient_input" },
      ]),
    ).toEqual({ score: null, tier: "missing" });
  });

  it("an empty findings list is also missing, never a fabricated default score", () => {
    expect(deriveCompanyRating([])).toEqual({ score: null, tier: "missing" });
  });

  it("all-weak findings score poor", () => {
    expect(
      deriveCompanyRating([
        { kind: "growth", status: "weak" },
        { kind: "competitive_position", status: "weak" },
      ]),
    ).toEqual({ score: 2, tier: "poor" });
  });
});

describe("deriveInvestmentRating -- reads Decision Support verbatim, never a second valuation judgment", () => {
  it("entry_supported is excellent", () => {
    expect(deriveInvestmentRating("entry_supported")).toEqual({ score: 9.5, tier: "excellent" });
  });

  it("exit_supported is poor", () => {
    expect(deriveInvestmentRating("exit_supported")).toEqual({ score: 1, tier: "poor" });
  });

  it("thesis_intact (hold, nothing changed) lands in the fair band, not neutral-as-missing", () => {
    expect(deriveInvestmentRating("thesis_intact")).toEqual({ score: 6, tier: "fair" });
  });

  it("insufficient_evidence (Recommendation Withheld) is missing, matching what the Recommendation badge itself already discloses", () => {
    expect(deriveInvestmentRating("insufficient_evidence")).toEqual({ score: null, tier: "missing" });
  });
});

describe("derivePortfolioRating -- reads the real Portfolio Fit verdict verbatim", () => {
  it("excellent fit is excellent", () => {
    expect(derivePortfolioRating("excellent")).toEqual({ score: 9.5, tier: "excellent" });
  });

  it("poor fit is poor", () => {
    expect(derivePortfolioRating("poor")).toEqual({ score: 1, tier: "poor" });
  });

  it("unavailable (held, but Portfolio Fit couldn't evaluate it) is missing -- the pillar applies, Atlas just doesn't have enough yet", () => {
    expect(derivePortfolioRating("unavailable")).toEqual({ score: null, tier: "missing" });
  });

  it("null (not a portfolio holding at all) is not_applicable -- a different, more honest fact than missing evidence", () => {
    expect(derivePortfolioRating(null)).toEqual({ score: null, tier: "not_applicable" });
  });
});

describe("deriveEvidenceRating -- averages Knowledge Coverage's own two real summary judgments", () => {
  it("substantial coverage with high confidence is excellent", () => {
    expect(deriveEvidenceRating("substantial_coverage", "high")).toEqual({ score: 9, tier: "excellent" });
  });

  it("partial coverage with limited confidence lands mid-scale", () => {
    expect(deriveEvidenceRating("partial_coverage", "limited")).toEqual({ score: 4, tier: "weak" });
  });

  it("no_coverage is missing outright -- nothing yet to rate the reliability of, not a rated-and-found-wanting evidence base", () => {
    expect(deriveEvidenceRating("no_coverage", "very_limited")).toEqual({ score: null, tier: "missing" });
  });
});

describe("deriveUpside -- the 4-year sensitivity's highest-growth endpoint, compounded, bucketed", () => {
  it("an unavailable or withheld endpoint is missing, never a guessed tier", () => {
    expect(deriveUpside(null, 4)).toEqual({ level: "missing" });
    expect(deriveUpside(0.2, null)).toEqual({ level: "missing" });
  });
  it("buckets the 4-year cumulative figure, not the annual rate", () => {
    // 5%/yr is 21.6% over four years -- moderate, where the annual
    // rate alone would read as low.
    expect(deriveUpside(0.05, 4)).toEqual({ level: "moderate" });
    // 11%/yr is 51.8% over four years -- high.
    expect(deriveUpside(0.11, 4)).toEqual({ level: "high" });
    // 19%/yr doubles the position (100.5%) -- very high.
    expect(deriveUpside(0.19, 4)).toEqual({ level: "very_high" });
  });
  it("under a cumulative 20% is low, including a negative endpoint", () => {
    expect(deriveUpside(0.04, 4)).toEqual({ level: "low" });
    expect(deriveUpside(-0.1, 4)).toEqual({ level: "low" });
  });
  it("reads fractions, never percent numbers", () => {
    // The engine sends 0.35 for +35%; a percent-scaled 35 would be absurd.
    expect(deriveUpside(0.35, 1)).toEqual({ level: "moderate" });
  });
});

describe("deriveRisk -- the worst real risk finding, never an average", () => {
  it("no evaluated category is missing", () => {
    expect(deriveRisk([{ status: "not_evaluated" }, { status: "insufficient_input" }])).toEqual({ level: "missing" });
  });
  it("all low is low", () => {
    expect(deriveRisk([{ status: "low" }, { status: "low" }])).toEqual({ level: "low" });
  });
  it("any moderate (no high) is moderate", () => {
    expect(deriveRisk([{ status: "low" }, { status: "moderate" }])).toEqual({ level: "moderate" });
  });
  it("exactly one high category is high", () => {
    expect(deriveRisk([{ status: "moderate" }, { status: "high" }, { status: "low" }])).toEqual({ level: "high" });
  });
  it("two or more high categories together escalate to very high -- a disclosed aggregation rule, not a fabricated fourth backend severity", () => {
    expect(deriveRisk([{ status: "high" }, { status: "high" }, { status: "low" }])).toEqual({ level: "very_high" });
  });
});

describe("deriveHorizon -- the 4-year sensitivity's own compounding duration, never a bucket", () => {
  it("Long-Term unavailable is missing -- Short-Term's re-rating has no horizon to fall back to", () => {
    expect(deriveHorizon(null)).toEqual({ years: null });
    expect(deriveHorizon({ monthsLow: null, monthsHigh: null })).toEqual({ years: null });
  });
  it("48 months is 4 years", () => {
    expect(deriveHorizon({ monthsLow: 48, monthsHigh: 48 })).toEqual({ years: 4 });
  });
  it("a range that is not one whole number of years is not rounded into one", () => {
    expect(deriveHorizon({ monthsLow: 36, monthsHigh: 60 })).toEqual({ years: null });
    expect(deriveHorizon({ monthsLow: 30, monthsHigh: 30 })).toEqual({ years: null });
  });
});
