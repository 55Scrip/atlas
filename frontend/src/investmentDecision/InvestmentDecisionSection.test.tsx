import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { InvestmentDecisionSection } from "./InvestmentDecisionSection";
import type { DecisionChangeView, InvestmentDecisionView } from "./investmentDecisionApi";

function decision(overrides: Partial<InvestmentDecisionView> = {}): InvestmentDecisionView {
  return {
    caseId: "case-1",
    action: "hold",
    qualifiers: [],
    supportingReasons: [],
    blockers: [],
    changeTrigger: null,
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function Wrapper({ decision: d, change }: { decision: InvestmentDecisionView; change: DecisionChangeView | null }) {
  const { t } = useTranslation();
  return <InvestmentDecisionSection decision={d} change={change} t={t} />;
}

function renderSection(d: InvestmentDecisionView, change: DecisionChangeView | null = null) {
  return render(
    <LanguageProvider>
      <Wrapper decision={d} change={change} />
    </LanguageProvider>,
  );
}

describe("InvestmentDecisionSection", () => {
  it("shows the translated action badge", () => {
    renderSection(decision({ action: "buy" }));
    expect(screen.getByText("Köp")).toBeInTheDocument();
  });

  it("shows a qualifier badge when one is present", () => {
    renderSection(decision({ action: "hold", qualifiers: [{ kind: "decision_blocked" }] }));
    expect(screen.getByText("Beslut blockerat")).toBeInTheDocument();
  });

  it("shows the primary supporting reason using the readiness reason vocabulary", () => {
    renderSection(
      decision({
        supportingReasons: [{ source: "readiness_support", code: "substantial_coverage_reached" }],
      }),
    );
    expect(screen.getAllByText(/Atlas har analyserat det här bolaget grundligt\./).length).toBeGreaterThan(0);
  });

  it("shows the primary blocker using the readiness blocker vocabulary", () => {
    renderSection(
      decision({
        blockers: [{ source: "readiness_blocker", code: "conflicting_evidence" }],
      }),
    );
    expect(screen.getAllByText(/Underlaget motsäger sig på minst en punkt\./).length).toBeGreaterThan(0);
  });

  it("shows the latest change line when a real change is provided", () => {
    renderSection(decision({ action: "add" }), {
      caseId: "case-1",
      previousAction: "hold",
      currentAction: "add",
      previousQualifierKinds: [],
      currentQualifierKinds: [],
      detectedAt: "2026-01-01T00:00:00Z",
    });
    expect(screen.getByText(/Rekommendationen ändrades från/)).toBeInTheDocument();
  });

  it("never renders raw technical vocabulary", () => {
    renderSection(decision({ blockers: [{ source: "readiness_blocker", code: "critical_dependency_unresolved" }] }));
    expect(screen.queryByText(/\bengine\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/decision engine/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/score/i)).not.toBeInTheDocument();
  });
});
