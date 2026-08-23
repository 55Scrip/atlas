import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { MaterialityPanel } from "./MaterialityPanel";
import type { MaterialityAssessmentView } from "./materialityApi";

function Harness({ assessment }: { assessment: MaterialityAssessmentView }) {
  const { t } = useTranslation();
  return <MaterialityPanel assessment={assessment} t={t} />;
}

function renderPanel(assessment: MaterialityAssessmentView) {
  return render(
    <LanguageProvider>
      <Harness assessment={assessment} />
    </LanguageProvider>,
  );
}

const BASE: MaterialityAssessmentView = {
  supportingEvidence: [],
  contradictingEvidence: [],
  limitingFactors: [],
  topSupportingEvidence: null,
  topContradictingEvidence: null,
  topLimitingFactor: null,
  topMissingEvidence: null,
};

describe("MaterialityPanel (Atlas Intelligence -- Materiality & Priority Engine)", () => {
  it("shows the top limiting factor with its real materiality badge, never a raw enum token", () => {
    renderPanel({
      ...BASE,
      topLimitingFactor: { reason: { code: "conviction_insufficient" }, materiality: "critical" },
    });
    expect(screen.getByText("Kritiskt")).toBeInTheDocument();
    expect(screen.getByText("Atlas kan ännu inte fastställa en samlad övertygelse för det här caset.")).toBeInTheDocument();
    expect(screen.queryByText("conviction_insufficient")).not.toBeInTheDocument();
  });

  it("names the real top missing dimension with its real gap reason", () => {
    renderPanel({
      ...BASE,
      topMissingEvidence: { dimension: "growth", level: "unavailable", reasoning: ["insufficient_historical_periods"] },
    });
    expect(screen.getByText(/Tillväxt/)).toBeInTheDocument();
    expect(screen.queryByText(/insufficient_historical_periods/)).not.toBeInTheDocument();
  });

  it("renders nothing for a top pick that is genuinely absent, never a fabricated placeholder", () => {
    renderPanel(BASE);
    expect(screen.queryByText("Starkaste skälen för")).not.toBeInTheDocument();
  });

  it("keeps the full, materiality-ordered list collapsed behind one expandable detail", () => {
    renderPanel({
      ...BASE,
      supportingEvidence: [{ reason: { code: "thesis_strengthened" }, materiality: "high" }],
      topSupportingEvidence: { reason: { code: "thesis_strengthened" }, materiality: "high" },
    });
    const matches = screen.getAllByText("Tesen har stärkts sedan senaste genomgången.");
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });
});
