import { describe, expect, it } from "vitest";
import { entrySupportBand, rankCandidates, type RankedCandidate } from "./rankCandidates";

function candidate(overrides: Partial<RankedCandidate> = {}): RankedCandidate {
  return {
    ticker: "AAA",
    caseId: "case-1",
    fit: "excellent",
    stance: null,
    priority: null,
    decisionSupport: "entry_supported",
    ...overrides,
  };
}

/**
 * Convergence Sprint 4D. Every case below is written in canonical
 * states, never in tickers: the live `entry_supported` set (ASML, CRM,
 * CRWD, TSM) is what motivated the sprint, but nothing here is pinned
 * to it -- the same assertions must hold when that set changes.
 */
describe("rankCandidates -- what Atlas concludes decides the tier (Sprint 4D)", () => {
  it("puts a candidate Atlas supports entering above one it has reached no conclusion on", () => {
    const result = rankCandidates([
      candidate({ ticker: "WITHHELD", decisionSupport: "insufficient_evidence" }),
      candidate({ ticker: "SUPPORTED", decisionSupport: "entry_supported" }),
    ]);
    expect(result.highest.map((c) => c.ticker)).toEqual(["SUPPORTED"]);
    expect(result.worthReviewing.map((c) => c.ticker)).toEqual(["WITHHELD"]);
  });

  /** The sprint's governing rule: Portfolio Fit informs, it does not
   * rewrite the case. A company Atlas concluded is worth buying stays
   * ahead of one it could not conclude on, however well the latter
   * happens to suit this particular portfolio. */
  it("keeps a supported entry with weak Fit ahead of an unconcluded one with good Fit", () => {
    const result = rankCandidates([
      candidate({ ticker: "GOODFIT", decisionSupport: "insufficient_evidence", fit: "good" }),
      candidate({ ticker: "WEAKFIT", decisionSupport: "entry_supported", fit: "weak" }),
    ]);
    expect(result.highest.map((c) => c.ticker)).toEqual(["WEAKFIT"]);
    expect(result.worthReviewing.map((c) => c.ticker)).toEqual(["GOODFIT"]);
  });

  it("does not let even a poor Fit demote a supported entry out of its tier", () => {
    const result = rankCandidates([candidate({ decisionSupport: "entry_supported", fit: "poor" })]);
    expect(result.highest.map((c) => c.ticker)).toEqual(["AAA"]);
  });

  /** `insufficient_evidence` is a withheld conclusion, not a negative
   * one, and must not be filed with Atlas's real "no". */
  it("ranks a withheld conclusion above an evaluated refusal, never treating the two as the same answer", () => {
    const result = rankCandidates([
      candidate({ ticker: "REFUSED", decisionSupport: "no_action_supported", fit: "excellent" }),
      candidate({ ticker: "WITHHELD", decisionSupport: "insufficient_evidence", fit: "unavailable" }),
    ]);
    expect(result.worthReviewing.map((c) => c.ticker)).toEqual(["WITHHELD"]);
    expect(result.everythingElse.map((c) => c.ticker)).toEqual(["REFUSED"]);
  });

  it("never presents an evaluated refusal as an opportunity, however well it fits the portfolio", () => {
    const result = rankCandidates([candidate({ decisionSupport: "no_action_supported", fit: "excellent" })]);
    expect(result.highest).toEqual([]);
    expect(result.everythingElse.map((c) => c.ticker)).toEqual(["AAA"]);
  });

  /** "The current thesis remains intact" is a statement about holding
   * something, not about buying it. Reading it as an entry endorsement
   * would invent a claim the recommendation engine never made. */
  it("does not read thesis_intact as support for a new entry", () => {
    expect(entrySupportBand("thesis_intact")).toBe("open");
    const result = rankCandidates([candidate({ decisionSupport: "thesis_intact" })]);
    expect(result.highest).toEqual([]);
    expect(result.worthReviewing.map((c) => c.ticker)).toEqual(["AAA"]);
  });

  it("files an adverse conclusion with the refusals, never with the open questions", () => {
    for (const level of ["reduction_supported", "exit_supported"] as const) {
      expect(entrySupportBand(level)).toBe("against");
      const result = rankCandidates([candidate({ decisionSupport: level })]);
      expect(result.everythingElse.map((c) => c.ticker)).toEqual(["AAA"]);
    }
  });

  it("treats a missing conclusion as no conclusion reached, never as support and never as refusal", () => {
    expect(entrySupportBand(null)).toBe("open");
    const result = rankCandidates([candidate({ decisionSupport: null })]);
    expect(result.worthReviewing.map((c) => c.ticker)).toEqual(["AAA"]);
  });
});

