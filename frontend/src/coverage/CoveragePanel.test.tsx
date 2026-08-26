import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { CoveragePanel } from "./CoveragePanel";
import type { CoverageAssessmentView } from "./coverageApi";

function Harness({ coverage }: { coverage: CoverageAssessmentView }) {
  const { t } = useTranslation();
  return <CoveragePanel coverage={coverage} t={t} />;
}

function renderPanel(coverage: CoverageAssessmentView) {
  return render(
    <LanguageProvider>
      <Harness coverage={coverage} />
    </LanguageProvider>,
  );
}

const BASE: CoverageAssessmentView = {
  dimensions: [],
  overallCoverage: "no_coverage",
  overallConfidence: "very_limited",
  missingDimensions: [],
  notApplicableDimensions: [],
  reasoning: [],
};

describe("CoveragePanel (Atlas Intelligence Sprint 1)", () => {
  it("shows the overall coverage and confidence badges", () => {
    renderPanel({ ...BASE, overallCoverage: "substantial_coverage", overallConfidence: "high" });
    expect(screen.getByText("Utvärderat")).toBeInTheDocument();
    expect(screen.getByText("Hög tillförlitlighet")).toBeInTheDocument();
  });

  it("lists a real dimension under available when it reached a conclusion", () => {
    renderPanel({
      ...BASE,
      dimensions: [{ dimension: "growth", level: "available", reasoning: [] }],
    });
    expect(screen.getByText("Tillväxt")).toBeInTheDocument();
    expect(screen.queryByText("Atlas har ännu inte utvärderat någon dimension av det här caset.")).not.toBeInTheDocument();
  });

  it("lists a real dimension under missing with its real gap reason, never a raw enum token", () => {
    renderPanel({
      ...BASE,
      dimensions: [{ dimension: "growth", level: "unavailable", reasoning: ["insufficient_historical_periods"] }],
      missingDimensions: ["growth"],
    });
    expect(screen.getByText(/Tillväxt/)).toBeInTheDocument();
    expect(screen.queryByText(/insufficient_historical_periods/)).not.toBeInTheDocument();
  });

  it("marks a partially-available dimension distinctly from a fully-available one", () => {
    renderPanel({
      ...BASE,
      dimensions: [{ dimension: "capital_allocation", level: "partially_available", reasoning: ["missing_dividend_data"] }],
    });
    expect(screen.getByText("Delvis tillgängligt")).toBeInTheDocument();
  });

  it("shows the honest empty state when nothing is available yet, not a blank list", () => {
    renderPanel(BASE);
    expect(screen.getByText("Atlas har ännu inte utvärderat någon dimension av det här caset.")).toBeInTheDocument();
  });

  it("shows the honest empty state when nothing is missing, not a blank list", () => {
    renderPanel({ ...BASE, dimensions: [{ dimension: "growth", level: "available", reasoning: [] }] });
    expect(screen.getByText("Varje utvärderad dimension nådde en verklig slutsats.")).toBeInTheDocument();
  });

  it("tucks not-applicable dimensions behind a collapsed count, never in the missing list", () => {
    renderPanel({ ...BASE, notApplicableDimensions: ["business_model", "management"] });
    expect(screen.getByText(/2 typer av analys/)).toBeInTheDocument();
    expect(screen.getByText("Varje utvärderad dimension nådde en verklig slutsats.")).toBeInTheDocument();
  });

  it("uses the real singular form for exactly one not-applicable dimension, never a raw '(er)' placeholder", () => {
    renderPanel({ ...BASE, notApplicableDimensions: ["business_model"] });
    expect(screen.getByText(/1 typ av analys/)).toBeInTheDocument();
    expect(screen.queryByText(/typ\(er\)/)).not.toBeInTheDocument();
  });

  it("shows no not-applicable note at all when every dimension is real (never an empty expand)", () => {
    renderPanel({ ...BASE, notApplicableDimensions: [] });
    expect(screen.queryByText(/typer? av analys/)).not.toBeInTheDocument();
  });

  it("renders the real counted reasoning sentences behind the confidence level, with real interpolated counts", () => {
    renderPanel({ ...BASE, reasoning: [{ code: "dimensions_conclusive", count: 2, total: 6 }] });
    expect(screen.getByText("2 av 6 utvärderade dimensioner nådde en verklig slutsats.")).toBeInTheDocument();
  });

  it("never shows a raw reason code as the sentence itself", () => {
    renderPanel({ ...BASE, reasoning: [{ code: "thesis_stale", count: null, total: null }] });
    expect(screen.queryByText("thesis_stale")).not.toBeInTheDocument();
    expect(screen.getByText(/har inte granskats/)).toBeInTheDocument();
  });
});
