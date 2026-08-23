import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { PortfolioDecisionMemoryBreakdown } from "./PortfolioDecisionMemoryBreakdown";
import type { PortfolioDecisionMemoryBreakdownView } from "./decisionMemoryApi";

function breakdown(overrides: Partial<PortfolioDecisionMemoryBreakdownView> = {}): PortfolioDecisionMemoryBreakdownView {
  return { recentlyChanged: [], stable: [], recentlyStrengthened: [], recentlyWeakened: [], ...overrides };
}

function Wrapper({ breakdown: b }: { breakdown: PortfolioDecisionMemoryBreakdownView }) {
  const { t } = useTranslation();
  return <PortfolioDecisionMemoryBreakdown breakdown={b} t={t} />;
}

function renderBreakdown(b: PortfolioDecisionMemoryBreakdownView) {
  return render(
    <LanguageProvider>
      <Wrapper breakdown={b} />
    </LanguageProvider>,
  );
}

describe("PortfolioDecisionMemoryBreakdown", () => {
  it("renders nothing when every bucket is empty", () => {
    const { container } = renderBreakdown(breakdown());
    expect(container).toBeEmptyDOMElement();
  });

  it("shows real counts per bucket", () => {
    renderBreakdown(breakdown({ recentlyChanged: ["AAPL", "MSFT"], stable: ["NVDA"] }));
    expect(screen.getByText("Nyligen ändrade (2)")).toBeInTheDocument();
    expect(screen.getByText("Stabila (1)")).toBeInTheDocument();
  });

  it("omits a bucket entirely when it has no members", () => {
    renderBreakdown(breakdown({ recentlyChanged: ["AAPL"] }));
    expect(screen.queryByText(/Stabila/)).not.toBeInTheDocument();
  });
});
