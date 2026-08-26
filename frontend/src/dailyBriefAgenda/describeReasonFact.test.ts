import { describe, expect, it } from "vitest";
import { describeReasonFact, describeReasonLine } from "./describeReasonFact";
import type { ReasonFactView } from "./dailyBriefAgendaApi";

const DICTIONARY: Record<string, string> = {
  "dailyBriefAgenda.attentionCategory.outcomeWithoutExecution": "utfall utan verkställande ({{count}} st)",
  "dailyBriefAgenda.reasonFact.missingEvidence.noEvidenceRecorded": "inget underlag registrerat än",
  "dailyBriefAgenda.reasonFact.missingEvidence.decisionWithoutLinkedObservation": "ett beslut saknar en anteckning om varför",
  "dailyBriefAgenda.reasonFact.concentration.highConcentration": "hög koncentration i det här innehavet",
  "dailyBriefAgenda.reasonFact.largeUnallocatedCapitalOne": "Stort oallokerat kapital — {{count}} möjlig placering att överväga.",
  "dailyBriefAgenda.reasonFact.largeUnallocatedCapitalOther": "Stort oallokerat kapital — {{count}} möjliga placeringar att överväga.",
  "dailyBriefAgenda.reasonFact.managementCredibility.inconsistentFollowThrough": "tidigare åtaganden har inte uppfyllts",
  "dailyBriefAgenda.reasonFact.businessQuality.weakeningBusiness": "verksamhetens grundläggande siffror försvagas",
  "dailyBriefAgenda.reasonFact.executiveChange.role.ceo": "VD",
  "dailyBriefAgenda.reasonFact.executiveChange.event.appointment": "tillträdde",
  "decisionWorkspace.caseConditions.status.satisfied": "Uppfyllt",
  "decisionWorkspace.assumptions.status.invalidated": "Ogiltigförklarat",
};

function t(key: string, params?: Record<string, string | number>): string {
  const template = DICTIONARY[key];
  if (!template) throw new Error(`No fixture translation for ${key}`);
  return template.replace(/\{\{(\w+)\}\}/g, (match, name: string) => (params && name in params ? String(params[name]) : match));
}

function fact(overrides: Partial<ReasonFactView>): ReasonFactView {
  return { code: "workflow_gap", entity: "AAPL", value: null, secondaryValue: null, label: null, count: null, ...overrides };
}

describe("describeReasonFact (Implementation Sprint B1.1 -- Backend Language Cleanup)", () => {
  it("translates a workflow_gap fact via the existing ATTENTION_CATEGORY_KEY map", () => {
    expect(describeReasonFact(fact({ code: "workflow_gap", value: "OUTCOME_WITHOUT_EXECUTION", count: 3 }), t)).toBe(
      "utfall utan verkställande (3 st)",
    );
  });

  it("translates a missing_evidence fact by its gap kind", () => {
    expect(describeReasonFact(fact({ code: "missing_evidence", value: "decision_without_linked_observation" }), t)).toBe(
      "ett beslut saknar en anteckning om varför",
    );
  });

  it("translates a concentration fact by its finding kind", () => {
    expect(describeReasonFact(fact({ code: "concentration", value: "high_concentration" }), t)).toBe(
      "hög koncentration i det här innehavet",
    );
  });

  it("pluralizes large_unallocated_capital correctly", () => {
    expect(describeReasonFact(fact({ code: "large_unallocated_capital", entity: "portfolio", count: 1 }), t)).toBe(
      "Stort oallokerat kapital — 1 möjlig placering att överväga.",
    );
    expect(describeReasonFact(fact({ code: "large_unallocated_capital", entity: "portfolio", count: 3 }), t)).toBe(
      "Stort oallokerat kapital — 3 möjliga placeringar att överväga.",
    );
  });

  it("composes an executive_change fact from name, role, and event, never a raw enum", () => {
    const result = describeReasonFact(
      fact({ code: "executive_change", value: "appointment", secondaryValue: "ceo", label: "Lisa Su" }),
      t,
    );
    expect(result).toBe("Lisa Su (VD) tillträdde");
  });

  it("translates a management_credibility fact by its finding kind", () => {
    expect(describeReasonFact(fact({ code: "management_credibility", value: "inconsistent_follow_through" }), t)).toBe(
      "tidigare åtaganden har inte uppfyllts",
    );
  });

  it("translates business_quality with its single fixed phrase", () => {
    expect(describeReasonFact(fact({ code: "business_quality" }), t)).toBe("verksamhetens grundläggande siffror försvagas");
  });

  it("composes a case_condition_status fact from the investor's own predicate text, never translating it", () => {
    const result = describeReasonFact(
      fact({ code: "case_condition_status", value: "satisfied", label: "Data center capex growth decelerates below 10% YoY" }),
      t,
    );
    expect(result).toBe("Data center capex growth decelerates below 10% YoY (Uppfyllt)");
  });

  it("composes an assumption_status fact the same way", () => {
    const result = describeReasonFact(fact({ code: "assumption_status", value: "invalidated", label: "GCP margin expansion continues" }), t);
    expect(result).toBe("GCP margin expansion continues (Ogiltigförklarat)");
  });

  it("returns null when a required field is missing, never a partially composed sentence", () => {
    expect(describeReasonFact(fact({ code: "executive_change", value: "appointment", secondaryValue: "ceo", label: null }), t)).toBeNull();
    expect(describeReasonFact(fact({ code: "missing_evidence", value: null }), t)).toBeNull();
  });
});

describe("describeReasonLine", () => {
  it("falls back to the raw text when fact is null", () => {
    expect(describeReasonLine("AAPL: raw backend text", null, t)).toBe("AAPL: raw backend text");
  });

  it("falls back to the raw text when the fact can't be translated", () => {
    expect(describeReasonLine("AAPL: raw backend text", fact({ code: "missing_evidence", value: null }), t)).toBe(
      "AAPL: raw backend text",
    );
  });

  it("prefixes the ticker for a normal entity fact", () => {
    const result = describeReasonLine("raw", fact({ code: "concentration", entity: "NVDA", value: "high_concentration" }), t);
    expect(result).toBe("NVDA: hög koncentration i det här innehavet");
  });

  it("never prefixes a portfolio-level large_unallocated_capital fact with its own placeholder entity", () => {
    const result = describeReasonLine("raw", fact({ code: "large_unallocated_capital", entity: "portfolio", count: 2 }), t);
    expect(result).toBe("Stort oallokerat kapital — 2 möjliga placeringar att överväga.");
  });
});
