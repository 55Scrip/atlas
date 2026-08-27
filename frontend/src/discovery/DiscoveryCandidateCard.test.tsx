import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LanguageProvider } from "../i18n";
import { DiscoveryCandidateCard } from "./DiscoveryCandidateCard";
import type { PortfolioFitAssessmentView } from "../portfolioFit/portfolioFitApi";
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
    ticker: "NVDA",
    isExistingHolding: false,
    currentWeightPercent: null,
    overall: "good",
    overallReasoning: ["More dimensions rated Good/Excellent than Weak/Poor."],
    dimensions: [
      { kind: "business", rating: "good", reasoning: ["4 of 6 categories rated Strong."], unavailableReason: null },
      { kind: "risk", rating: "weak", reasoning: ["High financial risk."], unavailableReason: null },
    ],
    trend: "unavailable",
    dataGaps: [],
    coverage: EMPTY_COVERAGE,
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function renderCard(props: Partial<Parameters<typeof DiscoveryCandidateCard>[0]> = {}) {
  return render(
    <LanguageProvider>
      <DiscoveryCandidateCard ticker="NVDA" assessment={assessment()} variant="primary" onOpenCase={vi.fn()} {...props} />
    </LanguageProvider>,
  );
}

describe("DiscoveryCandidateCard -- primary variant (Discover Doctrine, Highest opportunity)", () => {
  it("renders the ticker and Fit badge", () => {
    renderCard();
    expect(screen.getByText("NVDA")).toBeInTheDocument();
    expect(screen.getByText("Bra passform")).toBeInTheDocument();
  });

  it("shows exactly one sentence -- the synthesized Fit reasoning, never a raw event headline", () => {
    renderCard();
    expect(screen.getByText("More dimensions rated Good/Excellent than Weak/Poor.")).toBeInTheDocument();
  });

  it("shows the Stance badge alongside Fit when a Stance level is provided", () => {
    renderCard({ stance: "increase" });
    expect(screen.getByText("Synen har stärkts")).toBeInTheDocument();
    expect(screen.getByText("Bra passform")).toBeInTheDocument();
  });

  it("shows no Stance badge when none exists, never a fabricated one", () => {
    renderCard({ stance: null });
    expect(screen.queryByText(/Synen|Genomgång krävs/)).not.toBeInTheDocument();
  });

  it("never renders the Evidence quality / Evidence history / Why? disclosures -- internal analysis machinery that belongs only in Investment Case (Phase 4)", () => {
    renderCard();
    expect(screen.queryByText("Varför?")).not.toBeInTheDocument();
    expect(screen.queryByText("Bevisunderlagets kvalitet")).not.toBeInTheDocument();
    expect(screen.queryByText("Bevishistorik")).not.toBeInTheDocument();
  });

  it("never renders a dimension breakdown or data-gaps list -- Investment Case owns that depth, not the primary card", () => {
    renderCard();
    expect(screen.queryByText("Varför det passar")).not.toBeInTheDocument();
    expect(screen.queryByText("Vad som talar emot")).not.toBeInTheDocument();
  });

  it("calls onOpenCase when Open Investment Case is clicked", async () => {
    const onOpen = vi.fn();
    const user = userEvent.setup();
    renderCard({ onOpenCase: onOpen });
    await user.click(screen.getByRole("button", { name: "Öppna investeringscase" }));
    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it("shows Compare only when onCompare is provided", () => {
    const { rerender } = renderCard({ onCompare: vi.fn() });
    expect(screen.getByRole("button", { name: "Jämför" })).toBeInTheDocument();
    rerender(
      <LanguageProvider>
        <DiscoveryCandidateCard ticker="NVDA" assessment={assessment()} variant="primary" onOpenCase={vi.fn()} />
      </LanguageProvider>,
    );
    expect(screen.queryByRole("button", { name: "Jämför" })).not.toBeInTheDocument();
  });

  it("shows Remove from Watchlist as a plain link, not a button, only when the callback is provided", () => {
    renderCard({ onRemoveFromWatchlist: vi.fn() });
    expect(screen.getByRole("link", { name: "Ta bort från bevakningslistan" })).toBeInTheDocument();
  });

  it("never renders a numeric score anywhere on the card", () => {
    renderCard();
    const numbers = screen.queryAllByText(/^\d+$|^\d+\/\d+$|^\d+%$/);
    expect(numbers).toHaveLength(0);
  });
});

describe("DiscoveryCandidateCard -- secondary variant (Worth reviewing / Everything else)", () => {
  function renderSecondary(props: Partial<Parameters<typeof DiscoveryCandidateCard>[0]> = {}) {
    return render(
      <LanguageProvider>
        <DiscoveryCandidateCard ticker="NVDA" assessment={assessment()} variant="secondary" onOpenCase={vi.fn()} {...props} />
      </LanguageProvider>,
    );
  }

  it("shows ticker, rating, and one-line verdict, nothing more (Phase 3)", () => {
    renderSecondary();
    expect(screen.getByText("NVDA")).toBeInTheDocument();
    expect(screen.getByText("Bra passform")).toBeInTheDocument();
    expect(screen.getByText("More dimensions rated Good/Excellent than Weak/Poor.")).toBeInTheDocument();
  });

  it("shows only one action -- Open Investment Case, never Compare or Remove from Watchlist", () => {
    renderSecondary({ onCompare: vi.fn(), onRemoveFromWatchlist: vi.fn() });
    expect(screen.getByRole("button", { name: "Öppna investeringscase" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Jämför" })).not.toBeInTheDocument();
    expect(screen.queryByText("Ta bort från bevakningslistan")).not.toBeInTheDocument();
  });

  it("shows a disclosed 'fit pending' state, never a fabricated rating, when no assessment exists yet", () => {
    renderSecondary({ assessment: null });
    expect(screen.getByText("Bygg investeringscaset innan Atlas kan utvärdera portföljpassform.")).toBeInTheDocument();
  });

  it("never renders any expandable disclosure", () => {
    renderSecondary();
    expect(screen.queryByText("Varför?")).not.toBeInTheDocument();
    expect(screen.queryByText("Bevisunderlagets kvalitet")).not.toBeInTheDocument();
  });
});

describe("DiscoveryCandidateCard -- full variant (Candidate Detail)", () => {
  function renderFull(props: Partial<Parameters<typeof DiscoveryCandidateCard>[0]> = {}) {
    return render(
      <LanguageProvider>
        <DiscoveryCandidateCard
          ticker="NVDA"
          reasonKey="discovery.card.reason.watchlist"
          assessment={assessment()}
          isOnWatchlist={true}
          isHolding={false}
          variant="full"
          onOpenCase={vi.fn()}
          {...props}
        />
      </LanguageProvider>,
    );
  }

  it("shows the generic membership reason line", () => {
    renderFull();
    expect(screen.getByText("På din bevakningslista")).toBeInTheDocument();
  });

  it("renders strongest positives and limitations grouped from the shared dimension-grouping rule", () => {
    renderFull();
    expect(screen.getByText("Varför det passar")).toBeInTheDocument();
    expect(screen.getByText("4 of 6 categories rated Strong.")).toBeInTheDocument();
    expect(screen.getByText("Vad som talar emot")).toBeInTheDocument();
    expect(screen.getByText("High financial risk.")).toBeInTheDocument();
  });

  it("shows the disclosed-gap message and an Add-to-Watchlist action for a candidate with neither a Case nor a Watchlist entry", () => {
    const onAdd = vi.fn();
    renderFull({ assessment: null, isOnWatchlist: false, isHolding: false, onAddToWatchlist: onAdd });
    expect(screen.getByText("Bygg investeringscaset innan Atlas kan utvärdera portföljpassform.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Lägg till i bevakningslistan för att utvärdera" })).toBeInTheDocument();
  });

  it("shows Open Investment Case (live-verification regression) when a real assessment exists even though isOnWatchlist/isHolding are both false", () => {
    renderFull({ isOnWatchlist: false, isHolding: false, onAddToWatchlist: vi.fn() });
    expect(screen.getByRole("button", { name: "Öppna investeringscase" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Lägg till i bevakningslistan för att utvärdera" })).not.toBeInTheDocument();
  });

  it("still shows the real allocation dimension's own reasoning -- the compact-only boilerplate filter never applied here", () => {
    renderFull({
      assessment: assessment({
        dimensions: [
          {
            kind: "allocation",
            rating: "good",
            reasoning: ["No trade size is available to project a resulting weight; portfolio concentration is currently Low."],
            unavailableReason: null,
          },
        ],
      }),
    });
    expect(screen.getByText(/No trade size is available/)).toBeInTheDocument();
  });

  it("never renders a numeric score anywhere on the card", () => {
    renderFull();
    const numbers = screen.queryAllByText(/^\d+$|^\d+\/\d+$|^\d+%$/);
    expect(numbers).toHaveLength(0);
  });
});
