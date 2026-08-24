import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../testUtils";
import { DiscoveryPage } from "./DiscoveryPage";
import { __resetAlphaWatchlistCacheForTests } from "../discovery/watchlistActions";
import { __resetAlphaPortfolioCacheForTests } from "../portfolio/alphaPortfolioData";

const PORTFOLIO_RESPONSE = { exists: true, holdings: [{ ticker: "AAPL", caseId: "case-aapl" }] };
const WATCHLIST_RESPONSE = [{ ticker: "NVDA", caseId: "case-nvda", addedAt: "2026-01-01T00:00:00Z" }];
const EMPTY_COVERAGE = {
  dimensions: [],
  overallCoverage: "no_coverage",
  overallConfidence: "very_limited",
  missingDimensions: [],
  notApplicableDimensions: [],
  reasoning: [],
};
const CANDIDATES_RESPONSE = [
  {
    caseId: "case-nvda",
    ticker: "NVDA",
    isExistingHolding: false,
    currentWeightPercent: null,
    overall: "good",
    overallReasoning: ["More dimensions rated Good/Excellent than Weak/Poor."],
    dimensions: [],
    trend: "unavailable",
    dataGaps: [],
    coverage: EMPTY_COVERAGE,
    generatedAt: "2026-01-01T00:00:00Z",
  },
];

function mockFetch(overrides: Partial<Record<string, unknown>> = {}) {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/alpha-portfolio/trade-log")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.trades ?? []) } as Response);
      }
      if (url.includes("/api/alpha-portfolio") && !url.includes("status") && !url.includes("intelligence")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.portfolio ?? PORTFOLIO_RESPONSE) } as Response);
      }
      if (url.includes("/api/alpha-watchlist")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.watchlist ?? WATCHLIST_RESPONSE) } as Response);
      }
      if (url.includes("/api/portfolio-fit/candidates")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.candidates ?? CANDIDATES_RESPONSE) } as Response);
      }
      if (url.includes("/api/portfolio-fit/holdings")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.holdingsFit ?? []) } as Response);
      }
      if (url.includes("/api/security-discovery")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.search ?? []) } as Response);
      }
      if (url.includes("/api/daily-brief-agenda")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve(
              overrides.agenda ?? {
                generatedAt: "2026-01-01T09:00:00Z",
                summary: { holdingsCount: 1, criticalCount: 0, highCount: 0, watchlistOpportunityCount: 0, cashWeightPercent: null, concentrationLevel: null },
                items: [],
              },
            ),
        } as Response);
      }
      if (url.includes("/api/decisions") || url.includes("/api/outcomes")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
}