describe("rankCandidates -- ordering within a band", () => {
  it("orders equally-concluded candidates by Portfolio Fit", () => {
    const result = rankCandidates([
      candidate({ ticker: "WEAK", fit: "weak" }),
      candidate({ ticker: "EXCELLENT", fit: "excellent" }),
      candidate({ ticker: "GOOD", fit: "good" }),
    ]);
    expect(result.highest.map((c) => c.ticker)).toEqual(["EXCELLENT", "GOOD", "WEAK"]);
  });

  it("orders candidates equal on conclusion and Fit by Stance", () => {
    const result = rankCandidates([
      candidate({ ticker: "MAINTAIN", stance: "maintain" }),
      candidate({ ticker: "INCREASE", stance: "increase" }),
    ]);
    expect(result.highest.map((c) => c.ticker)).toEqual(["INCREASE", "MAINTAIN"]);
  });

  it("orders candidates equal on conclusion, Fit and Stance by Agenda priority", () => {
    const result = rankCandidates([
      candidate({ ticker: "QUIET", stance: "maintain", priority: null }),
      candidate({ ticker: "URGENT", stance: "maintain", priority: "high" }),
    ]);
    expect(result.highest.map((c) => c.ticker)).toEqual(["URGENT", "QUIET"]);
  });

  it("breaks a genuine tie alphabetically by ticker, never claiming further differentiation", () => {
    const result = rankCandidates([candidate({ ticker: "ZZZ" }), candidate({ ticker: "AAA" })]);
    expect(result.highest.map((c) => c.ticker)).toEqual(["AAA", "ZZZ"]);
  });

  /** Null is not a value on the scale -- it sorts last within its own
   * band, and is never quietly read as neutral or as good. */
  it("sorts a null Fit last within its band without inventing a rating for it", () => {
    const result = rankCandidates([
      candidate({ ticker: "NOFIT", fit: null }),
      candidate({ ticker: "POORFIT", fit: "poor" }),
    ]);
    expect(result.highest.map((c) => c.ticker)).toEqual(["POORFIT", "NOFIT"]);
  });

  it("sorts a null Stance last within its band without inventing a stance for it", () => {
    const result = rankCandidates([
      candidate({ ticker: "NOSTANCE", stance: null }),
      candidate({ ticker: "REVIEWED", stance: "review" }),
    ]);
    expect(result.highest.map((c) => c.ticker)).toEqual(["REVIEWED", "NOSTANCE"]);
  });
});

