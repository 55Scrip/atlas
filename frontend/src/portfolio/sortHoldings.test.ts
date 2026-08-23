import { describe, expect, it } from "vitest";
import { sortHoldings } from "./sortHoldings";

const H = (ticker: string, weightPercent: number) => ({ ticker, weightPercent });

describe("sortHoldings", () => {
  describe("attention (default)", () => {
    it("puts holdings with a flagged priority ahead of holdings with none, ranked critical > high > normal > low", () => {
      const holdings = [H("AAA", 10), H("BBB", 10), H("CCC", 10), H("DDD", 10)];
      const priority = new Map([
        ["BBB", "low" as const],
        ["CCC", "critical" as const],
      ]);
      const result = sortHoldings(holdings, "attention", priority, new Map());
      expect(result.map((h) => h.ticker)).toEqual(["CCC", "BBB", "AAA", "DDD"]);
    });

    it("breaks a tie in priority by weight, then ticker", () => {
      const holdings = [H("SMALL", 5), H("BIG", 40), H("MID", 20)];
      const priority = new Map([
        ["SMALL", "high" as const],
        ["BIG", "high" as const],
        ["MID", "high" as const],
      ]);
      const result = sortHoldings(holdings, "attention", priority, new Map());
      expect(result.map((h) => h.ticker)).toEqual(["BIG", "MID", "SMALL"]);
    });

    it("with no flagged holdings at all, falls back to weight then alphabetical", () => {
      const holdings = [H("ZZZ", 10), H("AAA", 30), H("MMM", 30)];
      const result = sortHoldings(holdings, "attention", new Map(), new Map());
      expect(result.map((h) => h.ticker)).toEqual(["AAA", "MMM", "ZZZ"]);
    });
  });

  describe("weight", () => {
    it("orders largest position first", () => {
      const holdings = [H("A", 5), H("B", 50), H("C", 20)];
      const result = sortHoldings(holdings, "weight", new Map(), new Map());
      expect(result.map((h) => h.ticker)).toEqual(["B", "C", "A"]);
    });
  });

  describe("fit", () => {
    it("orders weakest Portfolio Fit first, unavailable/unassessed last", () => {
      const holdings = [H("EXCELLENT", 10), H("POOR", 10), H("UNASSESSED", 10), H("NEUTRAL", 10)];
      const fit = new Map([
        ["EXCELLENT", "excellent" as const],
        ["POOR", "poor" as const],
        ["NEUTRAL", "neutral" as const],
      ]);
      const result = sortHoldings(holdings, "fit", new Map(), fit);
      expect(result.map((h) => h.ticker)).toEqual(["POOR", "NEUTRAL", "EXCELLENT", "UNASSESSED"]);
    });
  });

  describe("coverage", () => {
    it("orders lowest analysis coverage first, unassessed treated as no_coverage", () => {
      const holdings = [H("SUBSTANTIAL", 10), H("NO_COVERAGE", 10), H("UNASSESSED", 10), H("PARTIAL", 10)];
      const coverage = new Map([
        ["SUBSTANTIAL", "substantial_coverage" as const],
        ["NO_COVERAGE", "no_coverage" as const],
        ["PARTIAL", "partial_coverage" as const],
      ]);
      const result = sortHoldings(holdings, "coverage", new Map(), new Map(), coverage);
      expect(result.map((h) => h.ticker)).toEqual(["NO_COVERAGE", "UNASSESSED", "PARTIAL", "SUBSTANTIAL"]);
    });

    it("breaks a tie in coverage level by ticker", () => {
      const holdings = [H("ZZZ", 10), H("AAA", 10)];
      const coverage = new Map([
        ["ZZZ", "no_coverage" as const],
        ["AAA", "no_coverage" as const],
      ]);
      const result = sortHoldings(holdings, "coverage", new Map(), new Map(), coverage);
      expect(result.map((h) => h.ticker)).toEqual(["AAA", "ZZZ"]);
    });
  });

  describe("stance", () => {
    it("orders the levels needing the most attention first (Atlas Intelligence Sprint 2)", () => {
      const holdings = [H("INCREASE", 10), H("AVOID", 10), H("MAINTAIN", 10), H("REVIEW", 10)];
      const stance = new Map([
        ["INCREASE", "increase" as const],
        ["AVOID", "avoid_decision" as const],
        ["MAINTAIN", "maintain" as const],
        ["REVIEW", "review" as const],
      ]);
      const result = sortHoldings(holdings, "stance", new Map(), new Map(), new Map(), stance);
      expect(result.map((h) => h.ticker)).toEqual(["AVOID", "REVIEW", "MAINTAIN", "INCREASE"]);
    });

    it("treats an unassessed holding the same as no_recommendation", () => {
      const holdings = [H("INCREASE", 10), H("UNASSESSED", 10)];
      const stance = new Map([["INCREASE", "increase" as const]]);
      const result = sortHoldings(holdings, "stance", new Map(), new Map(), new Map(), stance);
      expect(result.map((h) => h.ticker)).toEqual(["UNASSESSED", "INCREASE"]);
    });
  });

  describe("alphabetical", () => {
    it("orders by ticker regardless of weight or priority", () => {
      const holdings = [H("ZETA", 90), H("ALPHA", 5), H("MID", 20)];
      const priority = new Map([["ZETA", "critical" as const]]);
      const result = sortHoldings(holdings, "alphabetical", priority, new Map());
      expect(result.map((h) => h.ticker)).toEqual(["ALPHA", "MID", "ZETA"]);
    });
  });

  it("never mutates the input array", () => {
    const holdings = [H("B", 1), H("A", 2)];
    sortHoldings(holdings, "alphabetical", new Map(), new Map());
    expect(holdings.map((h) => h.ticker)).toEqual(["B", "A"]);
  });
});