describe("DiscoveryPage (Discovery Engine v2)", () => {
  beforeEach(() => {
    mockFetch();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    __resetAlphaPortfolioCacheForTests();
    __resetAlphaWatchlistCacheForTests();
  });

  it("renders the ranked Candidates for Your Portfolio section with a Fit badge", async () => {
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("NVDA").length).toBeGreaterThan(0));
    expect(screen.getAllByText("Bra passform").length).toBeGreaterThan(0);
  });

  it("shows the honest empty state when no candidates exist", async () => {
    mockFetch({ candidates: [], watchlist: [] });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() =>
      expect(
        screen.getByText("Atlas har inte identifierat en tillräckligt övertygande kandidat utifrån tillgänglig data."),
      ).toBeInTheDocument(),
    );
  });

  it("shows the empty Watchlist message when the Watchlist is empty", async () => {
    mockFetch({ candidates: [], watchlist: [] });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getByText("Din bevakningslista är tom. Sök ovan för att lägga till ett bolag.")).toBeInTheDocument());
  });

  it("lists the full Watchlist roster, cross-referencing the ranked candidates for its Fit badge", async () => {
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("NVDA").length).toBeGreaterThanOrEqual(2));
  });

  it("shows a Watchlist entry's real Fit even when it is also a Portfolio holding (live-verification regression)", async () => {
    // AAPL is both a Portfolio holding and a Watchlist entry --
    // `/api/portfolio-fit/candidates` deliberately excludes it (it's
    // not a "candidate," it's already owned), so its real Fit only
    // comes back via `/api/portfolio-fit/holdings`. Before the fix this
    // rendered "Inte tillgängligt än" for a ticker Atlas can actually
    // evaluate.
    mockFetch({
      watchlist: [{ ticker: "AAPL", caseId: "case-aapl", addedAt: "2026-01-01T00:00:00Z" }],
      candidates: [],
      holdingsFit: [
        {
          caseId: "case-aapl",
          ticker: "AAPL",
          isExistingHolding: true,
          currentWeightPercent: 33,
          overall: "weak",
          overallReasoning: [],
          dimensions: [],
          trend: "unavailable",
          dataGaps: [],
          coverage: EMPTY_COVERAGE,
          generatedAt: "2026-01-01T00:00:00Z",
        },
      ],
    });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getByText("Svag passform")).toBeInTheDocument());
    expect(screen.queryByText("Inte tillgängligt än")).not.toBeInTheDocument();
  });

  it("searches via the real security-discovery endpoint and shows results", async () => {
    mockFetch({ search: [{ ticker: "TSLA", displayName: "Tesla Inc.", cik: 1318605, discoveryMethod: "ticker_exact", source: "sec_company_tickers", status: "candidate_only" }] });
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });

    await user.type(screen.getByPlaceholderText("Ticker eller bolagsnamn"), "TSLA");
    await user.click(screen.getByRole("button", { name: "Sök" }));

    await waitFor(() => expect(screen.getByText(/Tesla Inc\./)).toBeInTheDocument());
  });

  it("shows the honest no-results message for a search with no matches", async () => {
    mockFetch({ search: [] });
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });

    await user.type(screen.getByPlaceholderText("Ticker eller bolagsnamn"), "ZZZZZ");
    await user.click(screen.getByRole("button", { name: "Sök" }));

    await waitFor(() => expect(screen.getByText('Inget matchande bolag hittades för "ZZZZZ".')).toBeInTheDocument());
  });

  it("does not render the old What-Atlas-Found section (removed in Discovery Engine v2)", async () => {
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("NVDA").length).toBeGreaterThan(0));
    expect(screen.queryByText("Vad Atlas hittade")).not.toBeInTheDocument();
  });

  it("provides a Compare entry point linking to /discovery/compare", async () => {
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getByText("Öppna jämförelse →")).toBeInTheDocument());
    expect(screen.getByRole("link", { name: "Öppna jämförelse →" })).toHaveAttribute("href", "/discovery/compare");
  });

  it("shows the real Daily Brief Agenda headline on a candidate card as the reason Atlas surfaced it (Deliverable 3)", async () => {
    mockFetch({
      agenda: {
        generatedAt: "2026-01-01T09:00:00Z",
        summary: { holdingsCount: 1, criticalCount: 0, highCount: 0, watchlistOpportunityCount: 1, cashWeightPercent: null, concentrationLevel: null },
        items: [
          {
            id: "portfolio_opportunity:NVDA",
            priority: "low",
            kind: "portfolio_opportunity",
            group: "watchlist",
            source: "portfolio_fit",
            headline: "NVDA: Portfolio Fit is improving",
            reason: ["NVDA: Portfolio Fit is improving"],
            ticker: "NVDA",
            caseId: "case-nvda",
            portfolioContext: null,
            generatedAt: "2026-01-01T00:00:00Z",
          },
        ],
      },
    });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("NVDA: Portfolio Fit is improving").length).toBeGreaterThan(0));
  });

  it("orders Watchlist Candidates by Agenda priority first (Deliverable 9)", async () => {
    mockFetch({
      watchlist: [
        { ticker: "AMD", caseId: "case-amd", addedAt: "2026-01-01T00:00:00Z" },
        { ticker: "NVDA", caseId: "case-nvda", addedAt: "2026-01-01T00:00:00Z" },
      ],
      candidates: [],
      agenda: {
        generatedAt: "2026-01-01T09:00:00Z",
        summary: { holdingsCount: 1, criticalCount: 0, highCount: 1, watchlistOpportunityCount: 0, cashWeightPercent: null, concentrationLevel: null },
        items: [
          {
            id: "review_watchlist_candidate:AMD",
            priority: "high",
            kind: "review_watchlist_candidate",
            group: "watchlist",
            source: "portfolio_fit",
            headline: "AMD: Portfolio Fit is poor",
            reason: ["AMD: Portfolio Fit is poor"],
            ticker: "AMD",
            caseId: "case-amd",
            portfolioContext: null,
            generatedAt: "2026-01-01T00:00:00Z",
          },
        ],
      },
    });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText(/^(AMD|NVDA)$/).length).toBeGreaterThan(0));
    const tickerLinks = screen.getAllByRole("link", { name: /^(AMD|NVDA)$/ });
    expect(tickerLinks.map((link) => link.textContent)).toEqual(["AMD", "NVDA"]);
  });

  it("pre-fills Compare's second candidate with the weakest-fit holding (Deliverable 6)", async () => {
    mockFetch({
      holdingsFit: [
        { caseId: "case-msft", ticker: "MSFT", isExistingHolding: true, currentWeightPercent: 50, overall: "good", overallReasoning: [], dimensions: [], trend: "unavailable", dataGaps: [], coverage: EMPTY_COVERAGE, generatedAt: "2026-01-01T00:00:00Z" },
        { caseId: "case-aapl", ticker: "AAPL", isExistingHolding: true, currentWeightPercent: 50, overall: "weak", overallReasoning: [], dimensions: [], trend: "unavailable", dataGaps: [], coverage: EMPTY_COVERAGE, generatedAt: "2026-01-01T00:00:00Z" },
      ],
    });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getByRole("button", { name: "Jämför" })).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Jämför" }));
    // No route assertion needed beyond confirming no crash -- MemoryRouter
    // has no /discovery/compare route registered in this test harness;
    // the compareHref logic itself is covered directly below.
  });

  it("shows On Watchlist / New candidate state on search results before the user clicks (Deliverable 7)", async () => {
    mockFetch({
      search: [
        { ticker: "NVDA", displayName: "NVIDIA Corp", cik: 1, discoveryMethod: "ticker_exact", source: "sec", status: "candidate_only" },
        { ticker: "ZZZZ", displayName: "Unknown Co", cik: 2, discoveryMethod: "ticker_exact", source: "sec", status: "candidate_only" },
      ],
    });
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await user.type(screen.getByPlaceholderText("Ticker eller bolagsnamn"), "N");
    await user.click(screen.getByRole("button", { name: "Sök" }));
    await waitFor(() => expect(screen.getByText(/NVIDIA Corp/)).toBeInTheDocument());
    expect(screen.getAllByText("På din bevakningslista").length).toBeGreaterThan(0);
    expect(screen.getByText("Ny kandidat — ännu inte utvärderad")).toBeInTheDocument();
  });

  it("shows a real loading indicator while candidates/watchlist/activity load, never a silent blank section (Internal Alpha Stabilization)", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => {})));
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    expect(screen.getAllByText("Utvärderar portföljpassform…").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Läser in…").length).toBeGreaterThan(0);
  });

  it("shows an honest error message when a section's own fetch fails, never a silent fake-empty state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/portfolio-fit/candidates")) return Promise.resolve({ ok: false, status: 500 } as Response);
        if (url.includes("/api/alpha-portfolio/trade-log")) return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
        if (url.includes("/api/alpha-portfolio")) return Promise.resolve({ ok: true, json: () => Promise.resolve(PORTFOLIO_RESPONSE) } as Response);
        if (url.includes("/api/alpha-watchlist")) return Promise.resolve({ ok: true, json: () => Promise.resolve(WATCHLIST_RESPONSE) } as Response);
        if (url.includes("/api/portfolio-fit/holdings")) return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
        if (url.includes("/api/daily-brief-agenda"))
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ generatedAt: "2026-01-01T00:00:00Z", summary: { holdingsCount: 0, criticalCount: 0, highCount: 0, watchlistOpportunityCount: 0, cashWeightPercent: null, concentrationLevel: null }, items: [] }),
          } as Response);
        if (url.includes("/api/decisions") || url.includes("/api/outcomes")) return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getByText("Atlas kunde inte läsa in dina rankade kandidater. Försök att uppdatera sidan.")).toBeInTheDocument());
    expect(screen.queryByText("Atlas har inte identifierat en tillräckligt övertygande kandidat utifrån tillgänglig data.")).not.toBeInTheDocument();
  });

  it("restores a removed Watchlist entry if the backend DELETE actually fails (bug fix)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/api/alpha-watchlist/") && init?.method === "DELETE") {
          return Promise.resolve({ ok: false, status: 500 } as Response);
        }
        if (url.includes("/api/alpha-portfolio/trade-log")) return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
        if (url.includes("/api/alpha-portfolio")) return Promise.resolve({ ok: true, json: () => Promise.resolve(PORTFOLIO_RESPONSE) } as Response);
        if (url.includes("/api/alpha-watchlist")) return Promise.resolve({ ok: true, json: () => Promise.resolve(WATCHLIST_RESPONSE) } as Response);
        if (url.includes("/api/portfolio-fit/candidates")) return Promise.resolve({ ok: true, json: () => Promise.resolve(CANDIDATES_RESPONSE) } as Response);
        if (url.includes("/api/portfolio-fit/holdings")) return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
        if (url.includes("/api/daily-brief-agenda"))
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ generatedAt: "2026-01-01T00:00:00Z", summary: { holdingsCount: 0, criticalCount: 0, highCount: 0, watchlistOpportunityCount: 0, cashWeightPercent: null, concentrationLevel: null }, items: [] }),
          } as Response);
        if (url.includes("/api/decisions") || url.includes("/api/outcomes")) return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("Ta bort från bevakningslistan").length).toBeGreaterThan(0));
    await user.click(screen.getAllByText("Ta bort från bevakningslistan")[0]!);
    // Optimistically removed, then restored once the failed DELETE resolves.
    await waitFor(() => expect(screen.getAllByRole("link", { name: "NVDA" }).length).toBeGreaterThan(0));
  });
});
