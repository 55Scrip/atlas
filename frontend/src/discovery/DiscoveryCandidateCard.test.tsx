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
      <DiscoveryCandidateCard
        ticker="NVDA"
        reasonKey="discovery.card.reason.watchlist"
        assessment={assessment()}
        isOnWatchlist={true}
        isHolding={false}
        onOpenCase={vi.fn()}
        {...props}
      />
    </LanguageProvider>,
  );
}

describe("DiscoveryCandidateCard", () => {
  it("renders the ticker and overall Fit badge", () => {
    renderCard();
    expect(screen.getByText("NVDA")).toBeInTheDocument();
    expect(screen.getByText("Bra passform")).toBeInTheDocument();
  });

  it("shows a coverage-confidence badge distinct from the Fit badge (Atlas Intelligence Sprint 1, Deliverable 7)", () => {
    renderCard({ assessment: assessment({ coverage: { ...EMPTY_COVERAGE, overallConfidence: "high" } }) });
    expect(screen.getByText("Hög tillförlitlighet")).toBeInTheDocument();
    expect(screen.getByText("Bra passform")).toBeInTheDocument();
  });

  it("shows no coverage badge at all when no assessment exists yet, never a fabricated one", () => {
    renderCard({ assessment: null, isOnWatchlist: true });
    expect(screen.queryByText(/tillförlitlighet/)).not.toBeInTheDocument();
  });

  describe("Stance (Atlas Intelligence Sprint 2, Deliverable 7)", () => {
    it("shows the Stance badge as the leftmost, most prominent badge when present", () => {
      renderCard({
        assessment: assessment(),
        stance: {
          level: "review",
          reasoning: [{ code: "portfolio_fit_weak" }],
          supportingSignals: [],
          limitingSignals: [{ code: "portfolio_fit_weak" }],
          confidence: "high",
          missingInformation: [],
        },
      });
      expect(screen.getByText("Värt att se över")).toBeInTheDocument();
    });

    it("shows no Stance badge at all when none exists yet, never a fabricated one", () => {
      renderCard({ assessment: assessment(), stance: null });
      expect(screen.queryByText(/Genomgång krävs|Synen/)).not.toBeInTheDocument();
    });

    it("never shows increase/reduce alongside share-count or trade wording anywhere on the card", () => {
      renderCard({
        assessment: assessment(),
        stance: {
          level: "increase",
          reasoning: [{ code: "thesis_strengthened" }],
          supportingSignals: [{ code: "thesis_strengthened" }],
          limitingSignals: [],
          confidence: "high",
          missingInformation: [],
        },
      });
      expect(screen.getByText("Synen har stärkts")).toBeInTheDocument();
      expect(screen.queryByText(/köp|sälj|aktier/i)).not.toBeInTheDocument();
    });
  });

  it("shows a disclosed gap, not a fabricated rating, when no assessment exists yet", () => {
    renderCard({ assessment: null, isOnWatchlist: true });
    expect(screen.getByText("Atlas kan utvärdera portföljpassform när detta bolags investeringscase finns.")).toBeInTheDocument();
  });

  it("shows the no-Case message and an Add-to-Watchlist action for a candidate with neither a Case nor a Watchlist entry", () => {
    const onAdd = vi.fn();
    renderCard({ assessment: null, isOnWatchlist: false, isHolding: false, onAddToWatchlist: onAdd });
    expect(screen.getByText("Bygg investeringscaset innan Atlas kan utvärdera portföljpassform.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Lägg till i bevakningslistan för att utvärdera" })).toBeInTheDocument();
  });

  it("shows Open Investment Case (live-verification regression) when a real assessment exists even though isOnWatchlist/isHolding are both false", () => {
    // A Case can be resolvable (e.g. via a ticker previously
    // watchlisted then removed) without the ticker currently being a
    // Portfolio holding or Watchlist entry -- `assessment !== null` is
    // the authoritative "can Atlas evaluate this" signal, checked
    // before the two narrower membership flags.
    renderCard({ isOnWatchlist: false, isHolding: false, onAddToWatchlist: vi.fn() });
    expect(screen.getByRole("button", { name: "Öppna investeringscase" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Lägg till i bevakningslistan för att utvärdera" })).not.toBeInTheDocument();
  });

  it("calls onAddToWatchlist when that action is clicked", async () => {
    const onAdd = vi.fn();
    const user = userEvent.setup();
    renderCard({ assessment: null, isOnWatchlist: false, isHolding: false, onAddToWatchlist: onAdd });
    await user.click(screen.getByRole("button", { name: "Lägg till i bevakningslistan för att utvärdera" }));
    expect(onAdd).toHaveBeenCalledTimes(1);
  });

  it("calls onOpenCase when Open Investment Case is clicked for an evaluable candidate", async () => {
    const onOpen = vi.fn();
    const user = userEvent.setup();
    renderCard({ onOpenCase: onOpen });
    await user.click(screen.getByRole("button", { name: "Öppna investeringscase" }));
    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it("shows a Remove-from-Watchlist action only when isOnWatchlist and the callback are both provided", () => {
    const { rerender } = renderCard({ isOnWatchlist: true, onRemoveFromWatchlist: vi.fn() });
    expect(screen.getByRole("button", { name: "Ta bort från bevakningslistan" })).toBeInTheDocument();

    rerender(
      <LanguageProvider>
        <DiscoveryCandidateCard
          ticker="NVDA"
          reasonKey="discovery.card.reason.watchlist"
          assessment={assessment()}
          isOnWatchlist={false}
          isHolding={false}
          onOpenCase={vi.fn()}
        />
      </LanguageProvider>,
    );
    expect(screen.queryByRole("button", { name: "Ta bort från bevakningslistan" })).not.toBeInTheDocument();
  });

  it("renders full-variant strongest positives and limitations grouped from the shared dimension-grouping rule", () => {
    renderCard({ variant: "full" });
    expect(screen.getByText("Varför det passar")).toBeInTheDocument();
    expect(screen.getByText("4 of 6 categories rated Strong.")).toBeInTheDocument();
    expect(screen.getByText("Vad som talar emot")).toBeInTheDocument();
    expect(screen.getByText("High financial risk.")).toBeInTheDocument();
  });

  it("shows the real Daily Brief Agenda headline as the primary reason when one exists, alongside (not replacing) the generic membership category", () => {
    renderCard({ agendaHeadline: "NVDA: Portfolio Fit is improving" });
    expect(screen.getByText("NVDA: Portfolio Fit is improving")).toBeInTheDocument();
    expect(screen.getByText("På din bevakningslista")).toBeInTheDocument();
  });

  it("shows only the generic membership category when no Agenda headline exists, never a fabricated reason", () => {
    renderCard();
    expect(screen.getByText("På din bevakningslista")).toBeInTheDocument();
  });

  it("never renders a numeric score anywhere on the card", () => {
    renderCard({ variant: "full" });
    const numbers = screen.queryAllByText(/^\d+$|^\d+\/\d+$|^\d+%$/);
    expect(numbers).toHaveLength(0);
  });

  describe("Stance/Fit tension bridging (Atlas UX Phase 7B, Phase 3)", () => {
    function stanceView(level: "avoid_decision" | "increase") {
      return {
        level,
        reasoning: [{ code: "portfolio_fit_weak" as const }],
        supportingSignals: [],
        limitingSignals: [],
        confidence: "high" as const,
        missingInformation: [],
      };
    }

    it("explains a real Stance/Fit disagreement instead of leaving two opposing badges unexplained (confirmed live: 'Red flag found' next to 'Good Fit')", () => {
      renderCard({ assessment: assessment({ overall: "good" }), stance: stanceView("avoid_decision") });
      expect(screen.getByText("Röd flagga hittad")).toBeInTheDocument();
      expect(screen.getByText("Bra passform")).toBeInTheDocument();
      expect(
        screen.getByText("Det här gäller enbart portföljpassformen — Atlas flaggade separat en oro i själva bolaget."),
      ).toBeInTheDocument();
    });

    it("explains the opposite disagreement too -- a strengthened view but a poor portfolio fit", () => {
      renderCard({ assessment: assessment({ overall: "poor" }), stance: stanceView("increase") });
      expect(screen.getByText("Atlas syn på bolaget har stärkts, men det skulle passa din portfölj dåligt.")).toBeInTheDocument();
    });

    it("never shows a bridging sentence when Stance and Fit are simply neutral/compatible, not genuinely opposed", () => {
      renderCard({ assessment: assessment({ overall: "neutral" }), stance: stanceView("increase") });
      expect(screen.queryByText(/gäller enbart portföljpassformen|skulle passa din portfölj dåligt/)).not.toBeInTheDocument();
    });

    it("never shows a bridging sentence when either Stance or Fit is missing", () => {
      renderCard({ assessment: null, stance: stanceView("avoid_decision") });
      expect(screen.queryByText(/gäller enbart portföljpassformen|skulle passa din portfölj dåligt/)).not.toBeInTheDocument();
    });
  });

  it("filters the generic 'no trade size available' allocation boilerplate out of the compact preview, so it doesn't repeat identically on nearly every card (Atlas UX Phase 7B, Phase 2)", () => {
    renderCard({
      variant: "compact",
      assessment: assessment({
        dimensions: [
          {
            kind: "allocation",
            rating: "good",
            reasoning: ["No trade size is available to project a resulting weight; portfolio concentration is currently Low."],
            unavailableReason: null,
          },
          { kind: "business", rating: "weak", reasoning: ["Thin margins versus peers."], unavailableReason: null },
        ],
      }),
    });
    expect(screen.queryByText(/No trade size is available/)).not.toBeInTheDocument();
    expect(screen.getByText(/Thin margins versus peers\./)).toBeInTheDocument();
  });

  it("still shows the real allocation dimension in the full detail view -- the boilerplate filter only applies to the short compact preview", () => {
    renderCard({
      variant: "full",
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
});
