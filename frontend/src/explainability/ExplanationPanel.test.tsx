import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { ExplanationPanel } from "./ExplanationPanel";
import type { ExplanationView } from "./explainabilityApi";

function Harness({ explanation }: { explanation: ExplanationView }) {
  const { t } = useTranslation();
  return <ExplanationPanel explanation={explanation} t={t} />;
}

function renderPanel(explanation: ExplanationView) {
  return render(
    <LanguageProvider>
      <Harness explanation={explanation} />
    </LanguageProvider>,
  );
}

const BASE: ExplanationView = {
  supportingEvidence: [],
  contradictingEvidence: [],
  limitingFactors: [],
  missingEvidence: [],
  confidenceDrivers: [],
  mostValuableMissingInformation: null,
};

describe("ExplanationPanel (Atlas Intelligence Sprint 3)", () => {
  it("shows the honest empty state when nothing is missing, not a blank line", () => {
    renderPanel(BASE);
    expect(
      screen.getByText("Atlas saknar inget underlag som väsentligt skulle förändra den här slutsatsen."),
    ).toBeInTheDocument();
  });

  it("names the single most valuable missing dimension with its real gap reason, never a raw enum token", () => {
    renderPanel({
      ...BASE,
      mostValuableMissingInformation: {
        dimension: "growth",
        level: "unavailable",
        reasoning: ["insufficient_historical_periods"],
      },
    });
    expect(screen.getByText(/Tillväxt/)).toBeInTheDocument();
    expect(screen.queryByText(/insufficient_historical_periods/)).not.toBeInTheDocument();
  });

  it("keeps the rest of the evidence trace collapsed behind one expandable detail", () => {
    renderPanel({
      ...BASE,
      supportingEvidence: [{ code: "thesis_strengthened" }],
    });
    expect(screen.queryByText("Tesen har stärkts sedan senaste genomgången.")).not.toBeVisible();
  });

  it("reuses the real, already-translated stance reason sentence for supporting evidence, never a raw code", () => {
    renderPanel({ ...BASE, supportingEvidence: [{ code: "thesis_strengthened" }] });
    expect(screen.getByText("Tesen har stärkts sedan senaste genomgången.")).toBeInTheDocument();
    expect(screen.queryByText("thesis_strengthened")).not.toBeInTheDocument();
  });

  it("classifies a contradicting-evidence reason and a limiting-factor reason into separate groups", () => {
    renderPanel({
      ...BASE,
      contradictingEvidence: [{ code: "high_risk_present" }],
      limitingFactors: [{ code: "confidence_limited" }],
    });
    expect(screen.getByText("En allvarlig risk föreligger för närvarande.")).toBeInTheDocument();
    expect(screen.getByText("Atlas egen tillförlitlighet i den här analysen är begränsad.")).toBeInTheDocument();
  });

  it("renders the real counted confidence-driver sentence, matching the Coverage panel's own precedent", () => {
    renderPanel({ ...BASE, confidenceDrivers: [{ code: "dimensions_conclusive", count: 2, total: 6 }] });
    expect(screen.getByText("2 av 6 utvärderade dimensioner nådde en verklig slutsats.")).toBeInTheDocument();
  });

  it("shows the honest empty state for each bucket that has no evidence, not a blank list", () => {
    renderPanel(BASE);
    expect(screen.getByText("Atlas har inte identifierat något stödjande underlag ännu.")).toBeInTheDocument();
    expect(screen.getByText("Atlas har inte hittat underlag som motsäger den här slutsatsen.")).toBeInTheDocument();
    expect(screen.getByText("Inget hindrar för närvarande Atlas från att nå en tydlig syn.")).toBeInTheDocument();
  });
});
