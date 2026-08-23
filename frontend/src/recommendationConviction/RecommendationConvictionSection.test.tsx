import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { RecommendationConvictionSection } from "./RecommendationConvictionSection";
import type { ConvictionChangeView, RecommendationConvictionView } from "./recommendationConvictionApi";

function conviction(overrides: Partial<RecommendationConvictionView> = {}): RecommendationConvictionView {
  return {
    caseId: "case-1",
    action: "hold",
    strength: "moderate",
    stability: "stable",
    supportingReasons: [],
    limitingReasons: [],
    strengtheningTrigger: null,
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function Wrapper({
  conviction: c,
  change,
}: {
  conviction: RecommendationConvictionView;
  change: ConvictionChangeView | null;
}) {
  const { t } = useTranslation();
  return <RecommendationConvictionSection conviction={c} change={change} t={t} />;
}

function renderSection(c: RecommendationConvictionView, change: ConvictionChangeView | null = null) {
  return render(
    <LanguageProvider>
      <Wrapper conviction={c} change={change} />
    </LanguageProvider>,
  );
}

describe("RecommendationConvictionSection", () => {
  it("shows the translated strength badge", () => {
    renderSection(conviction({ strength: "very_strong" }));
    expect(screen.getByText("Mycket starkt")).toBeInTheDocument();
  });

  it("shows the translated stability badge", () => {
    renderSection(conviction({ stability: "fragile" }));
    expect(screen.getByText("Skört")).toBeInTheDocument();
  });

  it("shows the primary supporting reason using the analysis-conviction vocabulary", () => {
    renderSection(
      conviction({
        supportingReasons: [{ source: "analysis_conviction", code: "evidence_coverage_full" }],
      }),
    );
    expect(screen.getAllByText(/Beläggtäckningen är fullständig\./).length).toBeGreaterThan(0);
  });

  it("shows the primary limiting reason using the evidence-graph vocabulary", () => {
    renderSection(
      conviction({
        limitingReasons: [{ source: "evidence_graph", code: "critical_dependency" }],
      }),
    );
    expect(screen.getAllByText(/Flera slutsatser bygger på detta/).length).toBeGreaterThan(0);
  });

  it("shows the strengthening trigger when present", () => {
    renderSection(
      conviction({
        limitingReasons: [{ source: "readiness_blocker", code: "no_data_source" }],
        strengtheningTrigger: { source: "readiness_blocker", code: "no_data_source" },
      }),
    );
    expect(screen.getByText(/Vad som skulle stärka detta/)).toBeInTheDocument();
  });

  it("shows the latest change line when a real change is provided", () => {
    renderSection(conviction({ strength: "strong" }), {
      caseId: "case-1",
      previousStrength: "weak",
      currentStrength: "strong",
      previousStability: "stable",
      currentStability: "stable",
      newLimitingReasons: [],
      resolvedLimitingReasons: [],
      detectedAt: "2026-01-01T00:00:00Z",
    });
    expect(screen.getByText(/Styrkan ändrades från/)).toBeInTheDocument();
  });

  it("never renders raw technical vocabulary", () => {
    renderSection(conviction({ limitingReasons: [{ source: "readiness_blocker", code: "critical_dependency_unresolved" }] }));
    expect(screen.queryByText(/\bengine\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/probability/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/score/i)).not.toBeInTheDocument();
  });
});
