import { describe, expect, it } from "vitest";
import { itemsSinceLastVisit } from "./sinceYouWereHere";
import type { AgendaItemView } from "./dailyBriefAgendaApi";

function item(overrides: Partial<AgendaItemView> = {}): AgendaItemView {
  return {
    id: "a",
    priority: "high",
    kind: "review_investment_case",
    group: "portfolio",
    source: "executive_change",
    headline: "AMD: Lisa Su (CEO) appointed.",
    reason: ["AMD: Lisa Su (CEO) appointed."],
    nature: "change_event",
    reasonNature: ["change_event"],
    since: "2026-08-25T12:00:00Z",
    ticker: "AMD",
    caseId: "case-amd",
    portfolioContext: null,
    generatedAt: "2026-08-26T09:00:00Z",
    attentionCategory: null,
    attentionCount: null,
    ...overrides,
  };
}

describe("itemsSinceLastVisit (Since You Were Here)", () => {
  it("a genuine first visit (lastViewedAt null) includes every item, even those with no since timestamp", () => {
    const items = [item({ since: null })];
    expect(itemsSinceLastVisit(items, null)).toEqual(items);
  });

  it("an item with since strictly after lastViewedAt counts", () => {
    const items = [item({ since: "2026-08-26T10:00:00Z" })];
    expect(itemsSinceLastVisit(items, "2026-08-26T09:00:00Z")).toEqual(items);
  });

  it("an item with since at or before lastViewedAt does not count", () => {
    const items = [item({ since: "2026-08-26T08:00:00Z" })];
    expect(itemsSinceLastVisit(items, "2026-08-26T09:00:00Z")).toEqual([]);
  });

  it("an item with since exactly equal to lastViewedAt does not count (strictly after, not at)", () => {
    const items = [item({ since: "2026-08-26T09:00:00Z" })];
    expect(itemsSinceLastVisit(items, "2026-08-26T09:00:00Z")).toEqual([]);
  });

  it("an item with no since timestamp is never counted once a real lastViewedAt exists -- neither provably new nor old", () => {
    const items = [item({ since: null })];
    expect(itemsSinceLastVisit(items, "2026-08-26T09:00:00Z")).toEqual([]);
  });

  it("historical events never reappear on a later visit", () => {
    const items = [item({ since: "2026-06-30T00:00:00Z" })];
    expect(itemsSinceLastVisit(items, "2026-08-01T00:00:00Z")).toEqual([]);
  });
});
