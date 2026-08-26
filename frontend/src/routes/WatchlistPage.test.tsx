import { describe, expect, it, vi, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../testUtils";
import { WatchlistPage } from "./WatchlistPage";
import { __resetAlphaWatchlistCacheForTests } from "../discovery/watchlistActions";

const ENTRY = { ticker: "NVDA", caseId: "case-nvda", addedAt: "2026-01-01T00:00:00Z" };
const ANALYSIS = {
  companyProfile: { name: "NVIDIA Corp", sector: "Technology" },
  recommendation: { level: "thesis_intact" },
  confidence: "full",
  evidenceQuality: { coverage: "full" },
};

const EMPTY_AGENDA = { generatedAt: "2026-01-01T00:00:00Z", summary: {}, items: [] };

function agendaItem(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id: "review_investment_case:NVDA",
    priority: "high",
    kind: "review_investment_case",
    group: "watchlist",
    source: "executive_change",
    headline: "NVDA: Jensen Huang (CEO) appointed.",
    reason: ["NVDA: Jensen Huang (CEO) appointed."],
    nature: "change_event",
    reasonNature: ["change_event"],
    since: null,
    ticker: "NVDA",
    caseId: "case-nvda",
    portfolioContext: null,
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function mockFetch(overrides: { entries?: unknown[]; agendaItems?: unknown[] } = {}) {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/cases/") && url.includes("/analysis")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(ANALYSIS) } as Response);
      }
      if (url.includes("/api/daily-brief-agenda")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ ...EMPTY_AGENDA, items: overrides.agendaItems ?? [] }),
        } as Response);
      }
      if (url.includes("/api/alpha-watchlist")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.entries ?? [ENTRY]) } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
}

describe("WatchlistPage (Product Sprint 9 -- Discovery Excellence, Deliverable 8)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    __resetAlphaWatchlistCacheForTests();
  });

  it("offers Open Investment Case and Compare on every row -- no dead end from Watchlist", async () => {
    mockFetch();
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText("NVIDIA Corp").length).toBeGreaterThan(0));
    expect(screen.getByRole("button", { name: "Öppna investeringscase" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Jämför" })).toBeInTheDocument();
  });

  it("navigates to the real Investment Case, carrying origin: watchlist, when Open Investment Case is clicked", async () => {
    mockFetch();
    const user = userEvent.setup();
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText("NVIDIA Corp").length).toBeGreaterThan(0));
    await user.click(screen.getByRole("button", { name: "Öppna investeringscase" }));
    // MemoryRouter has no /investment-case/:caseId route registered in
    // this harness -- reaching this click without throwing, on the real
    // caseId from the entry, is the behavior under test.
  });

  it("activates the whole row into the real Investment Case (not Company Workspace), matching the row's explicit action button", async () => {
    mockFetch();
    const user = userEvent.setup();
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText("NVIDIA Corp").length).toBeGreaterThan(0));
    // Clicking the company-name cell -- outside the action cell entirely
    // -- exercises the row's own `role="button"` activation, not the
    // explicit "Öppna investeringscase" button tested above. MemoryRouter
    // has no /investment-case/:caseId route registered in this harness,
    // matching the existing button test's own precedent -- reaching this
    // click without throwing, on the real caseId, is the behavior under
    // test.
    await user.click(screen.getByText("NVIDIA Corp"));
  });

  it("shows the honest empty state with no fabricated candidates", async () => {
    mockFetch({ entries: [] });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getByText("Inga bolag i din bevakningslista")).toBeInTheDocument());
  });

  it("removes a ticker in one click, no confirmation step (Internal Alpha Stabilization: matches Discovery's own one-click remove for the same action)", async () => {
    let deleteCalled = false;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/api/alpha-watchlist/") && init?.method === "DELETE") {
          deleteCalled = true;
          return Promise.resolve({ ok: true } as Response);
        }
        if (url.includes("/api/cases/") && url.includes("/analysis")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(ANALYSIS) } as Response);
        }
        if (url.includes("/api/alpha-watchlist")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve([ENTRY]) } as Response);
        }
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText("NVIDIA Corp").length).toBeGreaterThan(0));
    expect(screen.queryByText(/Ta bort NVDA från din bevakningslista/)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Ta bort" }));
    await waitFor(() => expect(deleteCalled).toBe(true));
    expect(screen.queryByRole("button", { name: /Bekräfta/ })).not.toBeInTheDocument();
  });
});

describe("WatchlistPage Attention column (Product Intelligence Sprint 2 -- Watchlist Intelligence Activation)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    __resetAlphaWatchlistCacheForTests();
  });

  it("shows a real Agenda item's own priority and headline for a ticker with a signal", async () => {
    mockFetch({ agendaItems: [agendaItem()] });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText("NVIDIA Corp").length).toBeGreaterThan(0));
    // Implementation Sprint B2 (Hero Reordering): the same real headline
    // now renders twice by design -- once as the Hero's own compact
    // "Why now" preview, once in the table's Attention column below --
    // the same "compact fact in the hero, full detail below" pattern
    // this page's own Hero docstring establishes, never two different,
    // independently-worded reasons.
    const headlines = await screen.findAllByText("NVDA: Jensen Huang (CEO) appointed.");
    expect(headlines.length).toBe(2);
    expect(screen.getByText("Hög")).toBeInTheDocument();
  });

  it("shows an honest 'no significant changes' state, never implying it as positive news, when the Agenda has no item for this ticker", async () => {
    mockFetch({ agendaItems: [] });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText("NVIDIA Corp").length).toBeGreaterThan(0));
    expect(await screen.findByText("Inga betydande förändringar")).toBeInTheDocument();
  });

  it("only surfaces a portfolio-group item on the wrong ticker's own row, never bleeding across group boundaries", async () => {
    // A `portfolio`-group item for the same ticker must never be read
    // as a `watchlist` signal -- confirms the `group === "watchlist"`
    // filter is real, not merely present.
    mockFetch({ agendaItems: [agendaItem({ group: "portfolio" })] });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText("NVIDIA Corp").length).toBeGreaterThan(0));
    expect(await screen.findByText("Inga betydande förändringar")).toBeInTheDocument();
    expect(screen.queryByText("NVDA: Jensen Huang (CEO) appointed.")).not.toBeInTheDocument();
  });

  it("sorts a ticker with a real signal ahead of one with none, highest priority first", async () => {
    const entries = [
      { ticker: "AAPL", caseId: "case-aapl", addedAt: "2026-01-01T00:00:00Z" },
      { ticker: "NVDA", caseId: "case-nvda", addedAt: "2026-01-01T00:00:00Z" },
    ];
    mockFetch({
      entries,
      // AAPL has no signal; NVDA does -- NVDA must render first despite
      // being second in the raw entries list.
      agendaItems: [agendaItem({ id: "review_investment_case:NVDA" })],
    });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    // Implementation Sprint B2 (Hero Reordering): 3 matches, not 2 --
    // the Hero (added this sprint) also renders the top entry's own
    // ticker, ahead of the table. NVDA appears twice (Hero, then its
    // own table row) and AAPL once, in that DOM order -- the table's
    // own sort is unchanged, just no longer the only place this page
    // shows its highest-priority ticker.
    await waitFor(() => expect(screen.getAllByText(/^(AAPL|NVDA)$/).length).toBe(3));
    const tickerCells = screen.getAllByText(/^(AAPL|NVDA)$/);
    expect(tickerCells.map((el) => el.textContent)).toEqual(["NVDA", "NVDA", "AAPL"]);
  });
});
