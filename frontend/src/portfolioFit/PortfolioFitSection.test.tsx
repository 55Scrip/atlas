import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider } from "../i18n";
import { PortfolioFitSection } from "./PortfolioFitSection";
import type { PortfolioFitAssessmentView } from "./portfolioFitApi";
import type { CoverageAssessmentView } from "../coverage/coverageApi";

const EMPTY_COVERAGE: CoverageAssessmentView = {
  dimensions: [],
  overallCoverage: "no_coverage",
  overallConfidence: "very_limited",
  missingDimensions: [],
  notApplicableDimensions: [],
  reasoning: [],
};

function assessment(overrides: Partial<PortfolioFitAssessmentView> = {}): PortfolioFitAssessmentView {
  return {
    caseId: "case-1",
    ticker: "AAPL",
    isExistingHolding: true,
    currentWeightPercent: 12.5,
    overall: "good",
    overallReasoning: ["More dimensions rated Good/Excellent than Weak/Poor."],
    dimensions: [
      { kind: "business", rating: "good", reasoning: ["4 of 6 business categories rated Strong, 1 Moderate, 1 Weak."], unavailableReason: null },
      { kind: "risk", rating: "weak", reasoning: ["1 of 4 evaluated risk categories rated High, 1 Moderate, 2 Low."], unavailableReason: null },
      { kind: "cash_impact", rating: "unavailable", reasoning: [], unavailableReason: "Portfolio cash position has not been recorded." },
    ],
    trend: "improving",
    dataGaps: ["cash_impact: Portfolio cash position has not been recorded."],
    coverage: EMPTY_COVERAGE,
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function renderSection(a: PortfolioFitAssessmentView | null) {
  return render(
    <LanguageProvider>
      <PortfolioFitSection assessment={a} />
    </LanguageProvider>,
  );
}

describe("PortfolioFitSection", () => {
  it("shows the unavailable message when no assessment exists", () => {
    renderSection(null);
    expect(screen.getByText("Portföljpassform är inte tillgänglig för detta case än.")).toBeInTheDocument();
  });

  it("renders the overall rating and its reasoning verbatim", () => {
    renderSection(assessment());
    // "Bra passform" (Good Fit) appears twice by design: once for the
    // overall verdict, once for the Business dimension, which is also
    // rated Good in this fixture -- both are real, distinct badges.
    expect(screen.getAllByText("Bra passform").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("More dimensions rated Good/Excellent than Weak/Poor.")).toBeInTheDocument();
  });

  it("groups a Good dimension under 'why it fits' and a Weak one under 'what argues against'", () => {
    renderSection(assessment());
    expect(screen.getByText("Varför det passar")).toBeInTheDocument();
    expect(screen.getByText("Vad som talar emot")).toBeInTheDocument();
  });

  it("shows the trend line when trend is not unavailable", () => {
    renderSection(assessment());
    expect(screen.getByText("Passformen har förbättrats sedan din senaste genomgång")).toBeInTheDocument();
  });

  it("does not show a trend line when trend is unavailable", () => {
    renderSection(assessment({ trend: "unavailable" }));
    expect(screen.queryByText(/senaste genomgång/)).not.toBeInTheDocument();
  });

  it("discloses data gaps rather than omitting them silently", () => {
    renderSection(assessment());
    expect(screen.getByText("Vad Atlas inte kunde utvärdera:")).toBeInTheDocument();
    expect(screen.getByText("cash_impact: Portfolio cash position has not been recorded.")).toBeInTheDocument();
  });

  it("renders an unavailable dimension's own reason, not a fabricated rating", () => {
    renderSection(assessment());
    expect(screen.getByText("Portfolio cash position has not been recorded.")).toBeInTheDocument();
  });
});
