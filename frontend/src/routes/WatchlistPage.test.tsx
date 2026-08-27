import { describe, expect, it, vi, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../testUtils";
import { WatchlistPage } from "./WatchlistPage";
import { __resetAlphaWatchlistCacheForTests } from "../discovery/watchlistActions";
import { __resetAlphaPortfolioCacheForTests } from "../portfolio/alphaPortfolioData";

const ENTRY = { ticker: "NVDA", caseId: "case-nvda", addedAt: "2026-01-01T00:00:00Z" };
const IDENTITY = { companyProfile: { name: "NVIDIA Corp", sector: "Technology" } };
const EMPTY_PORTFOLIO = { exists: true, holdings: [] };

function stance(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    level: "maintain",
    reasoning: [],
    supportingSignals: [],
    limitingSignals: [],
    confidence: "moderate",
    missingInformation: [],
    ...overrides,
  };
}

function mockFetch(
  overrides: { entries?: unknown[]; stance?: unknown; identity?: unknown; portfolio?: unknown } = {},
) {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/cases/") && url.includes("/analysis")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.identity ?? IDENTITY) } as Response);
      }
      if (url.includes("/api/stance/case/")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.stance ?? stance()) } as Response);
      }
      if (url.includes("/api/alpha-watchlist")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.entries ?? [ENTRY]) } as Response);
      }
      if (url.includes("/api/alpha-portfolio") && !url.includes("trade-log") && !url.includes("status") && !url.includes("intelligence")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.portfolio ?? EMPTY_PORTFOLIO) } as Response);
      }
      if (url.includes("/api/monitoring/status")) {
        return Promise.resolve({ ok: false, status: 500 } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
}

describe("WatchlistPage (Watchlist Doctrine, 2026-08-27 -- Monitoring Workspace)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    __resetAlphaWatchlistCacheForTests();
    __resetAlphaPortfolioCacheForTests();
  });

  it("never fetches the Daily Brief Agenda at all -- Phase 1 removes every Agenda-driven concept from this page", async () => {
    const requestedUrls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        requestedUrls.push(url);
        if (url.includes("/api/cases/") && url.includes("/analysis")) return Promise.resolve({ ok: true, json: () => Promise.resolve(IDENTITY) } as Response);
        if (url.includes("/api/stance/case/")) return Promise.resolve({ ok: true, json: () => Promise.resolve(stance()) } as Response);
        if (url.includes("/api/alpha-watchlist")) return Promise.resolve({ ok: true, json: () => Promise.resolve([ENTRY]) } as Response);
        if (url.includes("/api/alpha-portfolio") && !url.includes("trade-log")) return Promise.resolve({ ok: true, json: () => Promise.resolve(EMPTY_PORTFOLIO) } as Response);
        if (url.includes("/api/monitoring/status")) return Promise.resolve({ ok: false, status: 500 } as Response);
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText("NVIDIA Corp").length).toBeGreaterThan(0));
    expect(requestedUrls.some((url) => url.includes("/api/daily-brief-agenda"))).toBe(false);
    expect(screen.queryByText("Why now")).not.toBeInTheDocument();
  });

  it("reframes the added date as 'Monitoring since' -- Phase 3", async () => {
    mockFetch();
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getByText("Bevakas sedan")).toBeInTheDocument());
    expect(screen.getByText(/^Sedan /)).toBeInTheDocument();
  });

  it("surfaces a real, already-computed missing-information gap as a 'Waiting for' line -- Phase 4", async () => {
    mockFetch({ stance: stance({ missingInformation: ["thesis_risk"] }) });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getByText(/Väntar på:/)).toBeInTheDocument());
  });

  it("states a calm, honest confirmation -- never a blank cell -- when nothing is missing", async () => {
    mockFetch({ stance: stance({ missingInformation: [] }) });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getByText("Atlas har det som behövs för att utvärdera det här.")).toBeInTheDocument());
  });

  it("never fabricates missing information when Stance has none to report", async () => {
    mockFetch({ stance: stance({ missingInformation: [] }) });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getByText("Atlas har det som behövs för att utvärdera det här.")).toBeInTheDocument());
    expect(screen.queryByText(/Väntar på:/)).not.toBeInTheDocument();
  });

  it("shows exactly one current-view Stance badge per row, not the old three-badge rating cluster -- Phase 5", async () => {
    mockFetch();
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText("NVIDIA Corp").length).toBeGreaterThan(0));
    expect(screen.getByText("Synen är oförändrad")).toBeInTheDocument();
    expect(screen.queryByText(/Investering \d/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Portfölj \d/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Underlag \d/)).not.toBeInTheDocument();
  });

  it("clearly distinguishes a held-and-watchlisted company -- Phase 8", async () => {
    mockFetch({ portfolio: { exists: true, holdings: [{ ticker: "NVDA", caseId: "case-nvda" }] } });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getByText("Även i din portfölj")).toBeInTheDocument());
  });

  it("never labels a company not currently held", async () => {
    mockFetch({ portfolio: EMPTY_PORTFOLIO });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText("NVIDIA Corp").length).toBeGreaterThan(0));
    expect(screen.queryByText("Även i din portfölj")).not.toBeInTheDocument();
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
  });

  it("activates the whole row into the real Investment Case", async () => {
    mockFetch();
    const user = userEvent.setup();
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText("NVIDIA Corp").length).toBeGreaterThan(0));
    await user.click(screen.getByText("NVIDIA Corp"));
  });

  it("shows the honest empty state with no fabricated candidates", async () => {
    mockFetch({ entries: [] });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getByText("Inga bolag i din bevakningslista")).toBeInTheDocument());
  });

  it("removes a ticker in one click, no confirmation step", async () => {
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
          return Promise.resolve({ ok: true, json: () => Promise.resolve(IDENTITY) } as Response);
        }
        if (url.includes("/api/stance/case/")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(stance()) } as Response);
        }
        if (url.includes("/api/alpha-watchlist")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve([ENTRY]) } as Response);
        }
        if (url.includes("/api/alpha-portfolio") && !url.includes("trade-log")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(EMPTY_PORTFOLIO) } as Response);
        }
        if (url.includes("/api/monitoring/status")) return Promise.resolve({ ok: false, status: 500 } as Response);
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText("NVIDIA Corp").length).toBeGreaterThan(0));
    await user.click(screen.getByRole("button", { name: "Ta bort" }));
    await waitFor(() => expect(deleteCalled).toBe(true));
    expect(screen.queryByRole("button", { name: /Bekräfta/ })).not.toBeInTheDocument();
  });

  it("sorts entries alphabetically by ticker, never implying an unstated urgency ranking", async () => {
    const entries = [
      { ticker: "NVDA", caseId: "case-nvda", addedAt: "2026-01-01T00:00:00Z" },
      { ticker: "AAPL", caseId: "case-aapl", addedAt: "2026-01-01T00:00:00Z" },
    ];
    mockFetch({ entries });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText(/^(AAPL|NVDA)$/).length).toBe(2));
    const tickerCells = screen.getAllByText(/^(AAPL|NVDA)$/);
    expect(tickerCells.map((el) => el.textContent)).toEqual(["AAPL", "NVDA"]);
  });
});
