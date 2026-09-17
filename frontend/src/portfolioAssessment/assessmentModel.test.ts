import { describe, expect, it } from "vitest";
import { applyPortfolioEdits, holdingKey, type PortfolioSimulationBase } from "../portfolioSimulation/simulationModel";
import {
  assessPortfolio,
  comparePortfolioAssessments,
  mainContributor,
  MEANINGFUL_DELTA_PERCENT,
  type AssessmentEvidence,
  type RiskLevel,
} from "./assessmentModel";

/** A portfolio shaped like the real one: fully invested, no cash, four
 * positions with distinct risk verdicts including an unassessable one. */
const BASE: PortfolioSimulationBase = {
  holdings: [
    { ticker: "META", caseId: "case-meta", valueAbsolute: 200000, currency: "SEK" },
    { ticker: "VST", caseId: "case-vst", valueAbsolute: 300000, currency: "SEK" },
    { ticker: "MA", caseId: "case-ma", valueAbsolute: 400000, currency: "SEK" },
    { ticker: "ASSA-B", caseId: "case-assa", valueAbsolute: 100000, currency: "SEK" },
  ],
  unallocatedValue: 0,
};
const META = holdingKey({ caseId: "case-meta", ticker: "META" });
const VST = holdingKey({ caseId: "case-vst", ticker: "VST" });
const MA = holdingKey({ caseId: "case-ma", ticker: "MA" });

function evidence(overrides: Record<string, { valuation: RiskLevel; financial: RiskLevel }> = {}): AssessmentEvidence {
  return {
    riskByTicker: new Map(
      Object.entries({
        META: { valuation: "high" as RiskLevel, financial: "low" as RiskLevel },
        VST: { valuation: "high" as RiskLevel, financial: "high" as RiskLevel },
        MA: { valuation: "low" as RiskLevel, financial: "low" as RiskLevel },
        // The honesty control: Atlas could not evaluate this one.
        "ASSA-B": { valuation: "insufficient_input" as RiskLevel, financial: "insufficient_input" as RiskLevel },
        ...overrides,
      }),
    ),
  };
}

const assess = (edits = {}, ev = evidence()) => assessPortfolio(applyPortfolioEdits(BASE, edits), ev);

describe("concentration", () => {
  it("reuses Atlas's own thresholds rather than inventing new ones", () => {
    // MA at 40% of 1,000,000 clears the canonical 35% "high" line from
    // `atlas/domains/portfolio/calculations.py`.
    const a = assess();
    expect(a.concentration.largestTicker).toBe("MA");
    expect(a.concentration.largestWeightPercent).toBeCloseTo(40, 6);
    expect(a.concentration.level).toBe("high");
    expect(a.concentration.topFiveWeightPercent).toBeCloseTo(100, 6);
  });

  it("falls to elevated, then low, as the largest position shrinks", () => {
    expect(assess({ [MA]: 300000 }).concentration.level).toBe("elevated"); // 30%
    // MA to 200,000 leaves VST largest at 30% -- still elevated.
    expect(assess({ [MA]: 200000 }).concentration.level).toBe("elevated");
    // Flatten everything below 25% and the top five no longer reach 75%
    // of a portfolio whose rest is cash.
    const flat = assess({ [META]: 100000, [VST]: 100000, [MA]: 100000 });
    expect(flat.concentration.largestWeightPercent).toBeCloseTo(10, 6);
    expect(flat.concentration.level).toBe("low");
  });

  it("stops counting a position removed in the simulation", () => {
    const a = assess({ [MA]: 0 });
    expect(a.concentration.largestTicker).toBe("VST");
    expect(a.concentration.largestWeightPercent).toBeCloseTo(30, 6);
  });

  it("names no largest position when everything has been sold down", () => {
    // Where the zero-weight guard actually bites. A zero weight
    // contributes zero to any total by arithmetic, so the guard is not
    // load-bearing there -- but without it an all-cash portfolio would
    // still name a holding as its largest position at 0%.
    const a = assess({ [META]: 0, [VST]: 0, [MA]: 0, "case:case-assa": 0 });
    expect(a.concentration.largestTicker).toBeNull();
    expect(a.concentration.largestWeightPercent).toBe(0);
    expect(a.concentration.level).toBe("low");
  });
});

