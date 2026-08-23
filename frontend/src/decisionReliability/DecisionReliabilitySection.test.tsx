import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { DecisionReliabilitySection } from "./DecisionReliabilitySection";
import type { DecisionReliabilityView, ReliabilityReasonView } from "./decisionReliabilityApi";

function reason(source: ReliabilityReasonView["source"], id: string): ReliabilityReasonView {
  return { source, reference: { kind: "reason_code", id }, count: null, total: null };
}

function reliability(overrides: Partial<DecisionReliabilityView> = {}): DecisionReliabilityView {
  return {
    caseId: "case-1",
    level: "moderate",
    supportingReasons: [],
    limitingReasons: [],
    primaryLimitingReason: null,
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function Wrapper({ reliability: r }: { reliability: DecisionReliabilityView }) {
  const { t } = useTranslation();
  return <DecisionReliabilitySection reliability={r} t={t} />;
}

function renderSection(r: DecisionReliabilityView) {
  return render(
    <LanguageProvider>
      <Wrapper reliability={r} />
    </LanguageProvider>,
  );
}

describe("DecisionReliabilitySection", () => {
  it("shows the translated reliability level badge", () => {
    renderSection(reliability({ level: "high" }));
    expect(screen.getByText("Hög")).toBeInTheDocument();
  });

  it("shows the honest 'no limitation' disclosure when there is none", () => {
    renderSection(reliability());
    expect(screen.getByText("Atlas har för närvarande ingen specifik begränsning att peka på.")).toBeInTheDocument();
  });

  it("shows the primary limiting reason when one exists", () => {
    renderSection(
      reliability({
        primaryLimitingReason: reason("readiness_blocker", "monitoring_pending"),
        limitingReasons: [reason("readiness_blocker", "monitoring_pending")],
      }),
    );
    expect(screen.getByText(/Atlas saknar för närvarande:/)).toBeInTheDocument();
  });

  it("shows the full breakdown with source provenance when expanded", () => {
    const blocker = reason("readiness_blocker", "monitoring_pending");
    renderSection(
      reliability({
        primaryLimitingReason: blocker,
        limitingReasons: [blocker],
        supportingReasons: [reason("evidence_quality", "fresh")],
      }),
    );
    screen.getByText("Visa fullständig tillförlitlighetsbedömning").click();
    expect(screen.getAllByText("Beslutsberedskap").length).toBeGreaterThan(0);
    expect(screen.getByText("Underlagets kvalitet")).toBeInTheDocument();
  });

  it("does not show the expand control when there is nothing more to show", () => {
    renderSection(reliability());
    expect(screen.queryByText("Visa fullständig tillförlitlighetsbedömning")).not.toBeInTheDocument();
  });

  it("never renders raw technical or AI/psychology vocabulary", () => {
    renderSection(reliability());
    expect(screen.queryByText(/\bengine\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bAI\b/)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bpredict/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bprobability\b/i)).not.toBeInTheDocument();
  });
});
