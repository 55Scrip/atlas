/**
 * The audit's exact data, and the rule that stops it happening again.
 *
 * Eleven changes were waiting on the start surface: AMZN, GOOG and META
 * had moved to *reduce*, and eight European holdings had moved from
 * unknown to operationally limited because Atlas had just read their
 * filings. Alphabetical order showed ALFA, AMZN, ASSA-B and collapsed the
 * rest, so two of the three reduce transitions sat behind a disclosure,
 * underneath coverage diagnostics.
 */

import { describe, expect, it } from "vitest";
import {
  classifyChange,
  orderBySignificance,
  visibleCount,
} from "./changeSignificance";
import type { ChangeLogEntryView, TickerChangeGroupView } from "./dailyBriefChangeLogApi";
import type { ReasonCode } from "./dailyBriefAgendaApi";

function entry(
  ticker: string,
  reasonCode: ReasonCode,
  value: string | null,
  detectedAt = "2026-09-17T12:59:01.000000Z",
): ChangeLogEntryView {
  return {
    id: `${ticker}:${reasonCode}`,
    ticker,
    caseId: `case-${ticker}`,
    reasonCode,
    value,
    secondaryValue: null,
    label: null,
    headline: `${ticker} changed`,
    detectedAt,
    seenAt: null,
  };
}

function group(
  ticker: string,
  reasonCode: ReasonCode,
  value: string | null,
  detectedAt?: string,
): TickerChangeGroupView {
  return { ticker, primary: entry(ticker, reasonCode, value, detectedAt), additionalCount: 0, isNew: true };
}

/** The eleven groups exactly as the change log returned them. */
const AUDIT_CORPUS: TickerChangeGroupView[] = [
  group("ALFA", "portfolio_decision_transition", "operationally_limited"),
  group("AMZN", "investment_decision_transition", "reduce"),
  group("ASSA-B", "portfolio_decision_transition", "operationally_limited"),
  group("ATCO-B", "portfolio_decision_transition", "operationally_limited"),
  group("GOOG", "investment_decision_transition", "reduce"),
  group("INVE-B", "portfolio_decision_transition", "operationally_limited"),
  group("META", "investment_decision_transition", "reduce"),
  group("MTRS", "portfolio_decision_transition", "operationally_limited"),
  group("SAND", "portfolio_decision_transition", "operationally_limited"),
  group("SU.PA", "portfolio_decision_transition", "operationally_limited"),
  group("VOLV-B", "portfolio_decision_transition", "operationally_limited"),
];

const VISIBLE_FLOOR = 3;

function visible(groups: TickerChangeGroupView[]): string[] {
  const ordered = orderBySignificance(groups);
  return ordered.slice(0, visibleCount(ordered, VISIBLE_FLOOR)).map((g) => g.ticker);
}

describe("the audit scenario", () => {
  it("shows every reduce transition before any coverage diagnostic", () => {
    expect(visible(AUDIT_CORPUS).sort()).toEqual(["AMZN", "GOOG", "META"]);
  });

  it("no longer lets the alphabet decide what is seen first", () => {
    // ALFA led the brief purely by name, and is now below the actions.
    expect(orderBySignificance(AUDIT_CORPUS)[0]?.ticker).not.toBe("ALFA");
    expect(visible(AUDIT_CORPUS)).not.toContain("ALFA");
  });

  it("keeps all eight European diagnostics present, just not in front", () => {
    const ordered = orderBySignificance(AUDIT_CORPUS);
    expect(ordered).toHaveLength(11);
    const limited = ordered.filter((g) => g.primary.value === "operationally_limited");
    expect(limited).toHaveLength(8);
    expect(ordered.slice(0, 3).every((g) => g.primary.value === "reduce")).toBe(true);
  });
});

