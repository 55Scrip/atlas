import { describe, expect, it } from "vitest";
import { groupAgendaByTicker } from "./groupAgendaByTicker";
import type { AgendaItemView } from "./dailyBriefAgendaApi";

function item(overrides: Partial<AgendaItemView> = {}): AgendaItemView {
  return {
    id: "review_investment_case:AMZN:1",
    priority: "high",
    kind: "review_investment_case",
    group: "portfolio",
    source: "case_condition",
    headline: "AMZN: missing evidence (no evidence recorded)",
    reason: ["AMZN: missing evidence (no evidence recorded)"],
    nature: "persistent_condition",
    reasonNature: ["persistent_condition"],
    since: null,
    ticker: "AMZN",
    caseId: "case-amzn",
    portfolioContext: null,
    generatedAt: "2026-01-01T00:00:00Z",
    attentionCategory: null,
    attentionCount: null,
    reasonFacts: [null],
    ...overrides,
  };
}

describe("groupAgendaByTicker (Daily Brief Compression)", () => {
  it("collapses multiple items for the same ticker into one group", () => {
    const groups = groupAgendaByTicker([
      item({ id: "a", headline: "AMZN: decision without outcome" }),
      item({ id: "b", headline: "AMZN: missing evidence" }),
    ]);
    expect(groups).toHaveLength(1);
    expect(groups[0]!.ticker).toBe("AMZN");
    expect(groups[0]!.items).toHaveLength(2);
  });

  it("never repeats the exact same reason line twice within a group", () => {
    const groups = groupAgendaByTicker([
      item({ id: "a", headline: "AMZN: missing evidence (no evidence recorded)" }),
      item({ id: "b", headline: "AMZN: missing evidence (no evidence recorded)" }),
    ]);
    expect(groups[0]!.reasons).toEqual(["AMZN: missing evidence (no evidence recorded)"]);
  });

  it("keeps a ticker-less (portfolio-wide/system) item as its own standalone group", () => {
    const groups = groupAgendaByTicker([item({ id: "a", ticker: null, kind: "portfolio_risk" })]);
    expect(groups).toHaveLength(1);
    expect(groups[0]!.ticker).toBeNull();
  });

  it("ranks a critical group above a high group above a normal group", () => {
    const groups = groupAgendaByTicker([
      item({ id: "a", ticker: "LOW", priority: "normal" }),
      item({ id: "b", ticker: "CRIT", priority: "critical" }),
      item({ id: "c", ticker: "HIGH", priority: "high" }),
    ]);
    expect(groups.map((g) => g.ticker)).toEqual(["CRIT", "HIGH", "LOW"]);
  });

  it("ranks a group with a genuine change event above an equal-priority group with only persistent conditions", () => {
    const groups = groupAgendaByTicker([
      item({ id: "a", ticker: "STALE", priority: "high", nature: "persistent_condition" }),
      item({ id: "b", ticker: "FRESH", priority: "high", nature: "change_event" }),
    ]);
    expect(groups.map((g) => g.ticker)).toEqual(["FRESH", "STALE"]);
  });

  it("a group's topPriority is the highest priority among its own items, never averaged or invented", () => {
    const groups = groupAgendaByTicker([
      item({ id: "a", ticker: "AMZN", priority: "normal" }),
      item({ id: "b", ticker: "AMZN", priority: "critical" }),
    ]);
    expect(groups[0]!.topPriority).toBe("critical");
  });
});
