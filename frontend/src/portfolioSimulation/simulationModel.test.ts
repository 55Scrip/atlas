import { describe, expect, it } from "vitest";
import {
  applyPortfolioEdits,
  availableCapital,
  editStep,
  holdingKey,
  resetPosition,
  resetSimulation,
  setPosition,
  type PortfolioSimulationBase,
} from "./simulationModel";

/** The real portfolio's shape, reduced: fully invested, no unallocated
 * capital, values in SEK, no share quantities anywhere. */
const BASE: PortfolioSimulationBase = {
  holdings: [
    { ticker: "META", caseId: "case-meta", valueAbsolute: 114154, currency: "SEK" },
    { ticker: "VST", caseId: "case-vst", valueAbsolute: 119768, currency: "SEK" },
    { ticker: "MA", caseId: "case-ma", valueAbsolute: 73219, currency: "SEK" },
  ],
  unallocatedValue: 0,
};
const TOTAL = 114154 + 119768 + 73219;
const META = holdingKey({ caseId: "case-meta", ticker: "META" });
const VST = holdingKey({ caseId: "case-vst", ticker: "VST" });
const MA = holdingKey({ caseId: "case-ma", ticker: "MA" });

describe("hypothetical portfolio -- baseline", () => {
  it("is the persisted portfolio exactly when there are no edits", () => {
    const h = applyPortfolioEdits(BASE, {});
    expect(h.isDirty).toBe(false);
    expect(h.changedCount).toBe(0);
    expect(h.unallocatedValue).toBe(0);
    for (const holding of h.holdings) {
      expect(holding.hypotheticalValue).toBe(holding.baseValue);
      expect(holding.deltaValue).toBe(0);
      expect(holding.isChanged).toBe(false);
      expect(holding.isRemoved).toBe(false);
    }
    // Weights reproduce the persisted ones and still sum to 100.
    expect(h.holdings.reduce((s, x) => s + x.hypotheticalWeightPercent, 0)).toBeCloseTo(100, 6);
  });

  it("never mutates the base portfolio", () => {
    // The mutation this kills: an edit reaching through into the
    // persisted read model, which would make "reset" unachievable and
    // the whole firewall meaningless.
    const snapshot = JSON.parse(JSON.stringify(BASE));
    applyPortfolioEdits(BASE, { [META]: 50000 });
    applyPortfolioEdits(BASE, { [VST]: 0 });
    expect(BASE).toEqual(snapshot);
  });
});

describe("reduce", () => {
  it("moves the freed capital into unallocated, conserving the total", () => {
    const h = applyPortfolioEdits(BASE, { [META]: 100000 });
    const meta = h.holdings.find((x) => x.key === META)!;
    expect(meta.hypotheticalValue).toBe(100000);
    expect(meta.deltaValue).toBe(-14154);
    expect(h.unallocatedValue).toBe(14154);
    expect(h.totalValue).toBe(TOTAL);
    // Value moved; it did not vanish.
    const held = h.holdings.reduce((s, x) => s + x.hypotheticalValue, 0);
    expect(held + h.unallocatedValue).toBeCloseTo(TOTAL, 6);
  });

  it("does not touch any other holding's value", () => {
    // The mutation this kills: renormalizing everyone else, which would
    // make reducing META look like a decision to increase VST and MA.
    const h = applyPortfolioEdits(BASE, { [META]: 100000 });
    expect(h.holdings.find((x) => x.key === VST)!.hypotheticalValue).toBe(119768);
    expect(h.holdings.find((x) => x.key === MA)!.hypotheticalValue).toBe(73219);
  });

  it("recomputes every weight from the hypothetical state", () => {
    const h = applyPortfolioEdits(BASE, { [META]: 100000 });
    const meta = h.holdings.find((x) => x.key === META)!;
    expect(meta.hypotheticalWeightPercent).toBeCloseTo((100000 / TOTAL) * 100, 6);
    expect(meta.deltaWeightPercent).toBeLessThan(0);
    // Allocation still accounts for everything, unallocated included.
    const total = h.holdings.reduce((s, x) => s + x.hypotheticalWeightPercent, 0) + h.unallocatedWeightPercent;
    expect(total).toBeCloseTo(100, 6);
  });

  it("floors a position at zero rather than going short", () => {
    const h = applyPortfolioEdits(BASE, { [META]: -50000 });
    const meta = h.holdings.find((x) => x.key === META)!;
    expect(meta.hypotheticalValue).toBe(0);
    expect(h.unallocatedValue).toBe(114154);
  });
});

