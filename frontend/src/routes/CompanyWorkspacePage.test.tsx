import { describe, expect, it, vi, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "../testUtils";
import { CompanyWorkspacePage } from "./CompanyWorkspacePage";

const PORTFOLIO_RESPONSE = { exists: true, holdings: [{ ticker: "AAPL", caseId: "case-aapl", reconciliationStatus: "NONE" }] };
const ANALYSIS_RESPONSE = {
  caseId: "case-aapl",
  holdingContext: { held: true, valueAbsolute: null, weightPercent: 33 },
  currentThesis: {},
  isThesisStale: false,
  confidence: "full",
  conviction: { level: "moderate", reasons: [] },
  coverage: {
    dimensions: [],
    overallCoverage: "no_coverage",
    overallConfidence: "very_limited",
    missingDimensions: [],
    notApplicableDimensions: [],
    reasoning: [],
  },
  businessAnalysis: { findings: [] },
  valuationSupport: { status: "insufficient_input", gap: null },
  risk: { findings: [] },
  evidenceQuality: null,
  openQuestions: [],
  recommendation: { level: "thesis_intact", badgeLabel: "", statement: "", outlookAlignment: {}, missingEvaluations: [] },
  // `companyProfile: null` + `financialHistory: []` deliberately route this
  // fixture through the honest "not yet analyzed" branch -- CompanyHeader
  // (where the new Compare link lives) renders regardless of that branch.
  companyProfile: null,
  financialHistory: [],
  marketSnapshot: null,
  strengths: [],
  risks: [],
  valuationContext: {},
  atlasThesis: {},
  outlook: { shortTerm: {}, longTerm: {} },
  changeIntelligenceAvailable: false,
  isBaselineCase: true,
  latestChanges: [],
  thesisChange: "unchanged",
  currentAnalysisAt: "2026-01-01T00:00:00Z",
};

function mockFetch() {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/alpha-portfolio/cockpit")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ holdings: [] }) } as Response);
      }
      if (url.includes("/api/alpha-portfolio/trade-log")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
      }
      if (url.includes("/api/alpha-portfolio")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(PORTFOLIO_RESPONSE) } as Response);
      }
      if (url.includes("/api/alpha-watchlist")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
      }
      if (url.includes("/api/cases/") && url.includes("/analysis")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(ANALYSIS_RESPONSE) } as Response);
      }
      if (url.includes("/api/decisions") || url.includes("/api/outcomes")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
}

describe("CompanyWorkspacePage (Product Sprint 10 -- Navigation & Workflow Excellence)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("offers a Compare entry point -- previously a dead end (Deliverable 1/4)", async () => {
    mockFetch();
    renderWithProviders(<CompanyWorkspacePage />, { route: "/company/AAPL", path: "/company/:ticker" });
    await waitFor(() => expect(screen.getByText("AAPL")).toBeInTheDocument());
    const link = screen.getByRole("link", { name: /Jämför med en annan kandidat/ });
    expect(link).toHaveAttribute("href", "/discovery/compare?a=AAPL");
  });
});