describe("risk exposure", () => {
  it("weights exposure by position size, not by whether a ticker exists", () => {
    const a = assess();
    // META 20% + VST 30% carry high valuation risk.
    expect(a.valuationRisk.highWeightPercent).toBeCloseTo(50, 6);
    // VST alone carries high financial risk.
    expect(a.financialRisk.highWeightPercent).toBeCloseTo(30, 6);
  });

  it("never turns missing evidence into low risk", () => {
    // The single most damaging thing this module could do.
    const a = assess();
    expect(a.valuationRisk.unassessedWeightPercent).toBeCloseTo(10, 6); // ASSA-B
    expect(a.valuationRisk.lowWeightPercent).toBeCloseTo(40, 6); // MA only
    expect(a.valuationRisk.assessedWeightPercent).toBeCloseTo(90, 6);
  });

  it("keeps not_applicable and not_evaluated out of low as well", () => {
    const a = assess({}, evidence({
      MA: { valuation: "not_applicable", financial: "not_evaluated" },
    }));
    expect(a.valuationRisk.lowWeightPercent).toBeCloseTo(0, 6);
    expect(a.valuationRisk.unassessedWeightPercent).toBeCloseTo(50, 6);
    expect(a.financialRisk.lowWeightPercent).toBeCloseTo(20, 6); // META only
  });

  it("reports thin coverage as a number beside the exposure, not as a withheld verdict", () => {
    // Most of the portfolio unassessable. There is no qualitative
    // whole-portfolio verdict to withhold, because the dimension never
    // publishes one -- it states what it measured and how much of the
    // portfolio that covers, and lets the reader weigh them.
    const a = assess({}, evidence({
      VST: { valuation: "insufficient_input", financial: "insufficient_input" },
      MA: { valuation: "insufficient_input", financial: "insufficient_input" },
    }));
    expect(a.valuationRisk.highWeightPercent).toBeCloseTo(20, 6);
    expect(a.valuationRisk.unassessedWeightPercent).toBeCloseTo(80, 6);
    expect(a.valuationRisk.coveragePercentOfInvested).toBeCloseTo(20, 6);
  });

  it("invents no qualitative band for an exposure Atlas has set no standard for", () => {
    // Concentration keeps a label because Atlas's own 35/25/75 ladder
    // is existing doctrine. These two have no doctrine, and a band
    // invented here would have created portfolio-risk vocabulary out of
    // a threshold picked in an afternoon.
    const a = assess();
    expect(Object.keys(a.valuationRisk).sort()).toEqual([
      "assessedWeightPercent",
      "coveragePercentOfInvested",
      "highContributors",
      "highWeightPercent",
      "lowWeightPercent",
      "moderateWeightPercent",
      "unassessedWeightPercent",
    ]);
    expect(a.concentration.level).toBe("high");
  });

  it("drops a removed position out of every exposure", () => {
    const a = assess({ [VST]: 0 });
    expect(a.valuationRisk.highWeightPercent).toBeCloseTo(20, 6); // META only
    expect(a.financialRisk.highWeightPercent).toBeCloseTo(0, 6);
    // And stops being named as a contributor -- the case the zero-weight
    // guard exists for. A removed position contributes zero to the
    // totals by arithmetic, but would otherwise still be listed as
    // driving an exposure it no longer has any part in.
    expect(a.financialRisk.highContributors).toEqual([]);
    expect(a.valuationRisk.highContributors.map((c) => c.ticker)).toEqual(["META"]);
  });

  it("does not lose coverage when capital moves into cash", () => {
    // Regression: coverage was a share of total value, so removing a
    // position pushed the assessed share below the threshold and
    // blacked out the whole dimension -- as though cash were a holding
    // Atlas had failed to evaluate. Cash is capital known to carry no
    // company risk; coverage is therefore a share of invested capital.
    const a = assess({ [VST]: 0 });
    // 60% of total is assessed, but 60 of the 70 still invested is 86%.
    expect(a.valuationRisk.assessedWeightPercent).toBeCloseTo(60, 6);
    expect(a.valuationRisk.coveragePercentOfInvested).toBeCloseTo((60 / 70) * 100, 6);
  });

  it("counts freed capital as unallocated, not as a low-risk holding", () => {
    // Cash is in the denominator but is not a position, so removing VST
    // reduces exposure rather than relabelling it.
    const a = assess({ [VST]: 0 });
    const total =
      a.valuationRisk.highWeightPercent +
      a.valuationRisk.moderateWeightPercent +
      a.valuationRisk.lowWeightPercent +
      a.valuationRisk.unassessedWeightPercent;
    expect(total).toBeCloseTo(70, 6); // the other 30% is cash
  });
});

