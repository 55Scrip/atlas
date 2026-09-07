import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { AtlasInvestmentReasoning } from "./AtlasInvestmentReasoning";
import type { InvestmentDecisionView } from "./investmentDecisionApi";
import type { RecommendationReasoningView } from "./reasoningContract";

/** Shaped exactly as `serialize_reasoning` writes it -- a directional
 * case: drivers on both sides, an unresolved unknown, a change
 * trigger, and a stated Recommendation Conviction (which the backend
 * structurally refuses to produce for a withheld outcome). */
function reasoning(overrides: Partial<RecommendationReasoningView> = {}): RecommendationReasoningView {
  return {
    schemaVersion: 1,
    primaryDrivers: [
      { kind: "growth_strong", polarity: "supportive", engine: "growth", sourceStatus: "strong" },
      { kind: "valuation_undervalued", polarity: "supportive", engine: "valuation", sourceStatus: "undervalued" },
    ],
    counterDrivers: [
      {
        kind: "financial_risk_elevated",
        polarity: "adverse",
        engine: "financial_risk",
        sourceStatus: "high",
      },
    ],
    signalSummary: [],
    keyUnknowns: [{ kind: "analysis_complete_unresolved", engine: "valuation_support" }],
    whatWouldChange: ["reduced_risk"],
    recommendationConviction: { level: "high", analyticalReasons: [], evidentialReasons: [] },
    ...overrides,
  };
}

function decision(overrides: Partial<InvestmentDecisionView> = {}): InvestmentDecisionView {
  return {
    caseId: "case-1",
    action: "buy",
    qualifiers: [],
    supportingReasons: [],
    blockers: [],
    changeTrigger: null,
    generatedAt: "2026-01-01T00:00:00Z",
    reasoning: reasoning(),
    ...overrides,
  };
}

function Wrapper({ decision: d }: { decision: InvestmentDecisionView }) {
  const { t } = useTranslation();
  return <AtlasInvestmentReasoning decision={d} t={t} />;
}

function renderCard(d: InvestmentDecisionView) {
  return render(
    <LanguageProvider>
      <Wrapper decision={d} />
    </LanguageProvider>,
  );
}

describe("AtlasInvestmentReasoning -- directional case", () => {
  it("renders the canonical drivers, counter-drivers, unknowns and change triggers", () => {
    renderCard(decision());
    expect(screen.getByText(/Stark tillväxt/)).toBeInTheDocument();
    expect(screen.getByText(/Lågt värderad/)).toBeInTheDocument();
    expect(screen.getByText(/Förhöjd finansiell risk/)).toBeInTheDocument();
    expect(screen.getByText(/Olöst efter analys: värderingsstöd/)).toBeInTheDocument();
    expect(screen.getByText(/Lägre risk/)).toBeInTheDocument();
  });

  it("states the recommendation Atlas actually reached", () => {
    renderCard(decision({ action: "buy" }));
    expect(screen.getByText(/Atlas slutsats: Köp\./)).toBeInTheDocument();
  });

  it("does not state that a recommendation is withheld", () => {
    renderCard(decision());
    expect(screen.queryByText(/stöder ännu ingen riktad rekommendation/)).not.toBeInTheDocument();
  });
});

describe("AtlasInvestmentReasoning -- withheld case", () => {
  const withheld = () =>
    decision({
      action: "no_decision",
      reasoning: reasoning({ recommendationConviction: null }),
    });

  it("states plainly that Atlas supports no directional recommendation", () => {
    renderCard(withheld());
    expect(screen.getByText(/Atlas stöder ännu ingen riktad rekommendation\./)).toBeInTheDocument();
  });

  it("still shows the reasoning -- no decision must not mean no reasoning", () => {
    renderCard(withheld());
    expect(screen.getByText(/Stark tillväxt/)).toBeInTheDocument();
    expect(screen.getByText(/Förhöjd finansiell risk/)).toBeInTheDocument();
    expect(screen.getByText(/Olöst efter analys: värderingsstöd/)).toBeInTheDocument();
  });

  it("frames the same drivers as evidence, never as an action", () => {
    renderCard(withheld());
    expect(screen.getByText(/Underlaget talar för/)).toBeInTheDocument();
    expect(screen.getByText(/Underlaget talar emot/)).toBeInTheDocument();
    // Negative control: the directional framing must be absent.
    expect(screen.queryByText(/Atlas slutsats/)).not.toBeInTheDocument();
  });

  it("never renders a directional action word for a withheld outcome", () => {
    const { container } = renderCard(withheld());
    const text = container.textContent ?? "";
    for (const word of ["Köp", "Öka innehav", "Avyttra", "Minska"]) {
      expect(text).not.toContain(word);
    }
  });
});

describe("AtlasInvestmentReasoning -- absence", () => {
  it("renders nothing when reasoning is absent (legacy rows)", () => {
    const { container } = renderCard(decision({ reasoning: null }));
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing rather than an empty shell when reasoning carries no content", () => {
    const { container } = renderCard(
      decision({
        reasoning: {
          schemaVersion: 1,
          primaryDrivers: [],
          counterDrivers: [],
          signalSummary: [],
          keyUnknowns: [],
          whatWouldChange: [],
          recommendationConviction: null,
        },
      }),
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("survives a legacy payload whose collection keys are missing entirely", () => {
    const { container } = renderCard(
      decision({ reasoning: { schemaVersion: 1 } as RecommendationReasoningView }),
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("renders what a partial legacy payload does contain", () => {
    renderCard(
      decision({
        reasoning: {
          schemaVersion: 1,
          primaryDrivers: [
            { kind: "growth_weak", polarity: "adverse", engine: "growth", sourceStatus: "weak" },
          ],
        } as RecommendationReasoningView,
      }),
    );
    expect(screen.getByText(/Svag tillväxt/)).toBeInTheDocument();
  });
});

describe("AtlasInvestmentReasoning -- what it must not do", () => {
  it("introduces no Figma-only metric or action vocabulary", () => {
    const { container } = renderCard(decision());
    const text = (container.textContent ?? "").toLowerCase();
    for (const forbidden of ["upside", "downside", "uppsida", "nedsida", "conviction", "% ", "kr", "target"]) {
      expect(text).not.toContain(forbidden);
    }
  });

  it("does not surface engine-wiring unknowns as company uncertainty", () => {
    renderCard(
      decision({
        reasoning: reasoning({
          keyUnknowns: [{ kind: "not_connected_to_direction", engine: "expected_return" }],
        }),
      }),
    );
    expect(screen.queryByText(/förväntad avkastning/)).not.toBeInTheDocument();
  });
});
