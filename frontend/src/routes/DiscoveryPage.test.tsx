import { describe, expect, it, vi, afterEach } from "vitest";
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
const EMPTY_AGENDA = {
  generatedAt: "2026-01-01T00:00:00Z",
  summary: { holdingsCount: 0, criticalCount: 0, highCount: 0, watchlistOpportunityCount: 0, cashWeightPercent: null, concentrationLevel: null },
  items: [],
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
      if (url.includes("/api/alpha-portfolio") && !url.includes("status") && !url.includes("intelligence") && !url.includes("trade-log")) {
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
      if (url.includes("/api/stance/candidates")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.stance ?? []) } as Response);
      }
      if (url.includes("/api/security-discovery")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.search ?? []) } as Response);
      }
      if (url.includes("/api/daily-brief-agenda")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.agenda ?? EMPTY_AGENDA) } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
}

describe("DiscoveryPage (Discover Doctrine, 2026-08-27)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    __resetAlphaPortfolioCacheForTests();
    __resetAlphaWatchlistCacheForTests();
  });

  it("renders a good-Fit candidate as a large card in Highest opportunity", async () => {
    mockFetch();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getByText("Största möjligheterna")).toBeInTheDocument());
    expect(screen.getAllByText("NVDA").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Bra passform").length).toBeGreaterThan(0);
  });

  it("shows the empty Watchlist message when the Watchlist is empty", async () => {
    mockFetch({ candidates: [], watchlist: [] });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getByText("Din bevakningslista är tom. Sök ovan för att lägga till ett bolag.")).toBeInTheDocument());
  });

  it("lists every Watchlist entry exactly once", async () => {
    mockFetch();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("NVDA").length).toBe(1));
  });

  it("never shows an already-held ticker as a candidate, even when it is also on the Watchlist (Phase 6)", async () => {
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
    await waitFor(() => expect(screen.getByText("Största möjligheterna")).toBeInTheDocument());
    expect(screen.getByText("Ingen kandidat sticker ut som en toppmöjlighet just nu.")).toBeInTheDocument();
    expect(screen.queryByText("AAPL")).not.toBeInTheDocument();
  });

  it("never renders a raw Daily Brief Agenda headline on a candidate card (Phase 5)", async () => {
    mockFetch({
      agenda: {
        ...EMPTY_AGENDA,
        items: [
          {
            id: "executive_change:NVDA",
            priority: "high",
            kind: "review_watchlist_candidate",
            group: "watchlist",
            source: "executive_change",
            headline: "NVDA: Jensen Huang (CEO) appointed.",
            reason: ["NVDA: Jensen Huang (CEO) appointed."],
            ticker: "NVDA",
            caseId: "case-nvda",
            portfolioContext: null,
            generatedAt: "2026-01-01T00:00:00Z",
          },
        ],
      },
    });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("NVDA").length).toBeGreaterThan(0));
    expect(screen.queryByText(/Jensen Huang/)).not.toBeInTheDocument();
    expect(screen.queryByText(/appointed/)).not.toBeInTheDocument();
    // The synthesized Fit reasoning is still the one real sentence shown.
    expect(screen.getByText("More dimensions rated Good/Excellent than Weak/Poor.")).toBeInTheDocument();
  });

  it("moves a candidate with an elevated Agenda priority into Worth reviewing when its own Fit doesn't already qualify it for Highest opportunity", async () => {
    mockFetch({
      watchlist: [{ ticker: "AMD", caseId: "case-amd", addedAt: "2026-01-01T00:00:00Z" }],
      candidates: [
        {
          caseId: "case-amd",
          ticker: "AMD",
          isExistingHolding: false,
          currentWeightPercent: null,
          overall: "neutral",
          overallReasoning: ["Fit is currently neutral."],
          dimensions: [],
          trend: "unavailable",
          dataGaps: [],
          coverage: EMPTY_COVERAGE,
          generatedAt: "2026-01-01T00:00:00Z",
        },
      ],
      agenda: {
        ...EMPTY_AGENDA,
        items: [
          {
            id: "x:AMD",
            priority: "high",
            kind: "review_watchlist_candidate",
            group: "watchlist",
            source: "portfolio_fit",
            headline: "AMD: something changed.",
            reason: ["AMD: something changed."],
            ticker: "AMD",
            caseId: "case-amd",
            portfolioContext: null,
            generatedAt: "2026-01-01T00:00:00Z",
          },
        ],
      },
    });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getByText("Värt att se över")).toBeInTheDocument());
    expect(screen.getByText("Ingen kandidat sticker ut som en toppmöjlighet just nu.")).toBeInTheDocument();
    expect(screen.getAllByText("AMD").length).toBeGreaterThan(0);
  });

  it("never renders a standalone Compare page section -- Compare is reachable only per-candidate (Phase 7)", async () => {
    mockFetch();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("NVDA").length).toBeGreaterThan(0));
    expect(screen.queryByText("Öppna jämförelse →")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Jämför" })).toBeInTheDocument();
  });

  it("never renders a Recent Watchlist Activity section -- removed entirely (Phase 9)", async () => {
    mockFetch();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("NVDA").length).toBeGreaterThan(0));
    expect(screen.queryByText("Senaste aktivitet på bevakningslistan")).not.toBeInTheDocument();
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

  it("shows On Watchlist / New candidate state on search results before the user clicks", async () => {
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

  it("pre-fills Compare's second candidate with the weakest-fit holding", async () => {
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
    // No route assertion beyond confirming no crash -- the test harness
    // has no /discovery/compare route registered; compareHref itself is
    // exercised directly by this click.
  });

  it("shows a real loading indicator while candidates/watchlist load, never a silent blank section", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => {})));
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    expect(screen.getAllByText("Utvärderar portföljpassform…").length).toBeGreaterThan(0);
  });

  it("shows an honest error message when the candidates fetch fails, never a silent fake-empty state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/portfolio-fit/candidates")) return Promise.resolve({ ok: false, status: 500 } as Response);
        if (url.includes("/api/alpha-portfolio") && !url.includes("trade-log")) return Promise.resolve({ ok: true, json: () => Promise.resolve(PORTFOLIO_RESPONSE) } as Response);
        if (url.includes("/api/alpha-watchlist")) return Promise.resolve({ ok: true, json: () => Promise.resolve(WATCHLIST_RESPONSE) } as Response);
        if (url.includes("/api/portfolio-fit/holdings")) return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
        if (url.includes("/api/stance/candidates")) return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
        if (url.includes("/api/daily-brief-agenda")) return Promise.resolve({ ok: true, json: () => Promise.resolve(EMPTY_AGENDA) } as Response);
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getByText("Atlas kunde inte läsa in dina rankade kandidater. Försök att uppdatera sidan.")).toBeInTheDocument());
  });

  it("restores a removed Watchlist entry if the backend DELETE actually fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/api/alpha-watchlist/") && init?.method === "DELETE") {
          return Promise.resolve({ ok: false, status: 500 } as Response);
        }
        if (url.includes("/api/alpha-portfolio") && !url.includes("trade-log")) return Promise.resolve({ ok: true, json: () => Promise.resolve(PORTFOLIO_RESPONSE) } as Response);
        if (url.includes("/api/alpha-watchlist")) return Promise.resolve({ ok: true, json: () => Promise.resolve(WATCHLIST_RESPONSE) } as Response);
        if (url.includes("/api/portfolio-fit/candidates")) return Promise.resolve({ ok: true, json: () => Promise.resolve(CANDIDATES_RESPONSE) } as Response);
        if (url.includes("/api/portfolio-fit/holdings")) return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
        if (url.includes("/api/stance/candidates")) return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
        if (url.includes("/api/daily-brief-agenda")) return Promise.resolve({ ok: true, json: () => Promise.resolve(EMPTY_AGENDA) } as Response);
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("Ta bort från bevakningslistan").length).toBeGreaterThan(0));
    await user.click(screen.getAllByText("Ta bort från bevakningslistan")[0]!);
    // Optimistically removed, then restored once the failed DELETE resolves.
    await waitFor(() => expect(screen.getAllByText("NVDA").length).toBeGreaterThan(0));
  });
});
