import { describe, expect, it } from "vitest";
import { agendaItemHeadline } from "./describeAgendaHeadline";
import type { AgendaItemView, ReasonFactView } from "./dailyBriefAgendaApi";

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
    reasonFacts: [null],
    ...overrides,
  };
}

const OUTCOME_WITHOUT_EXECUTION_FACT: ReasonFactView = {
  code: "workflow_gap",
  entity: "AAPL",
  value: "OUTCOME_WITHOUT_EXECUTION",
  secondaryValue: null,
  label: null,
  count: 3,
};

function sv(key: string, params?: Record<string, string | number>): string {
  const dictionary: Record<string, string> = {
    "dailyBriefAgenda.attentionCategory.outcomeWithoutExecution": "utfall utan verkställande ({{count}} st)",
  };
  const template = dictionary[key];
  if (!template) throw new Error(`No fixture translation for ${key}`);
  return template.replace(/\{\{(\w+)\}\}/g, (match, name: string) => (params && name in params ? String(params[name]) : match));
}

describe("agendaItemHeadline (Implementation Sprint B1.1 -- Backend Language Cleanup)", () => {
  it("composes and translates the headline from the matching reasonFacts entry, ticker-prefixed", () => {
    const result = agendaItemHeadline(item({ reasonFacts: [OUTCOME_WITHOUT_EXECUTION_FACT] }), sv);
    expect(result).toBe("AAPL: utfall utan verkställande (3 st)");
  });

  it("omits the ticker prefix for a portfolio-level item with no ticker", () => {
    const result = agendaItemHeadline(item({ ticker: null, reasonFacts: [OUTCOME_WITHOUT_EXECUTION_FACT] }), sv);
    expect(result).toBe("utfall utan verkställande (3 st)");
  });

  it("falls back to the raw backend headline when no reasonFacts entry matches the headline text", () => {
    const result = agendaItemHeadline(
      item({ headline: "AAPL: China revenue declines (satisfied)", reason: ["AAPL: China revenue declines (satisfied)"], reasonFacts: [null] }),
      sv,
    );
    expect(result).toBe("AAPL: China revenue declines (satisfied)");
  });

  it("falls back to the raw backend headline when the matching fact is missing a required field (never a guessed count)", () => {
    const result = agendaItemHeadline(
      item({ reasonFacts: [{ ...OUTCOME_WITHOUT_EXECUTION_FACT, count: null }] }),
      sv,
    );
    expect(result).toBe("AAPL: outcome without execution (3 item(s))");
  });
});