describe("classification", () => {
  it.each(["reduce", "exit", "buy", "add"])("treats a move to %s as an action", (value) => {
    expect(classifyChange(entry("X", "investment_decision_transition", value))).toBe("action");
  });

  it.each(["hold", "wait", "no_decision"])(
    "treats a move to %s as review, not action -- it is the absence of one",
    (value) => {
      expect(classifyChange(entry("X", "investment_decision_transition", value))).toBe("review");
    },
  );

  it("never turns a withheld recommendation into urgency", () => {
    const withheld = group("X", "investment_decision_transition", "no_decision");
    const diagnostic = group("Y", "portfolio_decision_transition", "operationally_limited");
    expect(classifyChange(withheld.primary)).not.toBe("action");
    // Still ranked above plumbing, because it is about the conclusion.
    expect(orderBySignificance([diagnostic, withheld])[0]?.ticker).toBe("X");
  });

  it("ranks an unrecognised future reason code below action", () => {
    const unknown = entry("X", "a_code_from_a_later_build" as ReasonCode, "something");
    expect(classifyChange(unknown)).not.toBe("action");
    expect(classifyChange(unknown)).toBe("information");
  });

  it("puts Atlas's own plumbing last", () => {
    const ordered = orderBySignificance([
      group("A", "workflow_gap", null),
      group("B", "portfolio_decision_transition", "operationally_limited"),
      group("C", "recommendation_conviction_transition", "low"),
      group("D", "investment_decision_transition", "reduce"),
    ]);
    expect(ordered.map((g) => g.ticker)).toEqual(["D", "C", "B", "A"]);
  });
});

describe("ordering is symmetric and deterministic", () => {
  it("does not favour selling over buying", () => {
    const ordered = orderBySignificance([
      group("DIAG", "portfolio_decision_transition", "operationally_limited"),
      group("BUYME", "investment_decision_transition", "add"),
    ]);
    expect(ordered[0]?.ticker).toBe("BUYME");
  });

  it("separates same-tier entries by recency, then by ticker", () => {
    const ordered = orderBySignificance([
      group("OLD", "investment_decision_transition", "reduce", "2026-09-01T00:00:00Z"),
      group("NEW", "investment_decision_transition", "reduce", "2026-09-17T00:00:00Z"),
    ]);
    expect(ordered.map((g) => g.ticker)).toEqual(["NEW", "OLD"]);

    const sameInstant = orderBySignificance([
      group("BBB", "investment_decision_transition", "reduce"),
      group("AAA", "investment_decision_transition", "reduce"),
    ]);
    expect(sameInstant.map((g) => g.ticker)).toEqual(["AAA", "BBB"]);
  });

  it("never sorts the caller's array in place", () => {
    // Deliberately a fresh array rather than the shared corpus: an
    // in-place sort by an earlier test would already have reordered that
    // one, and this test would then compare a mutated array against its
    // own mutated snapshot and pass. A mutation run found exactly that.
    const caller = [
      group("ZZZ", "portfolio_decision_transition", "operationally_limited"),
      group("AAA", "investment_decision_transition", "reduce"),
    ];
    const orderBefore = caller.map((g) => g.ticker);

    const sorted = orderBySignificance(caller);

    expect(caller.map((g) => g.ticker)).toEqual(orderBefore);
    expect(sorted.map((g) => g.ticker)).toEqual(["AAA", "ZZZ"]);
    expect(sorted).not.toBe(caller);
  });
});

describe("how much is shown", () => {
  it("expands past the floor rather than hiding an action", () => {
    const eightActions = ["A", "B", "C", "D", "E", "F", "G", "H"].map((t) =>
      group(t, "investment_decision_transition", "reduce"),
    );
    expect(visibleCount(eightActions, VISIBLE_FLOOR)).toBe(8);
  });

  it("still shows a few entries on a day with no actions at all", () => {
    const quiet = AUDIT_CORPUS.filter((g) => g.primary.value === "operationally_limited");
    expect(visibleCount(quiet, VISIBLE_FLOOR)).toBe(VISIBLE_FLOOR);
    expect(visible(quiet)).toHaveLength(3);
  });

  it("never claims to show more than exists", () => {
    expect(visibleCount([group("A", "workflow_gap", null)], VISIBLE_FLOOR)).toBe(1);
    expect(visibleCount([], VISIBLE_FLOOR)).toBe(0);
  });
});
