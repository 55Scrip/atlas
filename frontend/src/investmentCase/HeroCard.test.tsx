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
});
