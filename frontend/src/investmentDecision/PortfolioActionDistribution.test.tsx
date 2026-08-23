import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { PortfolioActionDistribution } from "./PortfolioActionDistribution";
import type { PortfolioActionDistributionView } from "./investmentDecisionApi";

function distribution(overrides: Partial<PortfolioActionDistributionView> = {}): PortfolioActionDistributionView {
  return { buy: [], add: [], hold: [], reduce: [], exit: [], wait: [], noDecision: [], ...overrides };
}

function Wrapper({ distribution: d }: { distribution: PortfolioActionDistributionView }) {
  const { t } = useTranslation();
  return <PortfolioActionDistribution distribution={d} t={t} />;
}

function renderDistribution(d: PortfolioActionDistributionView) {
  return render(
    <LanguageProvider>
      <Wrapper distribution={d} />
    </LanguageProvider>,
  );
}

describe("PortfolioActionDistribution", () => {
  it("renders nothing when every bucket is empty", () => {
    const { container } = renderDistribution(distribution());
    expect(container).toBeEmptyDOMElement();
  });

  it("shows real counts per bucket", () => {
    renderDistribution(distribution({ buy: ["AAPL", "MSFT"], reduce: ["NVDA"] }));
    expect(screen.getByText("Köp (2)")).toBeInTheDocument();
    expect(screen.getByText("Minska (1)")).toBeInTheDocument();
  });

  it("omits a bucket entirely when it has no members", () => {
    renderDistribution(distribution({ buy: ["AAPL"] }));
    expect(screen.queryByText(/Minska/)).not.toBeInTheDocument();
  });
});
