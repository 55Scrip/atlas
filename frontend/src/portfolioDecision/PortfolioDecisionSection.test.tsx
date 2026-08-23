import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { PortfolioDecisionSection } from "./PortfolioDecisionSection";
import type { PortfolioDecisionReasonView, PortfolioDecisionView } from "./portfolioDecisionApi";
import type { DecisionAlternativeView } from "../opportunityCost/opportunityCostApi";

function reason(source: PortfolioDecisionReasonView["source"], id: string): PortfolioDecisionReasonView {
  return { source, reference: { kind: "reason_code", id } };
}

function alternative(kind: DecisionAlternativeView["kind"], caseId = "other-case"): DecisionAlternativeView {
  return {
    kind,
    caseId,
    ticker: "OTHER",
    action: "buy",
    strength: null,
    reason: { source: "stance", code: "some_reason" },
  };
}

function decision(overrides: Partial<PortfolioDecisionView> = {}): PortfolioDecisionView {
  return {
    caseId: "case-1",
    action: "hold",
    category: "neutral",
    impact: {
      isExistingHolding: true,
      currentWeightPercent: 10,
      isLargestPosition: false,
      allocationRating: "neutral",
      portfolioConcentrationLevel: "Low",
    },
    capitalCompetition: { caseId: "case-1", competingAlternatives: [], nonCompetingAlternatives: [] },
    supportingReasons: [],
    limitingReasons: [],
    primaryLimitingReason: null,
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function Wrapper({ decision: d }: { decision: PortfolioDecisionView }) {
  const { t } = useTranslation();
  return <PortfolioDecisionSection decision={d} t={t} />;
}

function renderSection(d: PortfolioDecisionView) {
  return render(
    <LanguageProvider>
      <Wrapper decision={d} />
    </LanguageProvider>,
  );
}

describe("PortfolioDecisionSection", () => {
  it("shows the translated category badge", () => {
    renderSection(decision({ category: "conflicts_with_portfolio" }));
    expect(screen.getByText("Står i konflikt med portföljen")).toBeInTheDocument();
  });

  it("shows the honest 'no limitation' disclosure when there is none", () => {
    renderSection(decision());
    expect(screen.getByText("Atlas identifierar för närvarande ingen specifik portföljbegränsning.")).toBeInTheDocument();
  });

  it("shows the primary limiting reason when one exists", () => {
    renderSection(
      decision({
        primaryLimitingReason: reason("portfolio_fit", "poor"),
        limitingReasons: [reason("portfolio_fit", "poor")],
      }),
    );
    expect(screen.getByText(/Atlas identifierar för närvarande:/)).toBeInTheDocument();
  });

  it("shows the capital competition summary when a real competitor exists", () => {
    renderSection(
      decision({
        action: "buy",
        capitalCompetition: {
          caseId: "case-1",
          competingAlternatives: [alternative("increase_existing_holding")],
          nonCompetingAlternatives: [],
        },
      }),
    );
    expect(screen.getByText(/konkurrerar för närvarande med 1 annat verkligt alternativ/)).toBeInTheDocument();
  });

  it("shows the full breakdown with source provenance when expanded", () => {
    const item = reason("decision_reliability", "high");
    renderSection(
      decision({
        primaryLimitingReason: null,
        supportingReasons: [item],
      }),
    );
    screen.getByText("Visa fullständig portföljbedömning").click();
    expect(screen.getByText("Beslutets tillförlitlighet")).toBeInTheDocument();
  });

  it("does not show the expand control when there is nothing more to show", () => {
    renderSection(decision());
    expect(screen.queryByText("Visa fullständig portföljbedömning")).not.toBeInTheDocument();
  });

  it("never renders raw technical, AI, or portfolio-optimization vocabulary", () => {
    renderSection(decision());
    expect(screen.queryByText(/\bengine\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bAI\b/)).not.toBeInTheDocument();
    expect(screen.queryByText(/\boptimal\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/target allocation/i)).not.toBeInTheDocument();
  });
});
