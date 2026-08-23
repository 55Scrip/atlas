import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { PortfolioReliabilityBreakdown } from "./PortfolioReliabilityBreakdown";
import type { PortfolioReliabilityBreakdownView } from "./decisionReliabilityApi";

function breakdown(overrides: Partial<PortfolioReliabilityBreakdownView> = {}): PortfolioReliabilityBreakdownView {
  return { mostReliable: [], leastReliable: [], recentlyImproved: [], recentlyWeakened: [], ...overrides };
}

function Wrapper({ breakdown: b }: { breakdown: PortfolioReliabilityBreakdownView }) {
  const { t } = useTranslation();
  return <PortfolioReliabilityBreakdown breakdown={b} t={t} />;
}

function renderBreakdown(b: PortfolioReliabilityBreakdownView) {
  return render(
    <LanguageProvider>
      <Wrapper breakdown={b} />
    </LanguageProvider>,
  );
}

describe("PortfolioReliabilityBreakdown", () => {
  it("renders nothing when every bucket is empty", () => {
    const { container } = renderBreakdown(breakdown());
    expect(container).toBeEmptyDOMElement();
  });

  it("shows real counts per bucket", () => {
    renderBreakdown(breakdown({ mostReliable: ["AAPL", "MSFT"], leastReliable: ["NVDA"] }));
    expect(screen.getByText("Mest tillförlitliga (2)")).toBeInTheDocument();
    expect(screen.getByText("Minst tillförlitliga (1)")).toBeInTheDocument();
  });

  it("omits a bucket entirely when it has no members", () => {
    renderBreakdown(breakdown({ mostReliable: ["AAPL"] }));
    expect(screen.queryByText(/Nyligen förbättrade/)).not.toBeInTheDocument();
  });
});
