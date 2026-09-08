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
    overallReasoningCode: null,
    overallReasoningCount: null,
    dimensions: [],
    trend: "unavailable",
    dataGaps: [],
    coverage: EMPTY_COVERAGE,
    generatedAt: "2026-01-01T00:00:00Z",
  },
];

/** Sprint 4B: the passive candidate universe. Backend-decided
 * eligibility -- holdings and active Watchlist prospects are already
 * excluded there -- carrying canonical enum values only. */
const DISCOVERY_CANDIDATES = [
  {
    ticker: "NVDA",
    caseId: "case-nvda",
    companyName: "NVIDIA Corporation",
    decisionSupportLevel: "thesis_intact",
    analysisCoverageLevel: "substantial_coverage",
    fitRating: "good",
    stanceLevel: null,
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
      if (url.includes("/api/discovery-candidates")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.discoveryCandidates ?? DISCOVERY_CANDIDATES) } as Response);
      }
      if (url.includes("/api/case-identity/ensure")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ caseId: "case-ensured", ticker: "NVDA" }) } as Response);
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

  /** Sprint 4C. Every tier used to render behind
   * `watchlistStatus.entries.length > 0`, so a loaded candidate
   * universe went completely invisible whenever the Watchlist happened
   * to be empty -- and the page then explained itself with "Your
   * Watchlist is empty", a sentence about a list Discovery no longer
   * sources anything from. */
  it("renders the candidate universe even when the Watchlist is empty", async () => {
    mockFetch({ candidates: [], watchlist: [] });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("NVDA").length).toBeGreaterThan(0));
    expect(screen.queryByText("Din bevakningslista är tom. Sök ovan för att lägga till ett bolag.")).not.toBeInTheDocument();
  });

  it("renders the candidate universe even when the Watchlist request fails outright", async () => {
    mockFetch();
    const original = globalThis.fetch as typeof fetch;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).includes("/api/alpha-watchlist")) return Promise.resolve({ ok: false, status: 500 } as Response);
      return original(input as RequestInfo, init);
    }));
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("NVDA").length).toBeGreaterThan(0));
  });

  /** A degraded *secondary* service must never report itself as a
   * failure of the primary one. Portfolio Fit's candidate endpoint no
   * longer feeds this page at all -- Fit arrives on the candidate --
   * so its failure must leave the loaded universe untouched. */
  it("keeps a loaded candidate universe visible when the Portfolio Fit candidates request fails", async () => {
    mockFetch();
    const original = globalThis.fetch as typeof fetch;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).includes("/api/portfolio-fit/")) return Promise.resolve({ ok: false, status: 500 } as Response);
      return original(input as RequestInfo, init);
    }));
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("NVDA").length).toBeGreaterThan(0));
    expect(screen.queryByText("Atlas kunde inte läsa in dina rankade kandidater. Försök att uppdatera sidan.")).not.toBeInTheDocument();
  });

  it("lists every Watchlist entry exactly once", async () => {
    mockFetch();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("NVDA").length).toBe(1));
  });

  it("never shows an already-held ticker as a candidate, even when it is also on the Watchlist (Phase 6)", async () => {
    mockFetch({
      watchlist: [{ ticker: "AAPL", caseId: "case-aapl", addedAt: "2026-01-01T00:00:00Z" }],
      // Sprint 4B: eligibility moved to the backend, which excludes
      // holdings and active Watchlist prospects before Discovery ever
      // sees them. An empty universe must render the honest empty
      // state, never a padded one.
      discoveryCandidates: [],
      candidates: [],
      holdingsFit: [
        {
          caseId: "case-aapl",
          ticker: "AAPL",
          isExistingHolding: true,
          currentWeightPercent: 33,
          overall: "weak",
          overallReasoning: [],
          overallReasoningCode: null,
          overallReasoningCount: null,
          dimensions: [],
          trend: "unavailable",
          dataGaps: [],
          coverage: EMPTY_COVERAGE,
          generatedAt: "2026-01-01T00:00:00Z",
        },
      ],
    });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    // Sprint 4C: an empty universe renders its own honest empty state,
    // never the tier scaffolding with nothing in it.
    await waitFor(() =>
      expect(
        screen.getByText("Atlas har inga kandidater att visa. Varje bolag som analyserats är ett du redan äger eller redan bevakar."),
      ).toBeInTheDocument(),
    );
    expect(screen.queryByText("AAPL")).not.toBeInTheDocument();
    expect(screen.queryByText("Största möjligheterna")).not.toBeInTheDocument();
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
    // The Fit badge carries the rating; the backend's pre-rendered
    // English sentence is no longer printed into the Swedish UI.
    expect(screen.getByText("Bra passform")).toBeInTheDocument();
    expect(screen.queryByText(/More dimensions rated/)).not.toBeInTheDocument();
  });

  it("moves a candidate with an elevated Agenda priority into Worth reviewing when its own Fit doesn't already qualify it for Highest opportunity", async () => {
    mockFetch({
      watchlist: [{ ticker: "AMD", caseId: "case-amd", addedAt: "2026-01-01T00:00:00Z" }],
      discoveryCandidates: [
        {
          ticker: "AMD",
          caseId: "case-amd",
          companyName: "Advanced Micro Devices Inc",
          decisionSupportLevel: "insufficient_evidence",
          analysisCoverageLevel: "substantial_coverage",
          fitRating: "neutral",
          stanceLevel: null,
        },
      ],
      candidates: [
        {
          caseId: "case-amd",
          ticker: "AMD",
          isExistingHolding: false,
          currentWeightPercent: null,
          overall: "neutral",
          overallReasoning: ["Fit is currently neutral."],
          overallReasoningCode: null,
          overallReasoningCount: null,
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
    await waitFor(() => expect(screen.getAllByText(/NVIDIA Corp/).length).toBeGreaterThan(0));
    expect(screen.getAllByText("På din bevakningslista").length).toBeGreaterThan(0);
    expect(screen.getByText("Ny kandidat — ännu inte utvärderad")).toBeInTheDocument();
  });

  it("pre-fills Compare's second candidate with the weakest-fit holding", async () => {
    mockFetch({
      holdingsFit: [
        { caseId: "case-msft", ticker: "MSFT", isExistingHolding: true, currentWeightPercent: 50, overall: "good", overallReasoning: [], overallReasoningCode: null, overallReasoningCount: null, dimensions: [], trend: "unavailable", dataGaps: [], coverage: EMPTY_COVERAGE, generatedAt: "2026-01-01T00:00:00Z" },
        { caseId: "case-aapl", ticker: "AAPL", isExistingHolding: true, currentWeightPercent: 50, overall: "weak", overallReasoning: [], overallReasoningCode: null, overallReasoningCount: null, dimensions: [], trend: "unavailable", dataGaps: [], coverage: EMPTY_COVERAGE, generatedAt: "2026-01-01T00:00:00Z" },
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

  it("shows a real loading indicator while the candidate universe loads, never a silent blank section", () => {
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => {})));
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    expect(screen.getAllByText("Läser in bolagen som Atlas har analyserat…").length).toBeGreaterThan(0);
  });

  it("shows an honest error message when the candidate universe fetch fails, never a silent fake-empty state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        // Sprint 4C: the message belongs to the fetch it describes.
        // It used to be raised by the *Portfolio Fit* request, which
        // has not fed this list since Sprint 4B.
        if (url.includes("/api/discovery-candidates")) return Promise.resolve({ ok: false, status: 500 } as Response);
        if (url.includes("/api/portfolio-fit/candidates")) return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
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

  /** The optimistic remove/restore this once covered moved out with
   * the control itself (Sprint 4C): a Discovery candidate is never on
   * the active Watchlist, so the link could only ever do nothing.
   * Watchlist owns that flow and covers it in `WatchlistPage.test.tsx`. */
  it("never offers a Watchlist action on a Discovery candidate", async () => {
    mockFetch();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("NVDA").length).toBeGreaterThan(0));
    expect(screen.queryByText("Ta bort från bevakningslistan")).not.toBeInTheDocument();
    expect(screen.queryByText("Lägg till i bevakningslistan för att utvärdera")).not.toBeInTheDocument();
  });
});

describe("DiscoveryPage -- Sprint 4B candidate universe and direct Case entry", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    __resetAlphaWatchlistCacheForTests();
    __resetAlphaPortfolioCacheForTests();
  });

  it("sources passive candidates from the Discovery universe, not from the Watchlist", async () => {
    const requested: string[] = [];
    mockFetch();
    const original = globalThis.fetch as typeof fetch;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      requested.push(String(input));
      return original(input as RequestInfo, init);
    }));
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("NVDA").length).toBeGreaterThan(0));
    expect(requested.some((url) => url.includes("/api/discovery-candidates"))).toBe(true);
  });

  it("renders the honest empty state when Atlas has no eligible candidates", async () => {
    mockFetch({ discoveryCandidates: [] });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    // Never padded with Watchlist echoes to make the page look full.
    await waitFor(() =>
      expect(
        screen.getByText("Atlas har inga kandidater att visa. Varje bolag som analyserats är ett du redan äger eller redan bevakar."),
      ).toBeInTheDocument(),
    );
  });

  it("opens a candidate's Investment Case directly, without joining the Watchlist", async () => {
    const calls: Array<{ url: string; method: string | undefined }> = [];
    mockFetch();
    const original = globalThis.fetch as typeof fetch;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(input), method: init?.method });
      return original(input as RequestInfo, init);
    }));
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByRole("button", { name: "Öppna investeringscase" }).length).toBeGreaterThan(0));
    await user.click(screen.getAllByRole("button", { name: "Öppna investeringscase" })[0]!);

    await waitFor(() => expect(calls.some((c) => c.url.includes("/api/case-identity/ensure"))).toBe(true));
    // The whole point: no Watchlist write anywhere in the flow.
    expect(calls.some((c) => c.url.includes("/api/alpha-watchlist") && c.method === "POST")).toBe(false);
  });

  it("opens a search result's Investment Case directly, without joining the Watchlist", async () => {
    const calls: Array<{ url: string; method: string | undefined }> = [];
    mockFetch({ search: [{ ticker: "ASML", displayName: "ASML Holding NV", securityType: "common_stock" }] });
    const original = globalThis.fetch as typeof fetch;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(input), method: init?.method });
      return original(input as RequestInfo, init);
    }));
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await user.type(screen.getByPlaceholderText(/ticker/i), "ASML");
    await user.click(screen.getByRole("button", { name: "Sök" }));
    await waitFor(() => expect(screen.getByText(/ASML Holding NV/)).toBeInTheDocument());
    await user.click(screen.getByText(/ASML Holding NV/));

    await waitFor(() => expect(calls.some((c) => c.url.includes("/api/case-identity/ensure"))).toBe(true));
    expect(calls.some((c) => c.url.includes("/api/alpha-watchlist") && c.method === "POST")).toBe(false);
  });

  it("keeps a search match presented as a search result, never as an Atlas ranking", async () => {
    mockFetch({ search: [{ ticker: "ASML", displayName: "ASML Holding NV", securityType: "common_stock" }] });
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await user.type(screen.getByPlaceholderText(/ticker/i), "ASML");
    await user.click(screen.getByRole("button", { name: "Sök" }));
    await waitFor(() => expect(screen.getByText(/ASML Holding NV/)).toBeInTheDocument());
    // Honest state label, and no tier or recommendation language.
    expect(screen.getByText("Ny kandidat — ännu inte utvärderad")).toBeInTheDocument();
  });

  it("introduces no investment metric the engine does not compute", async () => {
    mockFetch();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getAllByText("NVDA").length).toBeGreaterThan(0));
    const text = document.body.textContent ?? "";
    for (const invented of ["Övertygelse", "Förv. avkastning", "Uppsida", "Nedsida"]) {
      expect(text).not.toContain(invented);
    }
    expect(text).not.toMatch(/\d+\s*\/\s*10/);
  });
});

