import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { PortfolioConvictionBreakdown } from "./PortfolioConvictionBreakdown";
import type { PortfolioConvictionBreakdownView } from "./recommendationConvictionApi";

function breakdown(overrides: Partial<PortfolioConvictionBreakdownView> = {}): PortfolioConvictionBreakdownView {
  return { highestConviction: [], lowestConviction: [], evidenceLimited: [], operationallyBlocked: [], ...overrides };
}

function Wrapper({ breakdown: b }: { breakdown: PortfolioConvictionBreakdownView }) {
  const { t } = useTranslation();
  return <PortfolioConvictionBreakdown breakdown={b} t={t} />;
}

function renderBreakdown(b: PortfolioConvictionBreakdownView) {
  return render(
    <LanguageProvider>
      <Wrapper breakdown={b} />
    </LanguageProvider>,
  );
}

describe("PortfolioConvictionBreakdown", () => {
  it("renders nothing when every bucket is empty", () => {
    const { container } = renderBreakdown(breakdown());
    expect(container).toBeEmptyDOMElement();
  });

  it("shows real counts per bucket", () => {
    renderBreakdown(breakdown({ highestConviction: ["AAPL", "MSFT"], operationallyBlocked: ["NVDA"] }));
    expect(screen.getByText("Starkast stöd (2)")).toBeInTheDocument();
    expect(screen.getByText("Operationellt blockerade (1)")).toBeInTheDocument();
  });

  it("omits a bucket entirely when it has no members", () => {
    renderBreakdown(breakdown({ highestConviction: ["AAPL"] }));
    expect(screen.queryByText(/Operationellt blockerade/)).not.toBeInTheDocument();
  });
});
