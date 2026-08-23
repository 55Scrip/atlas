import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { DecisionPathSection } from "./DecisionPathSection";
import type { DecisionPathChangeView, DecisionPathView, DecisionStepView } from "./decisionPathApi";

function step(overrides: Partial<DecisionStepView> = {}): DecisionStepView {
  return { source: "readiness_blocker", code: "no_data_source", progressKind: "operational", reachability: "not_reachable", ...overrides };
}

function path(overrides: Partial<DecisionPathView> = {}): DecisionPathView {
  return {
    caseId: "case-1",
    currentAction: "hold",
    currentStrength: "moderate",
    steps: [],
    immediateBlocker: null,
    nextAchievableImprovement: null,
    finalReachableState: "already_reached",
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function Wrapper({ path: p, change }: { path: DecisionPathView; change: DecisionPathChangeView | null }) {
  const { t } = useTranslation();
  return <DecisionPathSection path={p} change={change} t={t} />;
}

function renderSection(p: DecisionPathView, change: DecisionPathChangeView | null = null) {
  return render(
    <LanguageProvider>
      <Wrapper path={p} change={change} />
    </LanguageProvider>,
  );
}

describe("DecisionPathSection", () => {
  it("shows the translated final-state badge", () => {
    renderSection(path({ finalReachableState: "fully_reachable" }));
    expect(screen.getByText("Varje återstående steg har en verklig väg framåt")).toBeInTheDocument();
  });

  it("shows the immediate blocker using the readiness blocker vocabulary", () => {
    const blocker = step({ source: "readiness_blocker", code: "no_data_source", progressKind: "operational", reachability: "not_reachable" });
    renderSection(path({ steps: [blocker], immediateBlocker: blocker, finalReachableState: "not_reachable" }));
    expect(screen.getAllByText(/Ingen datakälla är tillgänglig just nu\./).length).toBeGreaterThan(0);
  });

  it("shows the next achievable improvement using outstanding-requirement phrasing, never achieved-state phrasing", () => {
    const improvement = step({ source: "readiness_progress", code: "confidence_established", progressKind: "readiness", reachability: "reachable" });
    renderSection(path({ steps: [improvement], nextAchievableImprovement: improvement, finalReachableState: "fully_reachable" }));
    expect(screen.getByText(/Nästa möjliga förbättring/)).toBeInTheDocument();
    expect(screen.getAllByText(/Atlas egen tillförlitlighet i den här analysen är ännu inte fastställd\./).length).toBeGreaterThan(0);
    expect(screen.queryByText(/väl underbyggd/i)).not.toBeInTheDocument();
  });

  it("shows the latest change line when a real change is provided", () => {
    renderSection(path({ finalReachableState: "already_reached" }), {
      caseId: "case-1",
      previousFinalReachableState: "fully_reachable",
      currentFinalReachableState: "already_reached",
      resolvedSteps: [],
      newSteps: [],
      detectedAt: "2026-01-01T00:00:00Z",
    });
    expect(screen.getByText(/Beslutsvägen ändrades från/)).toBeInTheDocument();
  });

  it("never renders raw technical vocabulary", () => {
    const blocker = step();
    renderSection(path({ steps: [blocker], immediateBlocker: blocker, finalReachableState: "not_reachable" }));
    expect(screen.queryByText(/\bengine\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/probability/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/improve valuation/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/increase confidence/i)).not.toBeInTheDocument();
  });
});
