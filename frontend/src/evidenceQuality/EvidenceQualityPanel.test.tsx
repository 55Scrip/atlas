import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { EvidenceQualityPanel } from "./EvidenceQualityPanel";
import type { EvidenceQualityReportView } from "./evidenceQualityApi";

function Harness({ report }: { report: EvidenceQualityReportView }) {
  const { t } = useTranslation();
  return <EvidenceQualityPanel report={report} t={t} />;
}

function renderPanel(report: EvidenceQualityReportView) {
  return render(
    <LanguageProvider>
      <Harness report={report} />
    </LanguageProvider>,
  );
}

const BASE: EvidenceQualityReportView = {
  quality: "not_applicable",
  conflictStatus: "not_applicable",
  freshness: "not_applicable",
  dominance: "not_applicable",
  warnings: [],
  facts: [],
  conflicts: [],
  unsupportedFindings: [],
};

describe("EvidenceQualityPanel (Atlas Intelligence Sprint 4)", () => {
  it("shows the overall quality badge with its real translated label", () => {
    renderPanel({ ...BASE, quality: "conflicting", conflictStatus: "conflicting" });
    expect(screen.getAllByText("Motstridigt").length).toBeGreaterThan(0);
  });

  it("shows the fresh quality badge with its real translated label", () => {
    renderPanel({ ...BASE, quality: "fresh" });
    expect(screen.getByText("Färskt")).toBeInTheDocument();
  });

  it("renders the real, already-translated warning sentence, never a raw code", () => {
    renderPanel({ ...BASE, warnings: ["conflicting_source_values"] });
    expect(screen.getByText("Atlas hittade källor som motsäger varandra.")).toBeInTheDocument();
    expect(screen.queryByText("conflicting_source_values")).not.toBeInTheDocument();
  });

  it("names the real disagreeing fact kind and period in a conflict sentence, never a raw enum token", () => {
    renderPanel({
      ...BASE,
      conflicts: [{ factKind: "free_cash_flow", period: "2024-12-31", unit: "usd", values: [100, 120], sourceRecordIds: ["a", "b"] }],
    });
    expect(screen.getByText(/Free cash flow/)).toBeInTheDocument();
    expect(screen.getByText(/2024-12-31/)).toBeInTheDocument();
  });

  it("shows the honest empty state for each bucket that has nothing to report", () => {
    renderPanel(BASE);
    expect(screen.getByText("Atlas har inget bedömt underlag för det här caset ännu.")).toBeInTheDocument();
    expect(screen.getByText("Atlas hittade ingen motsägelse i underlaget för det här caset.")).toBeInTheDocument();
    expect(screen.getByText("Varje verklig slutsats i det här caset pekar på verkligt stödjande underlag.")).toBeInTheDocument();
  });

  it("labels an unsupported finding using the shared dimension vocabulary, never a raw category token", () => {
    renderPanel({ ...BASE, unsupportedFindings: [{ category: "growth", status: "strong" }] });
    expect(screen.getByText("Tillväxt")).toBeInTheDocument();
  });
});
