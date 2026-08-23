import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { PortfolioOpportunityCostBreakdown } from "./PortfolioOpportunityCostBreakdown";
import type { PortfolioOpportunityCostBreakdownView } from "./opportunityCostApi";

function breakdown(overrides: Partial<PortfolioOpportunityCostBreakdownView> = {}): PortfolioOpportunityCostBreakdownView {
  return {
    holdingsCompetingForCapital: [],
    watchlistCompetingWithHoldings: [],
    waitingPreferable: [],
    noActionAppropriate: [],
    ...overrides,
  };
}

function Wrapper({ breakdown: b }: { breakdown: PortfolioOpportunityCostBreakdownView }) {
  const { t } = useTranslation();
  return <PortfolioOpportunityCostBreakdown breakdown={b} t={t} />;
}

function renderBreakdown(b: PortfolioOpportunityCostBreakdownView) {
  return render(
    <LanguageProvider>
      <Wrapper breakdown={b} />
    </LanguageProvider>,
  );
}

describe("PortfolioOpportunityCostBreakdown", () => {
  it("renders nothing when every bucket is empty", () => {
    const { container } = renderBreakdown(breakdown());
    expect(container).toBeEmptyDOMElement();
  });

  it("shows real counts per bucket", () => {
    renderBreakdown(breakdown({ holdingsCompetingForCapital: ["AAPL", "MSFT"], waitingPreferable: ["NVDA"] }));
    expect(screen.getByText("Konkurrerar om kapital (2)")).toBeInTheDocument();
    expect(screen.getByText("Att vänta är att föredra (1)")).toBeInTheDocument();
  });

  it("omits a bucket entirely when it has no members", () => {
    renderBreakdown(breakdown({ holdingsCompetingForCapital: ["AAPL"] }));
    expect(screen.queryByText(/Att vänta är att föredra/)).not.toBeInTheDocument();
  });
});