describe("comparison", () => {
  it("reads direction from the measure, not the band", () => {
    const current = assess();
    const after = assess({ [VST]: 0 });
    const c = comparePortfolioAssessments(current, after);
    const valuation = c.changes.find((x) => x.dimension === "valuationRisk")!;
    expect(valuation.currentMeasure).toBeCloseTo(50, 6);
    expect(valuation.afterMeasure).toBeCloseTo(20, 6);
    expect(valuation.direction).toBe("improved");
    // No band either side: the exposure reports its number, and the
    // direction is read from the number.
    expect(valuation.currentLabel).toBeNull();
    expect(valuation.afterLabel).toBeNull();
    expect(valuation.labelChanged).toBe(false);
  });

  it("does not dramatise a threshold crossed by a hair", () => {
    // The mutation this kills: reading direction off the label, so a
    // 0.01pp shift that tips a band reports a triumphant "improved".
    const base: PortfolioSimulationBase = {
      holdings: [
        { ticker: "A", caseId: "a", valueAbsolute: 150_010, currency: "SEK" },
        { ticker: "B", caseId: "b", valueAbsolute: 849_990, currency: "SEK" },
      ],
      unallocatedValue: 0,
    };
    const ev: AssessmentEvidence = {
      riskByTicker: new Map([
        ["A", { valuation: "high" as RiskLevel, financial: "low" as RiskLevel }],
        ["B", { valuation: "low" as RiskLevel, financial: "low" as RiskLevel }],
      ]),
    };
    const current = assessPortfolio(applyPortfolioEdits(base, {}), ev);
    // Nudge A from 15.001% to 14.999% of the portfolio.
    const after = assessPortfolio(applyPortfolioEdits(base, { "case:a": 149_990 }), ev);
    const change = comparePortfolioAssessments(current, after).changes.find((x) => x.dimension === "valuationRisk")!;
    expect(Math.abs(change.delta)).toBeLessThan(MEANINGFUL_DELTA_PERCENT);
    expect(change.direction).toBe("unchanged");
    // Concentration is the dimension with real bands, and the same
    // floor protects it: a two-thousandths shift may not be dressed up
    // as an improvement just because a doctrine threshold sits nearby.
    const conc = comparePortfolioAssessments(current, after).changes.find((x) => x.dimension === "concentration")!;
    expect(conc.direction).toBe("unchanged");
  });

  it("reports an unassessable dimension as not comparable, never as steady", () => {
    // Nothing rated at all: "0% high" is an absence of evidence, not a
    // clean portfolio, and must never read as one.
    const blind = evidence({
      META: { valuation: "insufficient_input", financial: "insufficient_input" },
      VST: { valuation: "insufficient_input", financial: "insufficient_input" },
      MA: { valuation: "insufficient_input", financial: "insufficient_input" },
      "ASSA-B": { valuation: "insufficient_input", financial: "insufficient_input" },
    });
    const c = comparePortfolioAssessments(assess({}, blind), assess({ [META]: 0 }, blind));
    expect(c.changes.find((x) => x.dimension === "valuationRisk")!.direction).toBe("not_comparable");
  });

  it("is identical to the current assessment when nothing is edited", () => {
    const current = assess();
    const c = comparePortfolioAssessments(current, assess({}));
    expect(c.hypothetical).toEqual(current);
    for (const change of c.changes) {
      expect(change.direction).toBe("unchanged");
      expect(change.delta).toBeCloseTo(0, 9);
      expect(change.labelChanged).toBe(false);
    }
  });

  it("composes multiple edits deterministically, in any order", () => {
    const a = assess({ [META]: 0, [VST]: 150000, [MA]: 500000 });
    const b = assess({ [MA]: 500000, [VST]: 150000, [META]: 0 });
    expect(a).toEqual(b);
  });
});

