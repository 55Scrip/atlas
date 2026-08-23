import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { DecisionReadinessSection } from "./DecisionReadinessSection";
import type { DecisionReadinessChangeView, DecisionReadinessView } from "./decisionReadinessApi";

function readiness(overrides: Partial<DecisionReadinessView> = {}): DecisionReadinessView {
  return {
    caseId: "case-1",
    status: "ready",
    blockers: [],
    supportingReasons: [{ kind: "substantial_coverage_reached", detail: null }],
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function Wrapper({ readiness: r, change }: { readiness: DecisionReadinessView; change: DecisionReadinessChangeView | null }) {
  const { t } = useTranslation();
  return <DecisionReadinessSection readiness={r} change={change} t={t} />;
}

function renderSection(r: DecisionReadinessView, change: DecisionReadinessChangeView | null = null) {
  return render(
    <LanguageProvider>
      <Wrapper readiness={r} change={change} />
    </LanguageProvider>,
  );
}

describe("DecisionReadinessSection", () => {
  it("shows the translated status badge", () => {
    renderSection(readiness({ status: "blocked" }));
    expect(screen.getByText("Beslut blockerat")).toBeInTheDocument();
  });

  it("explains readiness using the primary blocker when blocked", () => {
    renderSection(
      readiness({
        status: "blocked",
        blockers: [{ kind: "conflicting_evidence", detail: null }],
        supportingReasons: [],
      }),
    );
    expect(
      screen.getByText("Atlas kan ännu inte motivera ett beslut eftersom Underlaget motsäger sig på minst en punkt."),
    ).toBeInTheDocument();
  });

  it("explains readiness using the primary supporting reason when ready", () => {
    renderSection(readiness({ status: "ready", supportingReasons: [{ kind: "confidence_established", detail: null }] }));
    expect(screen.getByText("Atlas är redo eftersom Atlas förståelse är väl underbyggd.")).toBeInTheDocument();
  });

  it("shows the latest change line when a real change is provided", () => {
    renderSection(readiness({ status: "ready" }), {
      caseId: "case-1",
      previousStatus: "waiting",
      currentStatus: "ready",
      newBlockers: [],
      resolvedBlockers: ["monitoring_pending"],
      detectedAt: "2026-01-01T00:00:00Z",
    });
    expect(screen.getByText(/Beredskapen ändrades från/)).toBeInTheDocument();
  });

  it("never renders raw technical vocabulary", () => {
    renderSection(readiness({ status: "blocked", blockers: [{ kind: "critical_dependency_unresolved", detail: null }] }));
    expect(screen.queryByText(/\bengine\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/decision engine/i)).not.toBeInTheDocument();
  });
});
