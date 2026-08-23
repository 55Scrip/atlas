import { describe, expect, it } from "vitest";
import { groupCandidatesByTier } from "./groupCandidatesByTier";
import type { PortfolioFitAssessmentView } from "../portfolioFit/portfolioFitApi";
import type { CoverageAssessmentView } from "../coverage/coverageApi";

const EMPTY_COVERAGE: CoverageAssessmentView = {
  dimensions: [],
  overallCoverage: "no_coverage",
  overallConfidence: "very_limited",
  missingDimensions: [],
  notApplicableDimensions: [],
  reasoning: [],
};

function candidate(overrides: Partial<PortfolioFitAssessmentView> = {}): PortfolioFitAssessmentView {
  return {
    caseId: `case-${overrides.ticker ?? "x"}`,
    ticker: "AAA",
    isExistingHolding: false,
    currentWeightPercent: null,
    overall: "good",
    overallReasoning: [],
    dimensions: [],
    trend: "unavailable",
    dataGaps: [],
    coverage: EMPTY_COVERAGE,
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("groupCandidatesByTier", () => {
  it("groups candidates with the same rating into one tier, never splitting them", () => {
    const tiers = groupCandidatesByTier([
      candidate({ ticker: "MSFT", overall: "good" }),
      candidate({ ticker: "AAPL", overall: "good" }),
    ]);
    expect(tiers).toHaveLength(1);
    expect(tiers[0]!.rating).toBe("good");
    expect(tiers[0]!.candidates.map((c) => c.ticker)).toEqual(["AAPL", "MSFT"]);
  });

  it("orders tiers Excellent to Poor, then Unavailable last", () => {
    const tiers = groupCandidatesByTier([
      candidate({ ticker: "A", overall: "poor" }),
      candidate({ ticker: "B", overall: "excellent" }),
      candidate({ ticker: "C", overall: "unavailable" }),
      candidate({ ticker: "D", overall: "neutral" }),
    ]);
    expect(tiers.map((t) => t.rating)).toEqual(["excellent", "neutral", "poor", "unavailable"]);
  });

  it("omits empty tiers entirely rather than rendering a zero-count group", () => {
    const tiers = groupCandidatesByTier([candidate({ ticker: "A", overall: "excellent" })]);
    expect(tiers).toHaveLength(1);
    expect(tiers.some((t) => t.candidates.length === 0)).toBe(false);
  });

  it("returns no tiers for an empty candidate list", () => {
    expect(groupCandidatesByTier([])).toEqual([]);
  });

  it("sorts candidates within a tier alphabetically, never implying a further ranking", () => {
    const tiers = groupCandidatesByTier([
      candidate({ ticker: "TSLA", overall: "neutral" }),
      candidate({ ticker: "AMD", overall: "neutral" }),
      candidate({ ticker: "GOOGL", overall: "neutral" }),
    ]);
    expect(tiers[0]!.candidates.map((c) => c.ticker)).toEqual(["AMD", "GOOGL", "TSLA"]);
  });

  describe("with a Daily Brief Agenda priority map", () => {
    it("puts an Agenda-flagged candidate ahead of unflagged ones in the same tier", () => {
      const tiers = groupCandidatesByTier(
        [
          candidate({ ticker: "AMD", overall: "neutral" }),
          candidate({ ticker: "GOOGL", overall: "neutral" }),
          candidate({ ticker: "TSLA", overall: "neutral" }),
        ],
        new Map([["TSLA", "high"]]),
      );
      expect(tiers[0]!.candidates.map((c) => c.ticker)).toEqual(["TSLA", "AMD", "GOOGL"]);
    });

    it("ranks multiple flagged candidates critical > high > normal > low", () => {
      const tiers = groupCandidatesByTier(
        [
          candidate({ ticker: "A", overall: "good" }),
          candidate({ ticker: "B", overall: "good" }),
          candidate({ ticker: "C", overall: "good" }),
        ],
        new Map([
          ["A", "low"],
          ["B", "critical"],
          ["C", "normal"],
        ]),
      );
      expect(tiers[0]!.candidates.map((c) => c.ticker)).toEqual(["B", "C", "A"]);
    });

    it("with no priority map supplied, behaves exactly as the alphabetical-only default", () => {
      const withoutMap = groupCandidatesByTier([candidate({ ticker: "B", overall: "good" }), candidate({ ticker: "A", overall: "good" })]);
      const withEmptyMap = groupCandidatesByTier(
        [candidate({ ticker: "B", overall: "good" }), candidate({ ticker: "A", overall: "good" })],
        new Map(),
      );
      expect(withoutMap.map((t) => t.candidates.map((c) => c.ticker))).toEqual(withEmptyMap.map((t) => t.candidates.map((c) => c.ticker)));
    });
  });
});
