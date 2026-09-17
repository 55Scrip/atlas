/**
 * ASSA-B's hero said "Atlas is still missing: FCF Yield (Relative),
 * Financial, Valuation". "Financial" reads as though Atlas lacks financial
 * statements; it holds four years of ASSA-B's audited accounts. The real
 * reason -- no verified industry classification -- was already in the
 * payload, already translated, and already rendered, near the bottom of a
 * page of several thousand lines.
 */

import { describe, expect, it } from "vitest";
import { describeLineDimensions, describeMissingInformation } from "./describeMissingInformation";
import type { DimensionGap } from "./describeMissingInformation";

/** Enough of the real translation table to prove the wiring; anything
 * absent falls through to `humanize`, exactly as in the app. */
const KEYS: Record<string, string> = {
  "investmentCase.analysis.risk.gap.industryUnknown": "The company's industry is unknown.",
  "investmentCase.analysis.valuation.gap.missingMarketPrice": "Market price is missing.",
  "portfolio.cockpit.risk.category.financial_risk": "Financial",
  "portfolio.cockpit.risk.category.valuation_risk": "Valuation",
};
/** Unknown keys fall back to their last camelCase segment, which is close
 * enough to a real label for these assertions and keeps the test from
 * hard-coding the whole translation table. */
const t = ((key: string) =>
  KEYS[key] ?? (key.split(".").pop() ?? key)) as never;

/** ASSA-B's own `explanation.missingEvidence`, verbatim. */
const ASSA_B: DimensionGap[] = [
  { dimension: "fcf_yield_relative", reasoning: ["missing_market_price", "missing_share_count"] },
  { dimension: "financial_risk", reasoning: ["industry_unknown"] },
  { dimension: "valuation_risk", reasoning: ["valuation_assessment_unavailable"] },
];
const ASSA_B_DIMENSIONS = ["fcf_yield_relative", "financial_risk", "valuation_risk"];

describe("the ASSA-B control", () => {
  it("says why Financial Risk cannot conclude, not merely that it is missing", () => {
    const lines = describeMissingInformation(ASSA_B_DIMENSIONS, ASSA_B, t);
    const financial = lines.find((line) => line.dimensions.includes("financial_risk"));

    expect(financial?.reason).toBe("The company's industry is unknown.");
  });

  it("keeps one line per dimension when the reasons genuinely differ", () => {
    const lines = describeMissingInformation(ASSA_B_DIMENSIONS, ASSA_B, t);
    expect(lines).toHaveLength(3);
    expect(lines.every((line) => line.reason !== null)).toBe(true);
  });

  it("never renders a raw enum", () => {
    const rendered = describeMissingInformation(ASSA_B_DIMENSIONS, ASSA_B, t)
      .map((line) => `${describeLineDimensions(line, t)} ${line.reason}`)
      .join(" ");

    for (const raw of ["industry_unknown", "missing_market_price", "valuation_assessment_unavailable"]) {
      expect(rendered).not.toContain(raw);
    }
  });

  it("does not give the valuation gap Financial Risk's reason", () => {
    const lines = describeMissingInformation(ASSA_B_DIMENSIONS, ASSA_B, t);
    const valuation = lines.find((line) => line.dimensions.includes("valuation_risk"));
    expect(valuation?.reason).not.toBe("The company's industry is unknown.");
  });

  it("uses the first reason when a dimension lists several", () => {
    // `fcf_yield_relative` lists missing_market_price *and*
    // missing_share_count; the panel below has always shown the first, and
    // the hero must not disagree with it.
    const lines = describeMissingInformation(["fcf_yield_relative"], ASSA_B, t);
    expect(lines[0]?.reason).toBe("Market price is missing.");
  });
});

describe("shared reasons", () => {
  it("states one reason once and names every dimension it blocks", () => {
    const gaps: DimensionGap[] = [
      { dimension: "financial_risk", reasoning: ["industry_unknown"] },
      { dimension: "valuation_risk", reasoning: ["industry_unknown"] },
    ];
    const lines = describeMissingInformation(["financial_risk", "valuation_risk"], gaps, t);

    expect(lines).toHaveLength(1);
    expect(lines[0]?.dimensions).toEqual(["financial_risk", "valuation_risk"]);
    expect(describeLineDimensions(lines[0]!, t)).toBe("Financial, Valuation");
  });

  it("does not merge dimensions that merely both lack a reason", () => {
    const lines = describeMissingInformation(["financial_risk", "valuation_risk"], [], t);
    expect(lines).toHaveLength(2);
    expect(lines.every((line) => line.reason === null)).toBe(true);
  });
});

describe("degrading safely", () => {
  it("keeps the dimension when the Case offers no reason for it", () => {
    const lines = describeMissingInformation(["financial_risk"], [], t);
    expect(lines).toEqual([{ dimensions: ["financial_risk"], reason: null }]);
    expect(describeLineDimensions(lines[0]!, t)).toBe("Financial");
  });

  it("keeps the dimension when the reasoning array is empty", () => {
    const lines = describeMissingInformation(
      ["financial_risk"],
      [{ dimension: "financial_risk", reasoning: [] }],
      t,
    );
    expect(lines[0]?.reason).toBeNull();
  });

  it("humanises a reason code from a later build rather than printing it raw", () => {
    const lines = describeMissingInformation(
      ["financial_risk"],
      [{ dimension: "financial_risk", reasoning: ["some_future_reason_code"] }],
      t,
    );
    expect(lines[0]?.reason).not.toBeNull();
    expect(lines[0]?.reason).not.toContain("some_future_reason_code");
  });

  it("ignores reasons for dimensions the stance did not list", () => {
    const lines = describeMissingInformation(["financial_risk"], ASSA_B, t);
    expect(lines).toHaveLength(1);
    expect(lines[0]?.dimensions).toEqual(["financial_risk"]);
  });

  it("says nothing when nothing is missing", () => {
    expect(describeMissingInformation([], ASSA_B, t)).toEqual([]);
  });
});
