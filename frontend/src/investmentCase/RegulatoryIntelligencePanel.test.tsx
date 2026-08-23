import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { RegulatoryIntelligencePanel } from "./RegulatoryIntelligencePanel";
import type { RegulatoryFilingView } from "./managementIntelligenceApi";
import type { LegalProceedingsIntelligenceView, RiskFactorIntelligenceView } from "./regulatoryIntelligenceApi";

const EMPTY_RISK: RiskFactorIntelligenceView = { categories: [], changes: [], filingsConsidered: [] };
const EMPTY_LEGAL: LegalProceedingsIntelligenceView = { categories: [], changes: [], filingsConsidered: [] };

function Harness(props: {
  regulatoryFilings?: RegulatoryFilingView[];
  riskFactor?: RiskFactorIntelligenceView;
  legalProceedings?: LegalProceedingsIntelligenceView;
}) {
  const { t } = useTranslation();
  return (
    <RegulatoryIntelligencePanel
      regulatoryFilings={props.regulatoryFilings ?? []}
      riskFactor={props.riskFactor ?? EMPTY_RISK}
      legalProceedings={props.legalProceedings ?? EMPTY_LEGAL}
      t={t}
    />
  );
}

function renderPanel(props: Parameters<typeof Harness>[0] = {}) {
  return render(
    <LanguageProvider>
      <Harness {...props} />
    </LanguageProvider>,
  );
}

const AAPL_10K: RegulatoryFilingView = {
  formType: "10-K", filedAt: "2025-11-01T00:00:00Z", accessionNumber: "0000320193-25-000100",
  filingUrl: "https://example.test/10k", periodOfReport: "2025-09-30",
};

describe("RegulatoryIntelligencePanel (Product Utilization Sprint 1)", () => {
  it("shows an honest 'no filing known yet' state with no filings ingested", () => {
    renderPanel();
    expect(screen.getByText("Inga rapporter inhämtade ännu.")).toBeInTheDocument();
  });

  it("lists a real ingested filing's form type behind the expand control, with the right count", () => {
    renderPanel({ regulatoryFilings: [AAPL_10K] });
    const summary = screen.getByText(/1 rapport/);
    expect(summary.closest("details")).toContainElement(screen.getByText(/10-K/));
  });

  it("distinguishes 'content not yet acquired' (a 10-K is known) from 'no relevant filing known', for both filing-content-gated sub-sections", () => {
    const { unmount } = renderPanel({ regulatoryFilings: [AAPL_10K] });
    // A 10-K is relevant to both Risk Factors and Legal Proceedings.
    expect(screen.getAllByText(/Atlas har identifierat en relevant rapport/).length).toBe(2);
    unmount();

    renderPanel({ regulatoryFilings: [] });
    expect(screen.getAllByText(/Atlas har ännu inte identifierat någon relevant rapport/).length).toBe(2);
  });

  it("shows a real risk-factor category badge with a humanized label", () => {
    renderPanel({
      riskFactor: {
        categories: [
          {
            kind: "cybersecurity",
            disclosures: [{ categories: ["cybersecurity"], text: "A material cybersecurity incident could disrupt operations.", source: "risk_factors_section", accessionNumber: "0000320193-25-000100", filedAt: "2025-11-01T00:00:00Z" }],
          },
        ],
        changes: [],
        filingsConsidered: ["0000320193-25-000100"],
      },
    });
    expect(screen.getAllByText("Cybersecurity").length).toBeGreaterThan(0);
  });

  it("keeps risk-factor and legal-proceedings evidence in their own separate sub-sections", () => {
    renderPanel({
      riskFactor: {
        categories: [{ kind: "cybersecurity", disclosures: [{ categories: ["cybersecurity"], text: "Real risk text.", source: "risk_factors_section", accessionNumber: "acc-1", filedAt: "2025-11-01T00:00:00Z" }] }],
        changes: [], filingsConsidered: ["acc-1"],
      },
      legalProceedings: {
        categories: [{ kind: "antitrust", disclosures: [{ categories: ["antitrust"], text: "Real legal text.", source: "legal_proceedings_section", accessionNumber: "acc-1", filedAt: "2025-11-01T00:00:00Z" }] }],
        changes: [], filingsConsidered: ["acc-1"],
      },
    });
    expect(screen.getByText("Real risk text.")).toBeInTheDocument();
    expect(screen.getByText("Real legal text.")).toBeInTheDocument();
    expect(screen.getByText("Real risk text.").closest("details")).not.toContainElement(screen.getByText("Real legal text."));
    expect(screen.getAllByText("Antitrust").length).toBeGreaterThan(0);
  });
});
