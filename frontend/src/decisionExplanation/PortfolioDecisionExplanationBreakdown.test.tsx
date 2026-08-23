import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { PortfolioDecisionExplanationBreakdown } from "./PortfolioDecisionExplanationBreakdown";
import type { PortfolioDecisionExplanationBreakdownView } from "./decisionExplanationApi";

function breakdown(overrides: Partial<PortfolioDecisionExplanationBreakdownView> = {}): PortfolioDecisionExplanationBreakdownView {
  return { recentlyChanged: [], newSupportingFindings: [], resolvedBlockers: [], recentlyStrengthened: [], ...overrides };
}

function Wrapper({ breakdown: b }: { breakdown: PortfolioDecisionExplanationBreakdownView }) {
  const { t } = useTranslation();
  return <PortfolioDecisionExplanationBreakdown breakdown={b} t={t} />;
}

function renderBreakdown(b: PortfolioDecisionExplanationBreakdownView) {
  return render(
    <LanguageProvider>
      <Wrapper breakdown={b} />
    </LanguageProvider>,
  );
}

describe("PortfolioDecisionExplanationBreakdown", () => {
  it("renders nothing when every bucket is empty", () => {
    const { container } = renderBreakdown(breakdown());
    expect(container).toBeEmptyDOMElement();
  });

  it("shows real counts per bucket", () => {
    renderBreakdown(breakdown({ recentlyChanged: ["AAPL", "MSFT"], resolvedBlockers: ["NVDA"] }));
    expect(screen.getByText("Förklaring ändrad (2)")).toBeInTheDocument();
    expect(screen.getByText("Lösta hinder (1)")).toBeInTheDocument();
  });

  it("omits a bucket entirely when it has no members", () => {
    renderBreakdown(breakdown({ recentlyChanged: ["AAPL"] }));
    expect(screen.queryByText(/Nya stödjande skäl/)).not.toBeInTheDocument();
  });
});