describe("remove", () => {
  it("takes the position to zero and marks it removed, keeping the holding", () => {
    const h = applyPortfolioEdits(BASE, { [META]: 0 });
    const meta = h.holdings.find((x) => x.key === META)!;
    expect(meta.hypotheticalValue).toBe(0);
    expect(meta.isRemoved).toBe(true);
    // Still present: removal is a value of zero, never a deletion, so
    // it can be undone and so the row can say what it used to hold.
    expect(h.holdings).toHaveLength(3);
    expect(meta.baseValue).toBe(114154);
    expect(h.unallocatedValue).toBe(114154);
  });

  it("is undone exactly by resetting that position", () => {
    const edits = resetPosition({ [META]: 0 }, META);
    const h = applyPortfolioEdits(BASE, edits);
    expect(h.isDirty).toBe(false);
    expect(h.holdings.find((x) => x.key === META)!.hypotheticalValue).toBe(114154);
  });
});

describe("increase", () => {
  it("is funded from unallocated capital", () => {
    const edits = { [META]: 0, [MA]: 73219 + 50000 };
    const h = applyPortfolioEdits(BASE, edits);
    expect(h.holdings.find((x) => x.key === MA)!.hypotheticalValue).toBe(123219);
    expect(h.unallocatedValue).toBe(114154 - 50000);
    expect(h.totalValue).toBe(TOTAL);
  });

  it("cannot spend capital the investor does not have", () => {
    // Fully invested with nothing unallocated: an increase has nothing
    // to draw on until something is reduced. Honouring it anyway would
    // answer a question about money that is not there.
    const h = applyPortfolioEdits(BASE, { [MA]: 73219 + 50000 });
    expect(h.unallocatedValue).toBeCloseTo(0, 6);
    expect(h.holdings.find((x) => x.key === MA)!.hypotheticalValue).toBeCloseTo(73219, 6);
    expect(availableCapital(h)).toBeCloseTo(0, 6);
  });

  it("never drives unallocated capital negative", () => {
    // The mutation this kills: a reversed cash sign, which would show
    // the portfolio funding itself out of nothing.
    for (const target of [100000, 500000, 5000000]) {
      const h = applyPortfolioEdits(BASE, { [MA]: target });
      expect(h.unallocatedValue).toBeGreaterThanOrEqual(-1e-9);
    }
  });
});

