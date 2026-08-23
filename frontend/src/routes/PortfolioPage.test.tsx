import { describe, expect, it, vi, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "../testUtils";
import { PortfolioPage } from "./PortfolioPage";

function cockpitHolding(overrides: Record<string, unknown> = {}) {
  return {
    ticker: "AAPL",
    caseId: "case-aapl",
    weightPercent: 30,
    valueAbsolute: null,
    reconciliationStatus: "NONE",
    conviction: { level: "moderate", reasons: [] },
    analysisCoverage: { level: "substantial_coverage", reasons: [] },
    valuation: { status: "fairly_valued" },
    business: { growth: "moderate", capitalAllocation: "moderate" },
    riskProjection: { category: "financial_risk", status: "moderate" },
    confidence: "full",
    isThesisStale: false,
    attention: { priority: "standard_review", reasons: [] },
    decisionSupport: { level: "reduction_supported", badgeLabel: "Reduction supported", statement: "..." },
    ...overrides,
  };
}

function portfolioView(overrides: Record<string, unknown> = {}) {
  return {
    exists: true,
    entryMode: "PERCENT_ONLY",
    hasAbsoluteValues: false,
    holdings: [
      { ticker: "AAPL", weightPercent: 30, valueAbsolute: null, caseId: "case-aapl", reconciliationStatus: "NONE" },
      { ticker: "MSFT", weightPercent: 70, valueAbsolute: null, caseId: "case-msft", reconciliationStatus: "NONE" },
    ],
    cashWeightPercent: 5,
    cashValueAbsolute: null,
    totalValue: null,
    numberOfHoldings: 2,
    concentrationLevel: "Elevated",
    objective: null,
    horizon: null,
    awaitingReconciliation: false,
    ...overrides,
  };
}

function agendaResponse(overrides: Record<string, unknown> = {}) {
  return {
    generatedAt: "2026-01-01T09:00:00Z",
    summary: {
      holdingsCount: 2,
      criticalCount: 1,
      highCount: 0,
      watchlistOpportunityCount: 0,
      cashWeightPercent: 5,
      concentrationLevel: "Elevated",
    },
    items: [
      {
        id: "review_portfolio_position:AAPL",
        priority: "critical",
        kind: "review_portfolio_position",
        group: "portfolio",
        source: "portfolio_status",
        headline: "AAPL: outcome without execution (1 item(s))",
        reason: ["AAPL: outcome without execution (1 item(s))"],
        ticker: "AAPL",
        caseId: "case-aapl",
        portfolioContext: null,
        generatedAt: "2026-01-01T00:00:00Z",
        // Localization fix (Portfolio live-verification follow-up):
        // a real workflow item always carries these two -- the raw
        // English `headline` above is the backend's own unused-by-the
        // -UI fallback now, kept here only so a test overriding this
        // fixture without `attentionCategory` still gets a headline.
        attentionCategory: "OUTCOME_WITHOUT_EXECUTION",
        attentionCount: 1,
      },
    ],
    ...overrides,
  };
}

function fitAssessment(overrides: Record<string, unknown> = {}) {
  return {
    caseId: "case-aapl",
    ticker: "AAPL",
    isExistingHolding: true,
    currentWeightPercent: 30,
    overall: "weak",
    overallReasoning: ["More dimensions rated Weak/Poor than Good/Excellent."],
    dimensions: [],
    trend: "declining",
    dataGaps: [],
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function mockFetch(overrides: {
  view?: Record<string, unknown>;
  cockpitHoldings?: Record<string, unknown>[];
  fitAssessments?: Record<string, unknown>[];
  agenda?: Record<string, unknown>;
} = {}) {
  const view = overrides.view ?? portfolioView();
  const cockpitHoldings = overrides.cockpitHoldings ?? [
    cockpitHolding(),
    cockpitHolding({ ticker: "MSFT", caseId: "case-msft", weightPercent: 70, decisionSupport: { level: "thesis_intact", badgeLabel: "", statement: "" } }),
  ];
  const fitAssessments = overrides.fitAssessments ?? [
    fitAssessment(),
    fitAssessment({ ticker: "MSFT", caseId: "case-msft", overall: "excellent", trend: "unchanged", currentWeightPercent: 70 }),
  ];
  const agenda = overrides.agenda ?? agendaResponse();

  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/alpha-portfolio/cockpit")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ exists: true, holdings: cockpitHoldings, unresolvedHoldings: [], priorityReviewCount: 0 }),
        } as Response);
      }
      if (url.includes("/api/alpha-portfolio/trade-log")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
      }
      if (url.includes("/api/alpha-portfolio")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(view) } as Response);
      }
      if (url.includes("/api/portfolio-fit/holdings")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(fitAssessments) } as Response);
      }
      if (url.includes("/api/daily-brief-agenda")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(agenda) } as Response);
      }
      if (url.includes("/api/decisions") || url.includes("/api/outcomes")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
}

