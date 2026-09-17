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
    overallReasoningCode: null,
    overallReasoningCount: null,
    dimensions: [
      { kind: "allocation", rating: "good", reasoning: ["This holding is 12.5% of the portfolio (portfolio concentration overall: moderate)."], unavailableReason: null },
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

  it("renders the overall rating, falling back to the raw sentence when no reasoning code is present", () => {
    renderSection(assessment());
    // "Bra passform" (Good Fit) appears twice by design: once for the
    // overall verdict, once for the Business dimension, which is also
    // rated Good in this fixture -- both are real, distinct badges.
    expect(screen.getAllByText("Bra passform").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("More dimensions rated Good/Excellent than Weak/Poor.")).toBeInTheDocument();
  });

  it("Sprint 11 Phase 3: prefers the translated, code-driven verdict sentence over the raw English one", () => {
    renderSection(assessment({ overallReasoningCode: "more_good_excellent_than_weak_poor", overallReasoningCount: null }));
    expect(screen.getByText("Fler dimensioner är bra eller utmärkta än svaga eller dåliga.")).toBeInTheDocument();
    expect(screen.queryByText("More dimensions rated Good/Excellent than Weak/Poor.")).not.toBeInTheDocument();
  });

  it("interpolates the real count for a reasoning code that carries one", () => {
    renderSection(assessment({ overallReasoningCode: "multiple_poor", overallReasoningCount: 2 }));
    expect(screen.getByText("2 dimensioner är bedömda som dåliga.")).toBeInTheDocument();
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

describe("PortfolioFitSection — Convergence Sprint 1 compression", () => {
  // `ExpandableDetail` is a native <details>. Its children stay in the DOM
  // when closed, so "is it on the primary reading surface?" is asserted the
  // way this codebase already asserts it (AtlasReasoningSection.test.tsx):
  // via the `open` attribute and containment, never by queryByText absence.

  it("shows the distilled result on the primary surface", () => {
    renderSection(assessment());
    // Superseded by Position Editor v1. Sprint 1 asserted the *overall*
    // verdict was the distilled result. It is not: it votes across five
    // dimensions, three of which describe the company rather than the
    // portfolio, with a Poor Risk Fit as a hard gate -- so it could read
    // "Weak Fit" purely because the stock is expensive, which the Case
    // says at length in its own chapters. The distilled portfolio-fit
    // result is the one dimension that asks a portfolio question.
    const distilled = screen.getByText(/12,5 % av portföljen|12.5% of the portfolio/);
    expect(distilled.closest("details")).toBeNull();
  });

  it("Position Editor v1: keeps the case-quality verdict, but behind disclosure", () => {
    renderSection(assessment());
    const verdict = screen.getByText(/More dimensions rated Good\/Excellent/);
    expect(verdict.closest("details")).not.toBeNull();
  });

  it("Position Editor v1: names what Atlas does not yet assess, on every holding", () => {
    // Stated unconditionally, not only when a dimension is missing: the
    // absence of overlap and correlation analysis is a property of Atlas
    // today, not a gap in this holding's data. A reader who sees only
    // "Bra passform" would otherwise reasonably conclude Atlas had
    // checked this position against the rest of the portfolio.
    renderSection(assessment());
    const gap = screen.getByText(/bedömer ännu inte sektor/);
    expect(gap).toBeInTheDocument();
    expect(gap.closest("details")).toBeNull();
  });

  it("Position Editor v1: says so plainly when no portfolio-relative dimension exists", () => {
    const withoutAllocation = assessment();
    renderSection({
      ...withoutAllocation,
      dimensions: withoutAllocation.dimensions.filter((d) => d.kind !== "allocation"),
    });
    expect(
      screen.getByText("Atlas har ännu ingen portföljrelativ bedömning för det här innehavet."),
    ).toBeInTheDocument();
  });

  it("keeps every per-dimension row closed by default", () => {
    renderSection(assessment());
    const details = screen.getByText("Alla dimensioner").closest("details");
    expect(details).not.toBeNull();
    expect(details).not.toHaveAttribute("open");
    // Before this sprint these rows rendered inline, ahead of the page's own
    // Atlas conclusion.
    expect(details).toContainElement(screen.getByText(/4 of 6 business categories rated Strong/));
    expect(details).toContainElement(screen.getByText(/1 of 4 evaluated risk categories rated High/));
  });

  it("preserves honest data gaps rather than dropping them", () => {
    renderSection(assessment());
    const details = screen.getByText("Alla dimensioner").closest("details");
    expect(details).toContainElement(
      screen.getByText(/cash_impact: Portfolio cash position has not been recorded\./),
    );
  });

  it("renders no disclosure affordance when there is nothing behind it", () => {
    renderSection(assessment({ dimensions: [], dataGaps: [] }));
    expect(screen.queryByText("Alla dimensioner")).not.toBeInTheDocument();
  });
});