describe("composition and reset", () => {
  it("composes multiple edits deterministically, in any order", () => {
    const a = applyPortfolioEdits(BASE, { [META]: 90000, [VST]: 0, [MA]: 100000 });
    const b = applyPortfolioEdits(BASE, { [MA]: 100000, [META]: 90000, [VST]: 0 });
    expect(a).toEqual(b);
    expect(a.changedCount).toBe(3);
    expect(a.totalValue).toBe(TOTAL);
  });

  it("does not let one holding's edit change another's", () => {
    const only = applyPortfolioEdits(BASE, { [META]: 90000 });
    const both = applyPortfolioEdits(BASE, { [META]: 90000, [VST]: 110000 });
    expect(both.holdings.find((x) => x.key === META)!.hypotheticalValue).toBe(
      only.holdings.find((x) => x.key === META)!.hypotheticalValue,
    );
  });

  it("restores the exact baseline on reset, with no cumulative drift", () => {
    let edits = setPosition({}, META, 90000, 114154);
    edits = setPosition(edits, META, 40000, 114154);
    edits = setPosition(edits, VST, 0, 119768);
    edits = resetSimulation();
    expect(applyPortfolioEdits(BASE, edits)).toEqual(applyPortfolioEdits(BASE, {}));
  });

  it("treats an edit back to the persisted value as no edit at all", () => {
    let edits = setPosition({}, META, 90000, 114154);
    expect(applyPortfolioEdits(BASE, edits).isDirty).toBe(true);
    edits = setPosition(edits, META, 114154, 114154);
    expect(edits).toEqual({});
    expect(applyPortfolioEdits(BASE, edits).isDirty).toBe(false);
  });

  it("reaches exactly zero even when the step is not exactly representable", () => {
    // Regression from live verification: 114,154 / 10 = 11,415.4, which
    // binary floating point cannot hold exactly, so ten subtractions
    // land on ~1e-11. The position rendered as "$0" but was not zero,
    // so it did not count as removed and its control stayed enabled.
    // The earlier test missed this because 400,000 divides into a step
    // that happens to be exact.
    const base: PortfolioSimulationBase = {
      holdings: [{ ticker: "META", caseId: "case-meta", valueAbsolute: 114154, currency: "SEK" }],
      unallocatedValue: 0,
    };
    const step = editStep(114154);
    let value = 114154;
    for (let i = 0; i < 10; i += 1) value -= step;
    expect(value).not.toBe(0); // the dust is real
    const h = applyPortfolioEdits(base, { "case:case-meta": value });
    const meta = h.holdings[0]!;
    expect(meta.hypotheticalValue).toBe(0);
    expect(meta.isRemoved).toBe(true);
    expect(h.unallocatedValue).toBe(114154);
  });

  it("steps by a tenth of the persisted value, so ten steps reach zero exactly", () => {
    // Deliberately not "one share": quantity is null for every holding
    // in the real portfolio, so a share-denominated step would invent a
    // unit Atlas does not have.
    const step = editStep(114154);
    expect(step).toBeCloseTo(11415.4, 6);
    let value = 114154;
    for (let i = 0; i < 10; i += 1) value -= step;
    expect(value).toBeCloseTo(0, 6);
  });
});

describe("identity", () => {
  it("keys edits by case id, not display ticker", () => {
    expect(holdingKey({ caseId: "case-meta", ticker: "META" })).toBe("case:case-meta");
    expect(holdingKey({ caseId: null, ticker: "META" })).toBe("ticker:META");
  });

  it("keeps two holdings of the same ticker independently editable", () => {
    // Share classes and cross-venue listings share a ticker; keying on
    // it alone would edit both at once.
    const base: PortfolioSimulationBase = {
      holdings: [
        { ticker: "ABC", caseId: "case-a", valueAbsolute: 1000, currency: "SEK" },
        { ticker: "ABC", caseId: "case-b", valueAbsolute: 2000, currency: "SEK" },
      ],
      unallocatedValue: 0,
    };
    const h = applyPortfolioEdits(base, { "case:case-a": 500 });
    expect(h.holdings[0]!.hypotheticalValue).toBe(500);
    expect(h.holdings[1]!.hypotheticalValue).toBe(2000);
  });
});

describe("existing unallocated capital", () => {
  it("funds an increase from capital the investor already holds", () => {
    const withCash: PortfolioSimulationBase = { ...BASE, unallocatedValue: 50000 };
    const h = applyPortfolioEdits(withCash, { [MA]: 73219 + 30000 });
    expect(h.holdings.find((x) => x.key === MA)!.hypotheticalValue).toBe(103219);
    expect(h.unallocatedValue).toBe(20000);
    expect(h.totalValue).toBe(TOTAL + 50000);
  });
});
