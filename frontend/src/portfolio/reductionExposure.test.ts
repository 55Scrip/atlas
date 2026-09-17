/**
 * Atlas knew, per holding, that AMZN, GOOG, VST and META each carry a
 * supported reduction. What it never said is that they are 21% of the
 * portfolio between them -- a portfolio-level fact that previously
 * required scanning rows for one enum and adding four weights by hand.
 *
 * The fixture below is the real portfolio, with the real weights.
 */

import { describe, expect, it } from "vitest";
import { isReductionSupported, reductionExposure } from "./reductionExposure";
import type { DecisionSupportLevel } from "../status/statusTone";

function holding(ticker: string, weightPercent: number, level: DecisionSupportLevel | null) {
  return { ticker, weightPercent, decisionSupport: level === null ? null : { level } };
}

/** The four reduction-supported holdings and their actual weights. */
const REAL_PORTFOLIO = [
  holding("INVE-B", 9.1758, "insufficient_evidence"),
  holding("MSFT", 7.5636, "thesis_intact"),
  holding("AMZN", 6.6163, "reduction_supported"),
  holding("GOOG", 5.181, "reduction_supported"),
  holding("VST", 4.7083, "reduction_supported"),
  holding("META", 4.4876, "reduction_supported"),
  holding("MA", 2.8784, "increase_supported"),
  holding("TSMC", 4.9565, null),
];

describe("the real portfolio", () => {
  it("adds the four reduction-supported holdings and nothing else", () => {
    const exposure = reductionExposure(REAL_PORTFOLIO);
    expect(exposure.count).toBe(4);
    expect(exposure.tickers).toEqual(["AMZN", "GOOG", "VST", "META"]);
  });

  it("totals the exact weights, not a rounded guess", () => {
    // 6.6163 + 5.181 + 4.7083 + 4.4876
    expect(reductionExposure(REAL_PORTFOLIO).weightPercent).toBeCloseTo(20.9932, 4);
  });

  it("keeps percentage points, never a 0-1 fraction", () => {
    // The ×100 mistake would read as 0.21% of the portfolio, or 2099%.
    const { weightPercent } = reductionExposure(REAL_PORTFOLIO);
    expect(weightPercent).toBeGreaterThan(1);
    expect(weightPercent).toBeLessThan(100);
    expect(weightPercent.toFixed(1)).toBe("21.0");
  });
});

describe("only a supported reduction counts", () => {
  it.each<DecisionSupportLevel>([
    "thesis_intact",
    "insufficient_evidence",
    "entry_supported",
    "increase_supported",
    "no_action_supported",
    "exit_supported",
  ])("%s contributes nothing", (level) => {
    expect(isReductionSupported(level)).toBe(false);
    expect(reductionExposure([holding("X", 50, level)]).weightPercent).toBe(0);
  });

  it("counts reduction_supported", () => {
    expect(isReductionSupported("reduction_supported")).toBe(true);
  });

  it("treats a missing decision as contributing nothing", () => {
    expect(reductionExposure([holding("X", 50, null)])).toEqual({
      count: 0,
      weightPercent: 0,
      tickers: [],
    });
  });

  it("never infers a reduction from anything but the Decision Layer", () => {
    // A poor Portfolio Fit and a high Financial Risk are inputs to a
    // conclusion, not the conclusion. Neither appears in the input type at
    // all, which is the strongest form this guarantee can take -- but the
    // test states it, because the temptation is obvious.
    const poorFitHighRisk = holding("X", 50, "insufficient_evidence");
    expect(reductionExposure([poorFitHighRisk]).count).toBe(0);
  });
});

describe("counting each position once", () => {
  it("does not let a repeated ticker inflate the share", () => {
    const twice = [
      holding("AMZN", 6.6163, "reduction_supported"),
      holding("AMZN", 6.6163, "reduction_supported"),
    ];
    const exposure = reductionExposure(twice);
    expect(exposure.count).toBe(1);
    expect(exposure.weightPercent).toBeCloseTo(6.6163, 4);
  });

  it("still counts every distinct holding", () => {
    expect(reductionExposure(REAL_PORTFOLIO).count).toBe(4);
  });
});

describe("the quiet cases", () => {
  it("reports nothing at all for a portfolio with no supported reductions", () => {
    const calm = REAL_PORTFOLIO.filter((h) => h.decisionSupport?.level !== "reduction_supported");
    expect(reductionExposure(calm)).toEqual({ count: 0, weightPercent: 0, tickers: [] });
  });

  it("handles an empty portfolio", () => {
    expect(reductionExposure([])).toEqual({ count: 0, weightPercent: 0, tickers: [] });
  });

  it("handles exactly one holding", () => {
    const one = reductionExposure([holding("VST", 4.7083, "reduction_supported")]);
    expect(one.count).toBe(1);
    expect(one.tickers).toEqual(["VST"]);
    expect(one.weightPercent).toBeCloseTo(4.7083, 4);
  });
});

describe("it counts, it does not rank", () => {
  it("preserves the portfolio's own order rather than sorting by weight", () => {
    const reordered = [
      holding("META", 4.4876, "reduction_supported"),
      holding("AMZN", 6.6163, "reduction_supported"),
    ];
    expect(reductionExposure(reordered).tickers).toEqual(["META", "AMZN"]);
  });
});
