import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { KnowledgeCoveragePanel } from "./KnowledgeCoveragePanel";
import type { InvestmentCaseKnowledgeCoverageView, KnowledgeDomainCoverageView } from "./knowledgeCoverageApi";

function Harness({ coverage }: { coverage: InvestmentCaseKnowledgeCoverageView }) {
  const { t } = useTranslation();
  return <KnowledgeCoveragePanel coverage={coverage} t={t} />;
}

function renderPanel(coverage: InvestmentCaseKnowledgeCoverageView) {
  return render(
    <LanguageProvider>
      <Harness coverage={coverage} />
    </LanguageProvider>,
  );
}

function domain(overrides: Partial<KnowledgeDomainCoverageView> = {}): KnowledgeDomainCoverageView {
  return {
    domain: "company_profile",
    group: "company_overview",
    level: "not_applicable",
    freshness: "not_applicable",
    dominance: "not_applicable",
    missingReasons: ["domain_not_yet_wired"],
    ...overrides,
  };
}

const ALL_NOT_APPLICABLE: InvestmentCaseKnowledgeCoverageView = {
  domains: [domain()],
  availableCount: 0,
  partiallyAvailableCount: 0,
  applicableCount: 0,
  totalDomainCount: 1,
  notApplicableCount: 1,
  missingDomains: [],
  notApplicableDomains: ["company_profile"],
  coveragePercent: 0,
};

describe("KnowledgeCoveragePanel (Automatic Investment Case Builder Foundation)", () => {
  it("shows the available/applicable count alongside the percentage, never the percentage alone", () => {
    renderPanel({
      ...ALL_NOT_APPLICABLE,
      domains: [domain({ level: "available", missingReasons: [] })],
      availableCount: 1,
      applicableCount: 1,
      notApplicableCount: 0,
      notApplicableDomains: [],
      coveragePercent: 100,
    });
    expect(screen.getByText(/1 av 1 tillämpliga områden tillgängliga — 100%/)).toBeInTheDocument();
  });

  it("lists an available domain with its group heading and a status badge", () => {
    renderPanel({
      ...ALL_NOT_APPLICABLE,
      domains: [domain({ level: "available", missingReasons: [] })],
      availableCount: 1,
      applicableCount: 1,
      notApplicableCount: 0,
      notApplicableDomains: [],
    });
    expect(screen.getByText("Bolagsöversikt")).toBeInTheDocument();
    expect(screen.getByText("Bolagsprofil")).toBeInTheDocument();
    expect(screen.getByText("Tillgängligt")).toBeInTheDocument();
  });

  it("shows a specific missing-reason sentence for an unavailable domain, never a raw enum token", () => {
    renderPanel({
      ...ALL_NOT_APPLICABLE,
      domains: [domain({ level: "unavailable", missingReasons: ["no_source_document_ingested"] })],
      applicableCount: 1,
      notApplicableCount: 0,
      notApplicableDomains: [],
    });
    expect(screen.getByText(/Inget relevant dokument har hämtats in/)).toBeInTheDocument();
    expect(screen.queryByText("no_source_document_ingested")).not.toBeInTheDocument();
  });

  it("tucks not-applicable domains behind a collapsed count, using the real singular form, never a raw '(n)' placeholder", () => {
    renderPanel(ALL_NOT_APPLICABLE);
    expect(screen.getByText(/1 kunskapsområde ingår/)).toBeInTheDocument();
    expect(screen.queryByText(/kunskapsområde\(n\)/)).not.toBeInTheDocument();
    expect(screen.queryByText("Bolagsöversikt")).not.toBeInTheDocument();
  });

  it("shows no not-applicable note at all when every domain is applicable", () => {
    renderPanel({
      ...ALL_NOT_APPLICABLE,
      domains: [domain({ level: "available", missingReasons: [] })],
      availableCount: 1,
      applicableCount: 1,
      notApplicableCount: 0,
      notApplicableDomains: [],
    });
    expect(screen.queryByText(/kunskapsområde/)).not.toBeInTheDocument();
  });

  it("marks a partially-available domain distinctly from a fully-available one", () => {
    renderPanel({
      ...ALL_NOT_APPLICABLE,
      domains: [domain({ level: "partially_available", missingReasons: ["insufficient_history"] })],
      partiallyAvailableCount: 1,
      applicableCount: 1,
      notApplicableCount: 0,
      notApplicableDomains: [],
    });
    expect(screen.getByText("Delvis tillgängligt")).toBeInTheDocument();
  });
});
