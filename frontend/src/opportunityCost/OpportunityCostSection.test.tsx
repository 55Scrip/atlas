import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { OpportunityCostSection } from "./OpportunityCostSection";
import type {
  AlternativeComparisonView,
  DecisionAlternativeView,
  DecisionTradeoffView,
  OpportunityCostChangeView,
  OpportunityCostView,
} from "./opportunityCostApi";
import type { RecommendationConvictionView } from "../recommendationConviction/recommendationConvictionApi";
import type { DecisionPathView } from "../decisionPath/decisionPathApi";

function conviction(caseId: string): RecommendationConvictionView {
  return {
    caseId,
    action: "hold",
    strength: "moderate",
    stability: "stable",
    supportingReasons: [],
    limitingReasons: [],
    strengtheningTrigger: null,
    generatedAt: "2026-01-01T00:00:00Z",
  };
}

function path(caseId: string): DecisionPathView {
  return {
    caseId,
    currentAction: "hold",
    currentStrength: "moderate",
    steps: [],
    immediateBlocker: null,
    nextAchievableImprovement: null,
    finalReachableState: "already_reached",
    generatedAt: "2026-01-01T00:00:00Z",
  };
}

function comparison(overrides: Partial<AlternativeComparisonView> = {}): AlternativeComparisonView {
  return {
    conviction: { a: conviction("current"), b: conviction("other"), strongerCaseId: "other", moreEvidenceLimitedCaseId: null, moreOperationallyBlockedCaseId: null, moreStableCaseId: null },
    path: { a: path("current"), b: path("other"), shorterPathCaseId: null, fewerRemainingBlockersCaseId: null, moreOperationallyDependentCaseId: null, moreEvidenceDependentCaseId: null },
    moreDependencyBlockedCaseId: null,
    ...overrides,
  };
}

function alternative(overrides: Partial<DecisionAlternativeView> = {}): DecisionAlternativeView {
  return {
    kind: "wait",
    caseId: null,
    ticker: null,
    action: null,
    strength: null,
    reason: { source: "stance", code: "decision_support_favorable" },
    ...overrides,
  };
}

function opportunityCost(tradeoffs: DecisionTradeoffView[]): OpportunityCostView {
  return { caseId: "current", currentAction: "hold", tradeoffs, generatedAt: "2026-01-01T00:00:00Z" };
}

function Wrapper({
  oc,
  currentTicker,
  change,
}: {
  oc: OpportunityCostView;
  currentTicker: string;
  change: OpportunityCostChangeView | null;
}) {
  const { t } = useTranslation();
  return <OpportunityCostSection opportunityCost={oc} currentTicker={currentTicker} change={change} t={t} />;
}

function renderSection(oc: OpportunityCostView, currentTicker = "AAPL", change: OpportunityCostChangeView | null = null) {
  return render(
    <LanguageProvider>
      <Wrapper oc={oc} currentTicker={currentTicker} change={change} />
    </LanguageProvider>,
  );
}

describe("OpportunityCostSection", () => {
  it("renders nothing when there are no real alternatives", () => {
    const { container } = renderSection(opportunityCost([]));
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the translated alternative kind and reason", () => {
    renderSection(
      opportunityCost([{ alternative: alternative({ kind: "open_new_position", ticker: "NVDA", caseId: "o1" }), comparison: null }]),
    );
    expect(screen.getByText("Öppna ny position")).toBeInTheDocument();
    expect(screen.getByText("NVDA")).toBeInTheDocument();
    expect(screen.getByText("Det nuvarande underlaget talar för den här positionen.")).toBeInTheDocument();
  });

  it("always shows the fixed disclosure that Atlas never chooses for the investor", () => {
    renderSection(opportunityCost([{ alternative: alternative(), comparison: null }]));
    expect(screen.getByText(/Atlas väljer aldrig mellan dem åt dig\./)).toBeInTheDocument();
  });

  it("shows the comparison detail with the correct ticker for the stronger side", () => {
    renderSection(
      opportunityCost([
        {
          alternative: alternative({ kind: "open_new_position", ticker: "NVDA", caseId: "other" }),
          comparison: comparison({
            conviction: {
              a: conviction("current"),
              b: conviction("other"),
              strongerCaseId: "current",
              moreEvidenceLimitedCaseId: null,
              moreOperationallyBlockedCaseId: null,
              moreStableCaseId: null,
            },
          }),
        },
      ]),
      "AAPL",
    );
    expect(screen.getByText(/Visa fullständig jämförelse/)).toBeInTheDocument();
  });

  it("never renders raw technical or winner/ranking vocabulary", () => {
    renderSection(opportunityCost([{ alternative: alternative(), comparison: null }]));
    expect(screen.queryByText(/\bengine\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bwinner\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\brank\b/i)).not.toBeInTheDocument();
  });
});