describe("rankCandidates -- tier construction", () => {
  /** Kept from the pre-4D rule: a conclusion Atlas supports while its
   * own Stance is critical-toned is a real, unresolved tension, and is
   * never presented as a confident pick. Ordinary caution is not that
   * -- it is usually just moderate confidence. */
  it("demotes a supported entry whose Stance is a genuine red flag, but not one that is merely cautious", () => {
    const conflicted = rankCandidates([candidate({ stance: "avoid_decision" })]);
    expect(conflicted.highest).toEqual([]);
    expect(conflicted.worthReviewing.map((c) => c.ticker)).toEqual(["AAA"]);

    const cautious = rankCandidates([candidate({ stance: "review" })]);
    expect(cautious.highest.map((c) => c.ticker)).toEqual(["AAA"]);
  });

  it("never pads the supported tier -- no supported candidate means an empty list, not a promoted runner-up", () => {
    const result = rankCandidates([
      candidate({ ticker: "A", decisionSupport: "insufficient_evidence", fit: "excellent" }),
      candidate({ ticker: "B", decisionSupport: "insufficient_evidence", fit: "good" }),
    ]);
    expect(result.highest).toEqual([]);
    expect(result.worthReviewing.map((c) => c.ticker)).toEqual(["A", "B"]);
  });

  it("caps the supported tier at 5 and moves the overflow down, never dropping it", () => {
    const candidates = Array.from({ length: 7 }, (_, i) =>
      candidate({ ticker: `T${i}`, caseId: `case-${i}`, stance: "maintain" }),
    );
    const result = rankCandidates(candidates);
    expect(result.highest.length).toBe(5);
    expect(result.worthReviewing.length).toBe(2);
    const allTickers = [...result.highest, ...result.worthReviewing].map((c) => c.ticker).sort();
    expect(allTickers).toEqual(["T0", "T1", "T2", "T3", "T4", "T5", "T6"]);
  });

  it("keeps overflow ahead of genuinely unconcluded candidates in the tier it overflows into", () => {
    const supported = Array.from({ length: 6 }, (_, i) =>
      candidate({ ticker: `S${i}`, caseId: `case-s${i}`, fit: "good" }),
    );
    const result = rankCandidates([...supported, candidate({ ticker: "WITHHELD", decisionSupport: "insufficient_evidence", fit: "excellent" })]);
    expect(result.worthReviewing.map((c) => c.ticker)).toEqual(["S5", "WITHHELD"]);
  });

  it("assigns every candidate to exactly one tier, dropping none", () => {
    const all = rankCandidates([
      candidate({ ticker: "A", decisionSupport: "entry_supported" }),
      candidate({ ticker: "B", decisionSupport: "insufficient_evidence" }),
      candidate({ ticker: "C", decisionSupport: "no_action_supported" }),
      candidate({ ticker: "D", decisionSupport: null, fit: null, stance: null }),
    ]);
    const tickers = [...all.highest, ...all.worthReviewing, ...all.everythingElse].map((c) => c.ticker).sort();
    expect(tickers).toEqual(["A", "B", "C", "D"]);
  });

  /** No score exists to leak, and the returned shape is the guard: a
   * ranked candidate carries its canonical states and nothing derived. */
  it("returns only canonical categorical state, never a computed score field", () => {
    const result = rankCandidates([candidate()]);
    expect(Object.keys(result.highest[0]!).sort()).toEqual([
      "caseId",
      "decisionSupport",
      "fit",
      "priority",
      "stance",
      "ticker",
    ]);
  });
});

/** Sprint 4D's live-shaped case: the whole universe shares Fit `good`,
 * Stance `review` and a null Agenda priority, so before this sprint
 * every ranking input tied and ordering fell through to the
 * alphabetical tie-break -- putting companies Atlas had withheld any
 * conclusion on above ones it concluded were worth entering. */
describe("rankCandidates -- the live shape that motivated Sprint 4D", () => {
  it("lifts the supported entries above the withheld ones that alphabetically preceded them", () => {
    const shared = { fit: "good", stance: "review", priority: null } as const;
    const result = rankCandidates([
      candidate({ ticker: "AAPL", decisionSupport: "insufficient_evidence", ...shared }),
      candidate({ ticker: "AMD", decisionSupport: "insufficient_evidence", ...shared }),
      candidate({ ticker: "ASML", decisionSupport: "entry_supported", ...shared }),
      candidate({ ticker: "TSLA", decisionSupport: "insufficient_evidence", ...shared }),
      candidate({ ticker: "TSM", decisionSupport: "entry_supported", ...shared }),
    ]);
    expect(result.highest.map((c) => c.ticker)).toEqual(["ASML", "TSM"]);
    expect(result.worthReviewing.map((c) => c.ticker)).toEqual(["AAPL", "AMD", "TSLA"]);
  });
});
