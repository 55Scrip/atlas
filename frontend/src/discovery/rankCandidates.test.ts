import { describe, expect, it } from "vitest";
import { rankCandidates, type RankedCandidate } from "./rankCandidates";
import type { PortfolioFitAssessmentView, FitRating } from "../portfolioFit/portfolioFitApi";

function assessment(overall: FitRating, overrides: Partial<PortfolioFitAssessmentView> = {}): PortfolioFitAssessmentView {
  return {
    caseId: "case-1",
    ticker: "AAA",
    isExistingHolding: false,
    currentWeightPercent: null,
    overall,
    overallReasoning: ["Reasoning."],
    dimensions: [],
    trend: "unavailable",
    dataGaps: [],
    coverage: { level: "unavailable", reasoning: [] } as unknown as PortfolioFitAssessmentView["coverage"],
    generatedAt: "2026-08-27T00:00:00Z",
    ...overrides,
  };
}

function candidate(overrides: Partial<RankedCandidate> = {}): RankedCandidate {
  return {
    ticker: "AAA",
    caseId: "case-1",
    assessment: assessment("excellent"),
    stance: null,
    priority: null,
    ...overrides,
  };
}

describe("rankCandidates", () => {
  it("puts excellent Fit with no conflicting Stance in Highest opportunity", () => {
    const result = rankCandidates([candidate({ assessment: assessment("excellent"), stance: "maintain" })]);
    expect(result.highest.map((c) => c.ticker)).toEqual(["AAA"]);
    expect(result.worthReviewing).toEqual([]);
  });

  it("puts good Fit with an increasing Stance in Highest opportunity", () => {
    const result = rankCandidates([candidate({ assessment: assessment("good"), stance: "increase" })]);
    expect(result.highest.map((c) => c.ticker)).toEqual(["AAA"]);
  });

  it("moves a strong Fit with a critical Stance to Worth reviewing, not Highest opportunity (a real tension, not a confident top pick)", () => {
    const result = rankCandidates([candidate({ assessment: assessment("excellent"), stance: "avoid_decision" })]);
    expect(result.highest).toEqual([]);
    expect(result.worthReviewing.map((c) => c.ticker)).toEqual(["AAA"]);
  });

  it("moves a weak Fit with a positive Stance to Worth reviewing", () => {
    const result = rankCandidates([candidate({ assessment: assessment("weak"), stance: "increase" })]);
    expect(result.worthReviewing.map((c) => c.ticker)).toEqual(["AAA"]);
  });

  it("moves a neutral-Fit candidate with an elevated Agenda priority to Worth reviewing", () => {
    const result = rankCandidates([candidate({ assessment: assessment("neutral"), stance: null, priority: "high" })]);
    expect(result.worthReviewing.map((c) => c.ticker)).toEqual(["AAA"]);
  });

  it("puts a weak/poor Fit with no other signal in Everything else", () => {
    const result = rankCandidates([
      candidate({ ticker: "WEAK", assessment: assessment("weak"), stance: "maintain", priority: null }),
      candidate({ ticker: "POOR", assessment: assessment("poor"), stance: null, priority: "low" }),
    ]);
    expect(result.everythingElse.map((c) => c.ticker).sort()).toEqual(["POOR", "WEAK"]);
    expect(result.highest).toEqual([]);
    expect(result.worthReviewing).toEqual([]);
  });

  it("puts an unassessed candidate (assessment null) in Everything else, never fabricating a tier", () => {
    const result = rankCandidates([candidate({ ticker: "NEW", assessment: null })]);
    expect(result.everythingElse.map((c) => c.ticker)).toEqual(["NEW"]);
  });

  it("never pads Highest opportunity below the honest count -- zero qualifying candidates means an empty list", () => {
    const result = rankCandidates([candidate({ assessment: assessment("poor") })]);
    expect(result.highest).toEqual([]);
  });

  it("caps Highest opportunity at 5 and moves the overflow to Worth reviewing, never dropping it", () => {
    const candidates = Array.from({ length: 7 }, (_, i) =>
      candidate({ ticker: `T${i}`, caseId: `case-${i}`, assessment: assessment("excellent", { ticker: `T${i}` }), stance: "maintain" }),
    );
    const result = rankCandidates(candidates);
    expect(result.highest.length).toBe(5);
    expect(result.worthReviewing.length).toBe(2);
    const allTickers = [...result.highest, ...result.worthReviewing].map((c) => c.ticker).sort();
    expect(allTickers).toEqual(["T0", "T1", "T2", "T3", "T4", "T5", "T6"]);
  });

  it("ranks within a tier by Fit first, then Stance, then Agenda priority, then ticker", () => {
    const result = rankCandidates([
      candidate({ ticker: "GOOD_MAINTAIN", assessment: assessment("good"), stance: "maintain" }),
      candidate({ ticker: "EXCELLENT_MAINTAIN", assessment: assessment("excellent"), stance: "maintain" }),
      candidate({ ticker: "EXCELLENT_INCREASE", assessment: assessment("excellent"), stance: "increase" }),
    ]);
    expect(result.highest.map((c) => c.ticker)).toEqual(["EXCELLENT_INCREASE", "EXCELLENT_MAINTAIN", "GOOD_MAINTAIN"]);
  });

  it("breaks a genuine tie alphabetically by ticker, never claiming further differentiation", () => {
    const result = rankCandidates([
      candidate({ ticker: "ZZZ", assessment: assessment("excellent"), stance: "maintain" }),
      candidate({ ticker: "AAA", assessment: assessment("excellent"), stance: "maintain" }),
    ]);
    expect(result.highest.map((c) => c.ticker)).toEqual(["AAA", "ZZZ"]);
  });
});
