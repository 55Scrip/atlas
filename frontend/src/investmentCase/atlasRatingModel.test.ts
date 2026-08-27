import { describe, expect, it } from "vitest";
import {
  deriveCompanyRating,
  deriveEvidenceRating,
  deriveInvestmentRating,
  derivePortfolioRating,
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
