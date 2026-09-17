import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../testUtils";
import { ForwardViewSection, forwardViewSummary } from "./ForwardViewSection";
import { StrategySection } from "./StrategySection";
import { en } from "../i18n/translations/en";
import type { ForwardReasoningContextView } from "../investmentDecision/reasoningContract";

const t = ((key: string, params?: Record<string, string | number>) => {
  const value = (en as Record<string, string>)[key] ?? key;
  return params
    ? value.replace(/\{\{(\w+)\}\}/g, (_, name: string) => String(params[name] ?? ""))
    : value;
}) as never;

/** VST's real shape, reduced: two guided measures for 2026, both
 * reaffirmed, one of them a management-defined free-cash-flow measure. */
const GUIDANCE: ForwardReasoningContextView = {
  guidance: [
    {
      signalId: "sig:adjusted_ebitda:2026",
      subject: "adjusted_ebitda",
      measureDefinedByManagement: true,
      horizonPeriod: "2026",
      horizonKind: "unspecified_year",
      revision: "reaffirmed",
      valueText: "$6.8 billion-$7.6 billion",
      priorValueText: "$6.8 billion to $7.6 billion",
      sourcePeriod: "2026Q2",
      revisionCount: 1,
    },
    {
      signalId: "sig:free_cash_flow:2026",
      subject: "free_cash_flow",
      measureDefinedByManagement: true,
      horizonPeriod: "2026",
      horizonKind: "unspecified_year",
      revision: "raised",
      valueText: "$3.4 billion",
      priorValueText: "$3.1 billion",
      sourcePeriod: "2026Q2",
      revisionCount: 3,
    },
  ],
  contractedVolume: [],
  counterpartyTexts: [],
  unnamedObservationCount: 0,
  unestablishedEconomics: [],
  identityResolved: false,
};

const VOLUME: ForwardReasoningContextView = {
  guidance: [],
  contractedVolume: [
    {
      signalId: "sig:vol:1",
      sourcePeriod: "2026Q1",
      counterpartyText: "a hyperscaler",
      agreementText: "power supply agreement",
      quantityTexts: ["2 GW"],
      termYears: 12,
      deliveryStartYears: [2028],
      deliveryEndYears: [2040],
      notEstablished: ["price"],
    },
    {
      signalId: "sig:vol:2",
      sourcePeriod: "2026Q2",
      counterpartyText: null,
      agreementText: "long-term supply agreement",
      quantityTexts: ["600 MW"],
      termYears: null,
      deliveryStartYears: [],
      deliveryEndYears: [],
      notEstablished: [],
    },
  ],
  counterpartyTexts: ["a hyperscaler"],
  unnamedObservationCount: 1,
  unestablishedEconomics: ["price", "revenue_contribution", "earnings_contribution", "cash_flow_contribution"],
  identityResolved: false,
};

describe("Forward View -- honest absence", () => {
  // Product Convergence Sprint 1B: an absent capability costs a status
  // badge and one line, not a card. The chapter renders the absence
  // from `forwardViewSummary`; the panel below renders nothing at all,
  // which is what keeps the empty chapter short.
  it("reports the absence as a chapter headline, not a panel", () => {
    const summary = forwardViewSummary(null, t);
    expect(summary.hasEvidence).toBe(false);
    expect(summary.status).toBe(en["investmentCase.forwardView.status.none"]);
    expect(summary.headline).toBeNull();
  });

  it("treats a decision fetch still in flight the same honest way", () => {
    expect(forwardViewSummary(undefined, t).hasEvidence).toBe(false);
  });

  it("renders no panel at all when there is nothing to show", () => {
    const { container } = renderWithProviders(<ForwardViewSection context={null} t={t} />);
    expect(container.textContent).toBe("");
  });

  it("does not offer a historical trend in place of a forward claim", () => {
    // The chapter's own absence copy, which the page renders as the
    // headline, still says what is and is not being claimed.
    expect(en["investmentCase.forwardView.noneShort"]).toMatch(/No verified guidance or contracted volume/);
    expect(en["investmentCase.forwardView.noneShort"]).not.toMatch(/growth rate|CAGR|forecast/i);
  });
});

