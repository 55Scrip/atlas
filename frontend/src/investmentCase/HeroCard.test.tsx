import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider } from "../i18n";
import { HeroCard, type HeroAnalysisInput } from "./HeroCard";

function analysis(overrides: Partial<HeroAnalysisInput> = {}): HeroAnalysisInput {
  return {
    recommendationLevel: "reduction_supported",
    convictionLevel: "moderate",
    growthStatus: "moderate",
    capitalAllocationStatus: "moderate",
    valuationStatus: "fairly_valued",
    riskFindings: [],
    topStrengthKind: null,
    isBaselineCase: false,
    latestChangeCount: 0,
    currentAnalysisAt: "2026-01-01T00:00:00Z",
    longTermExpectedReturn: { lowPercent: 5, highPercent: 20 },
    longTermExpectedReturnGap: null,
    longTermBullReturnPercent: 20,
    longTermBearReturnPercent: 5,
    outlookAlignmentLongTerm: "corroborates",
    valuationSupportStatus: "insufficient_input",
    limitingFactors: [{ kind: "valuationGap", gap: "insufficient_historical_valuation_data" }],
    missingEvaluations: [],
    sharePrice: 100,
    currency: "USD",
    tradingDay: "2026-08-21",
    priceFreshness: "fresh",
    stance: null,
    ...overrides,
  };
}

function renderHero(props: Partial<Parameters<typeof HeroCard>[0]> = {}) {
  return render(
    <LanguageProvider>
      <HeroCard
        ticker="AAPL"
        analysis={analysis()}
        outstandingWorkKinds={[]}
        isThesisStale={false}
        openQuestionCount={0}
        t={(key) => key as unknown as string}
        locale="sv-SE"
        {...props}
      />
    </LanguageProvider>,
  );
}

