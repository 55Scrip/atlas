import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { PortfolioSharedWeakPointsSection } from "./PortfolioSharedWeakPointsSection";
import type { PortfolioSharedWeakPointsView } from "./portfolioSharedWeakPointsApi";

function points(overrides: Partial<PortfolioSharedWeakPointsView> = {}): PortfolioSharedWeakPointsView {
  return { sharedWeakAssumptions: [], sharedConditions: [], sharedMissingEvidence: [], ...overrides };
}

function Wrapper({ points: p }: { points: PortfolioSharedWeakPointsView }) {
  const { t } = useTranslation();
  return <PortfolioSharedWeakPointsSection points={p} t={t} />;
}

function renderSection(p: PortfolioSharedWeakPointsView) {
  return render(
    <LanguageProvider>
      <Wrapper points={p} />
    </LanguageProvider>,
  );
}

describe("PortfolioSharedWeakPointsSection", () => {
  it("renders nothing when there is nothing shared", () => {
    const { container } = renderSection(points());
    expect(container).toBeEmptyDOMElement();
  });

  it("names the real tickers and the real shared assumption text", () => {
    renderSection(
      points({
        sharedWeakAssumptions: [{ signature: "Demand stays strong", caseIds: ["a", "b"], tickers: ["NVDA", "AMD"] }],
      }),
    );
    expect(screen.getByText(/NVDA, AMD/)).toBeInTheDocument();
    expect(screen.getByText(/Demand stays strong/)).toBeInTheDocument();
  });
});