describe("Forward View -- chapter headline", () => {
  it("counts what Atlas verified, and judges none of it", () => {
    const summary = forwardViewSummary(GUIDANCE, t);
    expect(summary.hasEvidence).toBe(true);
    expect(summary.status).toBe(en["investmentCase.forwardView.status.present"]);
    expect(summary.headline).toBe("2 guided measures");
    // No polarity anywhere in the headline: a reaffirmed or raised
    // figure is neither good nor bad news here.
    expect(summary.headline).not.toMatch(/positive|supportive|strong|raised|lowered/i);
  });

  it("names guidance and contracted volume separately, never summed", () => {
    const both = forwardViewSummary({ ...GUIDANCE, contractedVolume: VOLUME.contractedVolume }, t);
    expect(both.headline).toBe("2 guided measures · 2 contracted-volume observations");
  });

  it("uses the singular form for a single observation", () => {
    const one = forwardViewSummary({ ...VOLUME, contractedVolume: [VOLUME.contractedVolume[0]!] }, t);
    expect(one.headline).toBe("1 contracted-volume observation");
  });
});

describe("Forward View -- real evidence", () => {
  it("states each guided measure in management's own figures", () => {
    const { container } = renderWithProviders(<ForwardViewSection context={GUIDANCE} t={t} />);
    expect(container.textContent).toContain("$6.8 billion-$7.6 billion");
    expect(container.textContent).toContain("$3.4 billion");
    // A management-defined measure is always qualified, never presented
    // as Atlas's own free-cash-flow figure.
    expect(container.textContent).toContain("management's definition");
  });

  it("reads a reaffirmation as unchanged, never as supportive", () => {
    const { container } = renderWithProviders(<ForwardViewSection context={GUIDANCE} t={t} />);
    expect(container.textContent).toContain("unchanged at");
    expect(container.textContent).not.toMatch(/positive|supportive|strong|bullish/i);
  });

  it("adds the detail the conclusion's one-line summary does not carry", () => {
    // This chapter exists to add depth, not to repeat the conclusion.
    // The source period is the detail the summary row omits.
    const { container } = renderWithProviders(<ForwardViewSection context={GUIDANCE} t={t} />);
    expect(container.textContent).toContain("Stated in 2026Q2");
    expect(container.textContent).toContain("3 verified revisions");
  });

  it("frames the whole chapter as evidence, not forecast or driver", () => {
    const { container } = renderWithProviders(<ForwardViewSection context={GUIDANCE} t={t} />);
    expect(container.textContent).toContain("Not a forecast");
    expect(container.textContent).toContain("not a reason for or against the recommendation");
  });

  it("lists contracted volume observation by observation, never summed", () => {
    const { container } = renderWithProviders(<ForwardViewSection context={VOLUME} t={t} />);
    expect(container.textContent).toContain("a hyperscaler");
    expect(container.textContent).toContain("2 GW");
    expect(container.textContent).toContain("600 MW");
    expect(container.textContent).toContain("an unnamed customer");
    // The warning that one agreement can appear in several observations.
    expect(container.textContent).toContain("never added up");
    // No total anywhere.
    expect(container.textContent).not.toContain("2.6 GW");
  });

  it("carries the economics the contract does not establish", () => {
    const { container } = renderWithProviders(<ForwardViewSection context={VOLUME} t={t} />);
    expect(container.textContent).toContain(en["investmentReasoning.forward.unknown.allEconomics"]);
  });
});

describe("Strategy -- honestly unavailable", () => {
  it("says so in one line, and shows no substitute assessment", () => {
    // Sprint 1B: this was two paragraphs and 184px for a capability
    // Atlas does not have. The status badge beside the chapter title
    // carries the answer; this is the whole body.
    const { container } = renderWithProviders(<StrategySection t={t} />);
    expect(screen.getByText(en["investmentCase.strategy.unavailableShort"])).toBeTruthy();
    expect(container.querySelectorAll("p")).toHaveLength(1);
    // Nothing that would read as a strategy verdict built out of
    // business-quality or moat figures.
    expect(container.textContent).not.toMatch(/moat|competitive advantage|score|rating|\d/i);
  });

  it("is named as unassessed rather than as a weakness", () => {
    // "Not yet assessed" is a statement about Atlas, not about the
    // company -- a company with no strategy model must never read as a
    // company with no strategy.
    expect(en["investmentCase.strategy.status.notAssessed"]).toBe("Not yet assessed");
    expect(en["investmentCase.strategy.unavailableShort"]).toMatch(/^Atlas does not yet/);
  });
});
