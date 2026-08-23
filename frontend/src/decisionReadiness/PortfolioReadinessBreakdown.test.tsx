import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { PortfolioReadinessBreakdown } from "./PortfolioReadinessBreakdown";
import type { PortfolioReadinessBreakdownView } from "./decisionReadinessApi";

function breakdown(overrides: Partial<PortfolioReadinessBreakdownView> = {}): PortfolioReadinessBreakdownView {
  return { ready: [], almostReady: [], waiting: [], blocked: [], unavailable: [], unknown: [], ...overrides };
}

function Wrapper({ breakdown: b }: { breakdown: PortfolioReadinessBreakdownView }) {
  const { t } = useTranslation();
  return <PortfolioReadinessBreakdown breakdown={b} t={t} />;
}

function renderBreakdown(b: PortfolioReadinessBreakdownView) {
  return render(
    <LanguageProvider>
      <Wrapper breakdown={b} />
    </LanguageProvider>,
  );
}

describe("PortfolioReadinessBreakdown", () => {
  it("renders nothing when every bucket is empty", () => {
    const { container } = renderBreakdown(breakdown());
    expect(container).toBeEmptyDOMElement();
  });

  it("shows real counts per bucket", () => {
    renderBreakdown(breakdown({ ready: ["AAPL", "MSFT"], blocked: ["NVDA"] }));
    expect(screen.getByText("Redo (2)")).toBeInTheDocument();
    expect(screen.getByText("Blockerade (1)")).toBeInTheDocument();
  });

  it("omits a bucket entirely when it has no members", () => {
    renderBreakdown(breakdown({ ready: ["AAPL"] }));
    expect(screen.queryByText(/Blockerade/)).not.toBeInTheDocument();
  });
});
