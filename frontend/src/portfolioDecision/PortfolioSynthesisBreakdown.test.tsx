import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { PortfolioSynthesisBreakdown } from "./PortfolioSynthesisBreakdown";
import type { PortfolioSynthesisBreakdownView } from "./portfolioDecisionApi";

function breakdown(overrides: Partial<PortfolioSynthesisBreakdownView> = {}): PortfolioSynthesisBreakdownView {
  return { supportsPortfolio: [], highestCapitalCompetition: [], conflictsWithPortfolio: [], neutral: [], ...overrides };
}

function Wrapper({ breakdown: b }: { breakdown: PortfolioSynthesisBreakdownView }) {
  const { t } = useTranslation();
  return <PortfolioSynthesisBreakdown breakdown={b} t={t} />;
}

function renderBreakdown(b: PortfolioSynthesisBreakdownView) {
  return render(
    <LanguageProvider>
      <Wrapper breakdown={b} />
    </LanguageProvider>,
  );
}

describe("PortfolioSynthesisBreakdown", () => {
  it("renders nothing when every bucket is empty", () => {
    const { container } = renderBreakdown(breakdown());
    expect(container).toBeEmptyDOMElement();
  });

  it("shows real counts per bucket", () => {
    renderBreakdown(breakdown({ supportsPortfolio: ["AAPL", "MSFT"], conflictsWithPortfolio: ["NVDA"] }));
    expect(screen.getByText("Stödjer portföljen (2)")).toBeInTheDocument();
    expect(screen.getByText("Står i konflikt med portföljen (1)")).toBeInTheDocument();
  });

  it("omits a bucket entirely when it has no members", () => {
    renderBreakdown(breakdown({ supportsPortfolio: ["AAPL"] }));
    expect(screen.queryByText(/Högst kapitalkonkurrens/)).not.toBeInTheDocument();
  });
});