describe("PortfolioPage (Product Sprint 8 -- Portfolio Excellence)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders portfolio status: holdings count, cash, largest position, and concentration", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("2 tillgångar")).toBeInTheDocument());
    expect(screen.getAllByText("5%").length).toBeGreaterThan(0);
    expect(screen.getByText("MSFT (70%)")).toBeInTheDocument();
    expect(screen.getAllByText("Förhöjd").length).toBeGreaterThan(0);
  });

  it("shows one critical pill sourced from the shared Daily Brief Agenda, never a second competing count", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("1 kritiska")).toBeInTheDocument());
  });

  it("renders Attention Required from the shared Daily Brief Agenda endpoint", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Kräver uppmärksamhet")).toBeInTheDocument());
    // Localization fix (Portfolio live-verification follow-up): a real
    // workflow item's headline is now composed and translated from
    // `attentionCategory`/`attentionCount`, never the backend's raw
    // English `headline` string -- see `describeAgendaHeadline.ts`.
    expect(screen.getByText(/utfall utan verkställande/)).toBeInTheDocument();
    expect(screen.queryByText(/outcome without execution/)).not.toBeInTheDocument();
  });

  it("shows the honest empty state for Attention Required when the agenda has no portfolio items", async () => {
    mockFetch({ agenda: agendaResponse({ items: [], summary: { holdingsCount: 2, criticalCount: 0, highCount: 0, watchlistOpportunityCount: 0, cashWeightPercent: 5, concentrationLevel: "Elevated" } }) });
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Kräver uppmärksamhet")).toBeInTheDocument());
    expect(screen.getByText("Atlas har inga väsentliga förändringar att rapportera idag.")).toBeInTheDocument();
  });

  function orderedTickersFromRowButtons(): string[] {
    return screen.getAllByRole("button", { name: /^Öppna (AAPL|MSFT)s vy$/ }).map((button) => {
      const match = button.getAttribute("aria-label")!.match(/^Öppna (AAPL|MSFT)s vy$/);
      if (!match || !match[1]) throw new Error("expected row button aria-label to match");
      return match[1];
    });
  }

  it("orders holdings by attention by default -- AAPL (flagged, lower weight) before MSFT (unflagged, higher weight)", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(orderedTickersFromRowButtons().length).toBe(2));
    expect(orderedTickersFromRowButtons()).toEqual(["AAPL", "MSFT"]);
  });

  it("re-sorts holdings by weight when Weight is selected", async () => {
    const user = (await import("@testing-library/user-event")).default.setup();
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(orderedTickersFromRowButtons().length).toBe(2));
    await user.click(screen.getByRole("link", { name: "Andel" }));
    expect(orderedTickersFromRowButtons()).toEqual(["MSFT", "AAPL"]);
  });

  it("shows the same Portfolio Fit rating for AAPL in both the Holdings Table and the Weakest Holdings section", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Svagaste innehaven")).toBeInTheDocument());
    const fitLabels = screen.getAllByText("Svag passform");
    expect(fitLabels.length).toBeGreaterThanOrEqual(2);
  });

  it("lists AAPL in Weakest Holdings (weak fit + reduction-supported) but not MSFT", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByText("Svagaste innehaven");
    // Exactly one holding (AAPL, weak fit + reduction-supported) qualifies
    // -- MSFT (excellent fit, thesis intact) does not -- so exactly one
    // "Compare alternatives" investigation link renders.
    expect(screen.getAllByRole("link", { name: /Jämför alternativ/ })).toHaveLength(1);
    expect(screen.queryByText("Inga innehav visar just nu svag portföljpassform eller ett reduktionsstött beslutsstöd.")).not.toBeInTheDocument();
  });

  it("offers Watchlist and Discovery entry points", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Utforska vidare")).toBeInTheDocument());
    expect(screen.getByRole("link", { name: /Öppna bevakningslistan/ })).toHaveAttribute("href", "/watchlist");
    expect(screen.getByRole("link", { name: /Öppna Discovery/ })).toHaveAttribute("href", "/discovery");
  });

  it("shows the empty-portfolio state honestly when no holdings exist", async () => {
    mockFetch({ view: portfolioView({ holdings: [], numberOfHoldings: 0 }) });
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Importera portfölj", { exact: false })).toBeInTheDocument());
  });

  it("never renders a fabricated Sector Allocation, only the honest disclosure", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Sektorfördelning")).toBeInTheDocument());
    expect(screen.getByText(/Sektorsdata följs ännu inte/)).toBeInTheDocument();
  });
});
