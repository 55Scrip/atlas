/**
 * Portfolio announced "Today's biggest opportunity: ASSA-B" while ASSA-B's
 * own Investment Case said "There's nothing to act on today". The headline
 * was `fitEvaluated[0]` -- best Portfolio Fit, nothing else. Fit says how
 * well a holding suits the portfolio; only the Decision Layer says whether
 * Atlas supports doing anything.
 *
 * The real portfolio below is the one that produced the contradiction:
 * ASSA-B and MTRS fit "excellent" with withheld recommendations, MA fits
 * "excellent" and is the one holding Atlas actually supports adding to,
 * and it sat second.
 */

import { describe, expect, it } from "vitest";
import { selectOpportunity, supportsPositiveAction } from "./opportunityEligibility";
import type { DecisionSupportLevel } from "../status/statusTone";

const holding = (ticker: string) => ({ ticker });

/** Best-first, exactly as `/portfolio-fit/holdings` returns it. */
const FIT_ORDER = ["ASSA-B", "MA", "MTRS", "ALFA", "META", "VST"].map(holding);

const DECISION_SUPPORT = new Map<string, DecisionSupportLevel>([
  ["ASSA-B", "insufficient_evidence"],
  ["MA", "increase_supported"],
  ["MTRS", "insufficient_evidence"],
  ["ALFA", "insufficient_evidence"],
  ["META", "reduction_supported"],
  ["VST", "reduction_supported"],
]);

describe("the ASSA-B contradiction", () => {
  it("does not name a withheld Case as the opportunity", () => {
    const { holding: chosen } = selectOpportunity(FIT_ORDER, DECISION_SUPPORT);
    expect(chosen?.ticker).not.toBe("ASSA-B");
  });

  it("names the holding Atlas actually supports adding to", () => {
    const { holding: chosen, kind } = selectOpportunity(FIT_ORDER, DECISION_SUPPORT);
    expect(chosen?.ticker).toBe("MA");
    expect(kind).toBe("supported_action");
  });

  it("still prefers fit order among holdings that qualify", () => {
    const twoActionable = new Map(DECISION_SUPPORT).set("ASSA-B", "entry_supported");
    // ASSA-B fits better than MA, and now both are actionable.
    expect(selectOpportunity(FIT_ORDER, twoActionable).holding?.ticker).toBe("ASSA-B");
  });
});

describe("what counts as a supported action", () => {
  it.each<DecisionSupportLevel>(["entry_supported", "increase_supported"])("%s qualifies", (level) => {
    expect(supportsPositiveAction(level)).toBe(true);
  });

  it.each<DecisionSupportLevel>([
    "thesis_intact",
    "no_action_supported",
    "insufficient_evidence",
    "reduction_supported",
    "exit_supported",
  ])("%s does not qualify", (level) => {
    expect(supportsPositiveAction(level)).toBe(false);
  });

  it("treats an unknown holding as not actionable", () => {
    expect(supportsPositiveAction(undefined)).toBe(false);
  });

  it("never turns a reduction into the positive headline", () => {
    const onlyReductions = new Map<string, DecisionSupportLevel>([
      ["META", "reduction_supported"],
      ["VST", "reduction_supported"],
    ]);
    const { kind } = selectOpportunity([holding("META"), holding("VST")], onlyReductions);
    expect(kind).toBe("strongest_setup");
  });

  it("never turns 'the thesis still holds' into a reason to add", () => {
    // MSFT, NVDA and AMAT are `thesis_intact`: a reason not to act.
    const intact = new Map<string, DecisionSupportLevel>([["MSFT", "thesis_intact"]]);
    expect(selectOpportunity([holding("MSFT")], intact).kind).toBe("strongest_setup");
  });
});

describe("when nothing is actionable", () => {
  const withheld = new Map<string, DecisionSupportLevel>([
    ["ASSA-B", "insufficient_evidence"],
    ["MTRS", "insufficient_evidence"],
  ]);

  it("does not force a winner into the opportunity label", () => {
    expect(selectOpportunity([holding("ASSA-B"), holding("MTRS")], withheld).kind).toBe("strongest_setup");
  });

  it("still names the best-fitting holding, rather than hiding it", () => {
    // Principle 3: ASSA-B may genuinely be interesting. The claim changes,
    // not the company.
    const { holding: chosen } = selectOpportunity([holding("ASSA-B"), holding("MTRS")], withheld);
    expect(chosen?.ticker).toBe("ASSA-B");
  });

  it("names nothing at all when there are no evaluated holdings", () => {
    const { holding: chosen, kind } = selectOpportunity([], DECISION_SUPPORT);
    expect(chosen).toBeNull();
    expect(kind).toBe("strongest_setup");
  });

  it("does not invent actionability from an empty decision-support map", () => {
    expect(selectOpportunity(FIT_ORDER, new Map()).kind).toBe("strongest_setup");
  });
});

describe("it picks, it does not rank", () => {
  it("never reorders the fit array it was given", () => {
    const given = [...FIT_ORDER];
    selectOpportunity(FIT_ORDER, DECISION_SUPPORT);
    expect(FIT_ORDER.map((h) => h.ticker)).toEqual(given.map((h) => h.ticker));
  });

  it("returns a holding from the array, never a synthesised one", () => {
    const { holding: chosen } = selectOpportunity(FIT_ORDER, DECISION_SUPPORT);
    expect(FIT_ORDER).toContain(chosen);
  });
});
