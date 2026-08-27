import { describe, expect, it } from "vitest";
import { describeChangeLogEntry } from "./describeChangeLogEntry";
import type { ChangeLogEntryView } from "./dailyBriefChangeLogApi";

const DICTIONARY: Record<string, string> = {
  "investmentDecision.action.hold": "Behåll",
  "investmentDecision.action.reduce": "Minska",
  "investmentDecision.change.line": "Rekommendationen ändrades från {{previous}} till {{current}}.",
  "dailyBriefAgenda.reasonFact.businessQuality.weakeningBusiness": "verksamhetens grundläggande siffror försvagas",
};

function t(key: string, params?: Record<string, string | number>): string {
  const template = DICTIONARY[key];
  if (!template) throw new Error(`No fixture translation for ${key}`);
  return template.replace(/\{\{(\w+)\}\}/g, (match, name: string) => (params && name in params ? String(params[name]) : match));
}

function entry(overrides: Partial<ChangeLogEntryView> = {}): ChangeLogEntryView {
  return {
    id: "id-1",
    ticker: "NVDA",
    caseId: "case-nvda",
    reasonCode: "investment_decision_transition",
    value: "reduce",
    secondaryValue: "hold",
    label: null,
    headline: "NVDA: fallback headline",
    detectedAt: "2026-08-27T09:00:00Z",
    seenAt: null,
    ...overrides,
  };
}

describe("describeChangeLogEntry", () => {
  it("reuses describeReasonFact's own transition rendering for a recommendation change (Phase 14's own worked test)", () => {
    expect(describeChangeLogEntry(entry(), t)).toBe("Rekommendationen ändrades från Behåll till Minska.");
  });

  it("reuses describeReasonFact for a persistent-finding source with no transition (business quality)", () => {
    expect(
      describeChangeLogEntry(
        entry({ reasonCode: "business_quality", value: null, secondaryValue: null, label: null }),
        t,
      ),
    ).toBe("verksamhetens grundläggande siffror försvagas");
  });

  it("falls back to the entry's own real headline when the reason code isn't recognized by the translation table", () => {
    expect(
      describeChangeLogEntry(entry({ reasonCode: "workflow_gap", value: null, headline: "NVDA: fallback headline" }), t),
    ).toBe("NVDA: fallback headline");
  });

  it("falls back to the headline rather than fabricating a sentence when a transition's own values are unrecognized", () => {
    expect(
      describeChangeLogEntry(
        entry({ value: "not_a_real_value", secondaryValue: "also_not_real", headline: "NVDA: fallback headline" }),
        t,
      ),
    ).toBe("NVDA: fallback headline");
  });
});
