import { describe, expect, it } from "vitest";
import { agendaItemHeadline } from "./describeAgendaHeadline";
import type { AgendaItemView } from "./dailyBriefAgendaApi";

function item(overrides: Partial<AgendaItemView> = {}): AgendaItemView {
  return {
    id: "review_portfolio_position:AAPL",
    priority: "critical",
    kind: "review_portfolio_position",
    group: "portfolio",
    source: "portfolio_status",
    headline: "AAPL: outcome without execution (3 item(s))",
    reason: ["AAPL: outcome without execution (3 item(s))"],
    nature: "persistent_condition",
    reasonNature: ["persistent_condition"],
    since: null,
    ticker: "AAPL",
    caseId: "case-aapl",
    portfolioContext: null,
    generatedAt: "2026-01-01T00:00:00Z",
    attentionCategory: null,
    attentionCount: null,
    ...overrides,
  };
}

function sv(key: string, params?: Record<string, string | number>): string {
  const dictionary: Record<string, string> = {
    "dailyBriefAgenda.attentionCategory.outcomeWithoutExecution": "utfall utan verkställande ({{count}} st)",
  };
  const template = dictionary[key];
  if (!template) throw new Error(`No fixture translation for ${key}`);
  return template.replace(/\{\{(\w+)\}\}/g, (match, name: string) => (params && name in params ? String(params[name]) : match));
}

describe("agendaItemHeadline (Localization fix -- Portfolio live-verification follow-up)", () => {
  it("composes and translates the headline from attentionCategory/attentionCount, ticker-prefixed", () => {
    const result = agendaItemHeadline(item({ attentionCategory: "OUTCOME_WITHOUT_EXECUTION", attentionCount: 3 }), sv);
    expect(result).toBe("AAPL: utfall utan verkställande (3 st)");
  });

  it("omits the ticker prefix for a portfolio-level item with no ticker", () => {
    const result = agendaItemHeadline(
      item({ ticker: null, attentionCategory: "OUTCOME_WITHOUT_EXECUTION", attentionCount: 3 }),
      sv,
    );
    expect(result).toBe("utfall utan verkställande (3 st)");
  });

  it("falls back to the raw backend headline when attentionCategory is null", () => {
    const result = agendaItemHeadline(item({ attentionCategory: null, attentionCount: null, headline: "AAPL: China revenue declines (satisfied)" }), sv);
    expect(result).toBe("AAPL: China revenue declines (satisfied)");
  });

  it("falls back to the raw backend headline when attentionCount is null even if a category is present (never a guessed count)", () => {
    const result = agendaItemHeadline(
      item({ attentionCategory: "OUTCOME_WITHOUT_EXECUTION", attentionCount: null, headline: "AAPL: outcome without execution (3 item(s))" }),
      sv,
    );
    expect(result).toBe("AAPL: outcome without execution (3 item(s))");
  });
});
