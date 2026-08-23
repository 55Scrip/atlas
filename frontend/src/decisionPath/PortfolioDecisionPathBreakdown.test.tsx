import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { PortfolioDecisionPathBreakdown } from "./PortfolioDecisionPathBreakdown";
import type { PortfolioDecisionPathBreakdownView } from "./decisionPathApi";

function breakdown(overrides: Partial<PortfolioDecisionPathBreakdownView> = {}): PortfolioDecisionPathBreakdownView {
  return {
    closestToInvestable: [],
    operationallyBlocked: [],
    requiringMoreEvidence: [],
    requiringDependencyResolution: [],
    ...overrides,
  };
}

function Wrapper({ breakdown: b }: { breakdown: PortfolioDecisionPathBreakdownView }) {
  const { t } = useTranslation();
  return <PortfolioDecisionPathBreakdown breakdown={b} t={t} />;
}

function renderBreakdown(b: PortfolioDecisionPathBreakdownView) {
  return render(
    <LanguageProvider>
      <Wrapper breakdown={b} />
    </LanguageProvider>,
  );
}

describe("PortfolioDecisionPathBreakdown", () => {
  it("renders nothing when every bucket is empty", () => {
    const { container } = renderBreakdown(breakdown());
    expect(container).toBeEmptyDOMElement();
  });

  it("shows real counts per bucket", () => {
    renderBreakdown(breakdown({ closestToInvestable: ["AAPL", "MSFT"], operationallyBlocked: ["NVDA"] }));
    expect(screen.getByText("Närmast investeringsbart (2)")).toBeInTheDocument();
    expect(screen.getByText("Vägen operationellt blockerad (1)")).toBeInTheDocument();
  });

  it("omits a bucket entirely when it has no members", () => {
    renderBreakdown(breakdown({ closestToInvestable: ["AAPL"] }));
    expect(screen.queryByText(/Vägen operationellt blockerad/)).not.toBeInTheDocument();
  });

  it("uses text distinguishable from RecommendationConviction's own portfolio breakdown labels", () => {
    /* Live-verification finding: both breakdowns can legitimately name
     * the same tickers for different reasons (Conviction's own
     * stability vs. this package's own decision-path dependency) --
     * identical rendered text for two different facts reads as a
     * glitch, so the copy must be distinct even when the counts
     * coincide. */
    renderBreakdown(breakdown({ requiringMoreEvidence: ["AAPL"], operationallyBlocked: ["MSFT"] }));
    expect(screen.queryByText("Behöver mer underlag (1)")).not.toBeInTheDocument();
    expect(screen.queryByText("Operationellt blockerade (1)")).not.toBeInTheDocument();
  });
});