describe("HeroCard", () => {
  it("shows the compact limiting-factor preview line by default (real value on Company Workspace, which renders this Hero standalone)", () => {
    renderHero();
    expect(screen.getByText(/investmentCase.hero.limitedByPrefix/)).toBeInTheDocument();
  });

  it("omits the preview line when suppressLimitingFactorPreview is set (Internal Alpha Stabilization: Investment Case shows the fuller detail immediately below this same card)", () => {
    renderHero({ suppressLimitingFactorPreview: true });
    expect(screen.queryByText(/investmentCase.hero.limitedByPrefix/)).not.toBeInTheDocument();
  });

  it("never shows the preview line when there are no real limiting factors, suppressed or not", () => {
    renderHero({ analysis: analysis({ limitingFactors: [] }) });
    expect(screen.queryByText(/investmentCase.hero.limitedByPrefix/)).not.toBeInTheDocument();
  });

  describe("Stance (Atlas Intelligence Sprint 2)", () => {
    it("shows no Stance block at all when stance is null, never a placeholder", () => {
      renderHero({ analysis: analysis({ stance: null }) });
      expect(screen.queryByText("stance.heading")).not.toBeInTheDocument();
    });

    it("shows the level badge and the primary reason when a real Stance is present", () => {
      renderHero({
        analysis: analysis({
          stance: {
            level: "maintain",
            reasoning: [{ code: "thesis_unchanged" }],
            supportingSignals: [],
            limitingSignals: [],
            confidence: "high",
            missingInformation: [],
          },
        }),
      });
      expect(screen.getByText("stance.level.maintain")).toBeInTheDocument();
      expect(screen.getByText(/stance.reason.thesisUnchanged/)).toBeInTheDocument();
    });

    it("shows a cautionary line only when a real limiting signal exists alongside a real direction", () => {
      renderHero({
        analysis: analysis({
          stance: {
            level: "increase",
            reasoning: [{ code: "thesis_strengthened" }, { code: "portfolio_fit_weak" }],
            supportingSignals: [{ code: "thesis_strengthened" }],
            limitingSignals: [{ code: "portfolio_fit_weak" }],
            confidence: "high",
            missingInformation: [],
          },
        }),
      });
      expect(screen.getByText(/stance.reason.thesisStrengthened/)).toBeInTheDocument();
      expect(screen.getByText(/stance.reason.portfolioFitWeak/)).toBeInTheDocument();
    });

    it("never shows a cautionary line for a gated level (the primary reason already explains it)", () => {
      renderHero({
        analysis: analysis({
          stance: {
            level: "wait",
            reasoning: [{ code: "confidence_limited" }],
            supportingSignals: [],
            limitingSignals: [{ code: "confidence_limited" }],
            confidence: "limited",
            missingInformation: [],
          },
        }),
      });
      const reasonMatches = screen.getAllByText(/stance.reason.confidenceLimited/);
      expect(reasonMatches).toHaveLength(1);
    });

    it("shows missing information when present", () => {
      renderHero({
        analysis: analysis({
          stance: {
            level: "wait",
            reasoning: [{ code: "confidence_very_limited" }],
            supportingSignals: [],
            limitingSignals: [{ code: "confidence_very_limited" }],
            confidence: "very_limited",
            missingInformation: ["growth", "fcf_yield_relative"],
          },
        }),
      });
      expect(screen.getByText(/stance.missingInformationLabel/)).toBeInTheDocument();
    });
  });

  describe("Price freshness (Internal Alpha Stabilization 1 -- MSFT price root cause fix)", () => {
    it("shows the updated-date caption but no badge and no button when fresh", () => {
      renderHero({ analysis: analysis({ priceFreshness: "fresh", tradingDay: "2026-08-21" }) });
      expect(screen.getByText(/investmentCase.keyMetrics.priceUpdatedLabel/)).toBeInTheDocument();
      expect(screen.queryByText("investmentCase.keyMetrics.priceStale")).not.toBeInTheDocument();
      expect(screen.queryByText("investmentCase.keyMetrics.priceRefreshing")).not.toBeInTheDocument();
      expect(screen.queryByText("investmentCase.keyMetrics.priceRefreshFailed")).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "investmentCase.keyMetrics.priceRefreshButton" })).not.toBeInTheDocument();
    });

    it("shows a stale badge and an enabled Refresh button when stale", () => {
      renderHero({ analysis: analysis({ priceFreshness: "stale" }), onRefreshPrice: () => {} });
      expect(screen.getByText("investmentCase.keyMetrics.priceStale")).toBeInTheDocument();
      const button = screen.getByRole("button", { name: "investmentCase.keyMetrics.priceRefreshButton" });
      expect(button).not.toBeDisabled();
    });

    it("shows a refreshing badge and a disabled button while a refresh is in flight", () => {
      renderHero({ analysis: analysis({ priceFreshness: "refreshing" }), onRefreshPrice: () => {} });
      // Both the badge and the button legitimately show the identical
      // "Uppdaterar…" text while refreshing -- two real occurrences,
      // not a duplicate-rendering bug.
      expect(screen.getAllByText("investmentCase.keyMetrics.priceRefreshing")).toHaveLength(2);
      const button = screen.getByRole("button", { name: "investmentCase.keyMetrics.priceRefreshing" });
      expect(button).toBeDisabled();
    });

    it("also disables the button via the local isRefreshingPrice flag, even if the server-reported status has not caught up yet", () => {
      renderHero({ analysis: analysis({ priceFreshness: "stale" }), onRefreshPrice: () => {}, isRefreshingPrice: true });
      const button = screen.getByRole("button", { name: "investmentCase.keyMetrics.priceRefreshing" });
      expect(button).toBeDisabled();
    });

    it("shows a failed badge, distinct from plain stale, when the last refresh attempt failed", () => {
      renderHero({ analysis: analysis({ priceFreshness: "failed" }), onRefreshPrice: () => {} });
      expect(screen.getByText("investmentCase.keyMetrics.priceRefreshFailed")).toBeInTheDocument();
      expect(screen.queryByText("investmentCase.keyMetrics.priceStale")).not.toBeInTheDocument();
    });

    it("shows no refresh button at all when no onRefreshPrice handler is supplied (e.g. Company Workspace's own reuse of this card)", () => {
      renderHero({ analysis: analysis({ priceFreshness: "stale" }) });
      expect(screen.queryByRole("button", { name: /priceRefresh/ })).not.toBeInTheDocument();
    });

    it("shows no button and no badge for an unavailable price, only when priceFreshness is genuinely omitted (older caller shape)", () => {
      const { priceFreshness: _omit, tradingDay: _omitDay, ...rest } = analysis();
      renderHero({ analysis: rest as HeroAnalysisInput, onRefreshPrice: () => {} });
      expect(screen.queryByText("investmentCase.keyMetrics.priceStale")).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /priceRefresh/ })).not.toBeInTheDocument();
    });
  });

  describe("No provider data found (Import Robustness, Internal Alpha Stabilization 1)", () => {
    it("shows the honest 'no provider data' message instead of the generic withheld sentence when withheld and noProviderDataFound is true", () => {
      renderHero({
        analysis: analysis({ recommendationLevel: "insufficient_evidence", noProviderDataFound: true }),
      });
      expect(screen.getByText("investmentCase.hero.noProviderData")).toBeInTheDocument();
      expect(screen.queryByText(/investmentCase.hero.withheld.opening/)).not.toBeInTheDocument();
    });

    it("shows the ordinary generic withheld sentence, unchanged, when withheld but noProviderDataFound is false", () => {
      renderHero({
        analysis: analysis({ recommendationLevel: "insufficient_evidence", noProviderDataFound: false }),
      });
      expect(screen.getByText(/investmentCase.hero.withheld.opening/)).toBeInTheDocument();
      expect(screen.queryByText("investmentCase.hero.noProviderData")).not.toBeInTheDocument();
    });

    it("shows the ordinary generic withheld sentence, unchanged, when withheld and noProviderDataFound is omitted (older caller shape, e.g. a build not yet passing this field)", () => {
      const { noProviderDataFound: _omit, ...rest } = analysis({ recommendationLevel: "insufficient_evidence" });
      renderHero({ analysis: rest as HeroAnalysisInput });
      expect(screen.getByText(/investmentCase.hero.withheld.opening/)).toBeInTheDocument();
      expect(screen.queryByText("investmentCase.hero.noProviderData")).not.toBeInTheDocument();
    });

    it("never shows the no-provider-data message outside the withheld branch, even if noProviderDataFound were somehow true", () => {
      renderHero({
        analysis: analysis({ recommendationLevel: "reduction_supported", noProviderDataFound: true }),
      });
      expect(screen.queryByText("investmentCase.hero.noProviderData")).not.toBeInTheDocument();
    });
  });

  describe("Neutral vs. insufficient business tension (Status/Explanation Language stabilization)", () => {
    it("a genuinely moderate business signal (the default fixture: both dimensions 'moderate') shows the neutral sentence, not the insufficient-evidence one", () => {
      renderHero();
      expect(screen.getByText(/investmentCase\.hero\.why\.neutral/)).toBeInTheDocument();
      expect(screen.queryByText(/investmentCase\.hero\.why\.insufficient/)).not.toBeInTheDocument();
    });

    it("truly missing business data (both dimensions insufficient_input) still shows the insufficient-evidence sentence, unchanged", () => {
      renderHero({
        analysis: analysis({ growthStatus: "insufficient_input", capitalAllocationStatus: "insufficient_input" }),
      });
      expect(screen.getByText(/investmentCase\.hero\.why\.insufficient/)).toBeInTheDocument();
      expect(screen.queryByText(/investmentCase\.hero\.why\.neutral/)).not.toBeInTheDocument();
    });
  });
});