describe("attribution", () => {
  it("names the edited position that moved most", () => {
    const portfolio = applyPortfolioEdits(BASE, { [META]: 0, [VST]: 280000 });
    const top = mainContributor(portfolio, "valuationRisk", evidence())!;
    // META lost 20 points of weight; VST lost 2.
    expect(top.ticker).toBe("META");
    expect(top.baseWeightPercent).toBeCloseTo(20, 6);
    expect(top.hypotheticalWeightPercent).toBeCloseTo(0, 6);
  });

  it("never names a position the engine did not rate high for that risk", () => {
    // MA is low valuation risk: editing it cannot be what moved a
    // high-valuation-risk exposure, and saying so would be a causal
    // claim this has no basis for.
    const portfolio = applyPortfolioEdits(BASE, { [MA]: 0 });
    expect(mainContributor(portfolio, "valuationRisk", evidence())).toBeNull();
    // It is, however, exactly what moved concentration.
    expect(mainContributor(portfolio, "concentration", evidence())!.ticker).toBe("MA");
  });

  it("offers no attribution when nothing was edited", () => {
    const portfolio = applyPortfolioEdits(BASE, {});
    for (const dimension of ["concentration", "valuationRisk", "financialRisk"] as const) {
      expect(mainContributor(portfolio, dimension, evidence())).toBeNull();
    }
  });
});

describe("no invented thresholds", () => {
  it("carries no qualitative band for the risk exposures, at any exposure level", () => {
    // The guarantee: whatever share of the portfolio sits in high-rated
    // holdings, the dimension answers with that share and never with a
    // word implying a standard Atlas has not set. Swept across the
    // whole range so a band reintroduced at any cut point shows up
    // here, not only at the 15/5 the first draft used.
    for (const metaValue of [0, 50_000, 100_000, 150_000, 200_000]) {
      const a = assess({ [META]: metaValue, [VST]: 0, [MA]: 0 });
      const exposure = a.valuationRisk as unknown as Record<string, unknown>;
      for (const key of Object.keys(exposure)) {
        expect(typeof exposure[key], `${key} must stay numeric or a list`).not.toBe("string");
      }
    }
  });

  it("keeps a qualitative label only where Atlas already has doctrine", () => {
    const a = assess();
    // Concentration: a word, from `calculations.py`'s own ladder.
    expect(typeof a.concentration.level).toBe("string");
    // The exposures: numbers, and a comparison that carries no label.
    const changes = comparePortfolioAssessments(a, assess({ [META]: 0 })).changes;
    const concentration = changes.find((c) => c.dimension === "concentration")!;
    const valuation = changes.find((c) => c.dimension === "valuationRisk")!;
    const financial = changes.find((c) => c.dimension === "financialRisk")!;
    expect(concentration.currentLabel).not.toBeNull();
    expect(valuation.currentLabel).toBeNull();
    expect(valuation.afterLabel).toBeNull();
    expect(financial.currentLabel).toBeNull();
    expect(financial.afterLabel).toBeNull();
  });
});

describe("what this model refuses to assess", () => {
  it("exposes only the three supported dimensions", () => {
    // No expected return, no volatility, no AI dependency, no rate
    // sensitivity, no sector or geographic diversification, and no
    // single overall portfolio score. Each is absent because its data
    // does not exist, not because it was forgotten.
    expect(Object.keys(assess()).sort()).toEqual(["concentration", "financialRisk", "valuationRisk"]);
  });
});