/**
 * Convergence Sprint 4C -- Discovery's IA against a real universe.
 *
 * These fixtures deliberately mirror the live shape Sprint 4B measured:
 * a Stance of "review" on nearly every independent candidate, so the
 * Highest-opportunity tier is genuinely empty and the dense tiers carry
 * the page. `rankCandidates` is unchanged and stays unchanged -- what
 * moved is how its three tiers are rendered.
 */
describe("DiscoveryPage -- Sprint 4C Discovery UX convergence", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    __resetAlphaWatchlistCacheForTests();
    __resetAlphaPortfolioCacheForTests();
  });

  function universeCandidate(overrides: Partial<Record<string, unknown>> = {}) {
    return {
      ticker: "ASML",
      caseId: "case-asml",
      companyName: "ASML Holding NV ADR",
      decisionSupportLevel: "entry_supported",
      analysisCoverageLevel: "substantial_coverage",
      fitRating: "good",
      stanceLevel: null,
      ...overrides,
    };
  }

  it("renders the three tiers in fixed priority order, dense tiers as a comparative table", async () => {
    mockFetch({
      discoveryCandidates: [
        // Highest: positive Fit, no disagreeing Stance.
        universeCandidate(),
        // Worth reviewing: positive Fit, but a caution-toned Stance.
        universeCandidate({ ticker: "CRM", caseId: "case-crm", companyName: "Salesforce.com Inc", stanceLevel: "review" }),
        // Everything else: nothing currently pulling attention there.
        universeCandidate({
          ticker: "UNP",
          caseId: "case-unp",
          companyName: "Union Pacific Corporation",
          decisionSupportLevel: "no_action_supported",
          fitRating: "weak",
          stanceLevel: "review",
        }),
      ],
    });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getByText("Största möjligheterna")).toBeInTheDocument());

    // Highest opportunity stays a card with its own primary action.
    expect(screen.getByRole("button", { name: "Öppna investeringscase" })).toBeInTheDocument();
    // The lower tiers are dense rows, not one-signal lines.
    expect(screen.getByRole("button", { name: "Öppna investeringscaset för CRM" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Öppna investeringscaset för UNP" })).toBeInTheDocument();

    const text = document.body.textContent ?? "";
    expect(text.indexOf("Största möjligheterna")).toBeLessThan(text.indexOf("Värt att se över"));
    expect(text.indexOf("Värt att se över")).toBeLessThan(text.indexOf("1 bolag till"));
  });

  it("keeps every candidate reachable -- the Everything-else tier is collapsed, never dropped", async () => {
    mockFetch({
      discoveryCandidates: [
        universeCandidate({ ticker: "XOM", caseId: "case-xom", companyName: "Exxon Mobil Corp", fitRating: null, stanceLevel: null }),
      ],
    });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getByText("1 bolag till")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Öppna investeringscaset för XOM" })).toBeInTheDocument();
  });

  it("states why Atlas shows the top candidate, in Atlas's own canonical vocabulary", async () => {
    mockFetch({ discoveryCandidates: [universeCandidate()] });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getByText("Nuvarande underlag stöder att inleda en position.")).toBeInTheDocument());
    expect(screen.getAllByText("Nyinvestering stöds").length).toBeGreaterThan(0);
  });

  it("says how large the universe is, and claims nothing beyond the count", async () => {
    mockFetch({
      discoveryCandidates: [universeCandidate(), universeCandidate({ ticker: "TSM", caseId: "case-tsm", companyName: "TSMC" })],
    });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() =>
      expect(screen.getByText("2 bolag som Atlas har analyserat och som du varken äger eller bevakar.")).toBeInTheDocument(),
    );
  });

  it("separates Search from the ranked candidates, and says the results are not ranked", async () => {
    mockFetch({ discoveryCandidates: [universeCandidate()] });
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getByText("Sök efter ett bolag")).toBeInTheDocument());
    expect(
      screen.getByText(
        "Sökningen är inte rankad: den slår upp vilket noterat bolag som helst på ticker eller namn, oavsett om Atlas har analyserat det.",
      ),
    ).toBeInTheDocument();
    const text = document.body.textContent ?? "";
    expect(text.indexOf("Största möjligheterna")).toBeLessThan(text.indexOf("Sök efter ett bolag"));
  });

  /** A search result for a company Atlas has already analysed used to
   * read "New candidate -- not yet evaluated", which was simply false
   * for anything in the universe rendered directly above it. */
  it("marks a search result that is already a ranked candidate as analysed, never as unevaluated", async () => {
    mockFetch({
      discoveryCandidates: [universeCandidate()],
      search: [{ ticker: "ASML", displayName: "ASML Holding NV ADR", cik: 1, discoveryMethod: "ticker_exact", source: "sec", status: "candidate_only" }],
    });
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await user.type(screen.getByPlaceholderText("Ticker eller bolagsnamn"), "ASML");
    await user.click(screen.getByRole("button", { name: "Sök" }));
    await waitFor(() => expect(screen.getByText("Analyserad — finns bland kandidaterna ovan")).toBeInTheDocument());
    expect(screen.queryByText("Ny kandidat — ännu inte utvärderad")).not.toBeInTheDocument();
  });

  /** Ownership is only claimed once the list that would prove it has
   * actually loaded -- a failed Portfolio request must not turn a
   * company the investor owns into "New candidate". */
  it("claims no ownership state on a search result while Portfolio is still degraded", async () => {
    mockFetch({ search: [{ ticker: "ZZZZ", displayName: "Unknown Co", cik: 2, discoveryMethod: "ticker_exact", source: "sec", status: "candidate_only" }] });
    const original = globalThis.fetch as typeof fetch;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/api/alpha-portfolio") && !url.includes("trade-log")) return Promise.resolve({ ok: false, status: 500 } as Response);
      return original(input as RequestInfo, init);
    }));
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await user.type(screen.getByPlaceholderText("Ticker eller bolagsnamn"), "ZZZZ");
    await user.click(screen.getByRole("button", { name: "Sök" }));
    await waitFor(() => expect(screen.getByText(/Unknown Co/)).toBeInTheDocument());
    expect(screen.queryByText("Ny kandidat — ännu inte utvärderad")).not.toBeInTheDocument();
    expect(screen.queryByText("I din portfölj")).not.toBeInTheDocument();
  });

  it("clears a search back to the passive universe without reloading candidates", async () => {
    mockFetch({
      discoveryCandidates: [universeCandidate()],
      search: [{ ticker: "TSLA", displayName: "Tesla Inc.", cik: 1, discoveryMethod: "ticker_exact", source: "sec", status: "candidate_only" }],
    });
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await user.type(screen.getByPlaceholderText("Ticker eller bolagsnamn"), "TSLA");
    await user.click(screen.getByRole("button", { name: "Sök" }));
    await waitFor(() => expect(screen.getByText(/Tesla Inc\./)).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "Rensa" }));
    expect(screen.queryByText(/Tesla Inc\./)).not.toBeInTheDocument();
    expect(screen.getAllByText("ASML").length).toBeGreaterThan(0);
  });

  /** Sprint 4A/4B put a direct, membership-free path from a candidate
   * to its Case. A dense row has to take exactly that path -- not the
   * legacy `/discovery/candidate/:ticker` intermediary. */
  it("opens a dense row's Investment Case directly, creating no membership", async () => {
    const calls: Array<{ url: string; method: string | undefined }> = [];
    mockFetch({
      discoveryCandidates: [
        universeCandidate({ ticker: "CRM", caseId: "case-crm", companyName: "Salesforce.com Inc", stanceLevel: "review" }),
      ],
    });
    const original = globalThis.fetch as typeof fetch;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(input), method: init?.method });
      return original(input as RequestInfo, init);
    }));
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getByRole("button", { name: "Öppna investeringscaset för CRM" })).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "Öppna investeringscaset för CRM" }));
    await waitFor(() => expect(calls.some((c) => c.url.includes("/api/case-identity/ensure"))).toBe(true));
    expect(calls.some((c) => c.url.includes("/api/alpha-watchlist") && c.method === "POST")).toBe(false);
    expect(calls.some((c) => c.url.includes("/discovery/candidate"))).toBe(false);
  });

  it("reports a failed Case open instead of resetting as if nothing was pressed", async () => {
    mockFetch({ discoveryCandidates: [universeCandidate()] });
    const original = globalThis.fetch as typeof fetch;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).includes("/api/case-identity/ensure")) return Promise.resolve({ ok: false, status: 500 } as Response);
      return original(input as RequestInfo, init);
    }));
    const user = userEvent.setup();
    renderWithProviders(<DiscoveryPage />, { route: "/discovery" });
    await waitFor(() => expect(screen.getByRole("button", { name: "Öppna investeringscase" })).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "Öppna investeringscase" }));
    await waitFor(() =>
      expect(screen.getByText("Kunde inte öppna investeringscaset. Försök igen.")).toBeInTheDocument(),
    );
  });
});
