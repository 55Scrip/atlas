import { describe, expect, it, vi, afterEach } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../testUtils";
import { WatchlistPage } from "./WatchlistPage";
import { __resetAlphaWatchlistCacheForTests } from "../discovery/watchlistActions";
import { __resetAlphaPortfolioCacheForTests } from "../portfolio/alphaPortfolioData";

const ENTRY = { ticker: "NVDA", caseId: "case-nvda", addedAt: "2026-01-01T00:00:00Z" };
const SUMMARY = {
  ticker: "NVDA",
  caseId: "case-nvda",
  addedAt: "2026-01-01T00:00:00Z",
  companyName: "NVIDIA Corp",
  sector: "Technology",
  decisionSupportLevel: "thesis_intact",
  analysisCoverageLevel: "substantial_coverage",
};
const EMPTY_PORTFOLIO = { exists: true, holdings: [] };
const FIT = { caseId: "case-nvda", ticker: "NVDA", isExistingHolding: false, currentWeightPercent: null, overall: "good", overallReasoning: [], dimensions: [], trend: "unchanged", dataGaps: [] };

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
  overrides: {
    entries?: unknown[];
    stance?: unknown;
    summary?: unknown[];
    portfolio?: unknown;
    fit?: unknown;
    summaryOk?: boolean;
    fitOk?: boolean;
  } = {},
) {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      // Deliberately unhandled: the heavy `/cases/{id}/analysis`
      // endpoint must never be reached by ordinary Watchlist
      // composition, so this stub rejects it like any other unexpected
      // request.
      if (url.includes("/api/alpha-watchlist/summary")) {
        if (overrides.summaryOk === false) return Promise.resolve({ ok: false, status: 500 } as Response);
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.summary ?? [SUMMARY]) } as Response);
      }
      if (url.includes("/api/stance/case/")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.stance ?? stance()) } as Response);
      }
      if (url.includes("/api/portfolio-fit/case/")) {
        if (overrides.fitOk === false) return Promise.resolve({ ok: false, status: 404 } as Response);
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.fit ?? FIT) } as Response);
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
        if (url.includes("/api/alpha-watchlist/summary")) return Promise.resolve({ ok: true, json: () => Promise.resolve([SUMMARY]) } as Response);
        if (url.includes("/api/stance/case/")) return Promise.resolve({ ok: true, json: () => Promise.resolve(stance()) } as Response);
        if (url.includes("/api/portfolio-fit/case/")) return Promise.resolve({ ok: true, json: () => Promise.resolve(FIT) } as Response);
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

  it("keeps 'Monitoring since' as context inside the prospect cell, not as its own column", async () => {
    mockFetch();
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    // The fact survives; the column it used to occupy does not -- it is
    // context, not something prospects are compared on.
    await waitFor(() => expect(screen.getByText(/^Sedan /)).toBeInTheDocument());
    expect(screen.queryByRole("columnheader", { name: "Bevakas sedan" })).not.toBeInTheDocument();
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

  it("keeps Compare on every row and makes the row itself the way into the case", async () => {
    mockFetch();
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText("NVIDIA Corp").length).toBeGreaterThan(0));
    expect(screen.getByRole("button", { name: "Jämför" })).toBeInTheDocument();
    // The separate "Open Investment Case" button was a second copy of
    // what activating the row already does, taking a third of the
    // action column. The row remains a keyboard-operable button.
    expect(screen.queryByRole("button", { name: "Öppna investeringscase" })).not.toBeInTheDocument();
    const row = screen.getByRole("button", { name: "Öppna investeringscase för NVDA" });
    expect(row.tagName).toBe("TR");
    expect(row).toHaveAttribute("tabIndex", "0");
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
        if (url.includes("/api/alpha-watchlist/summary")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve([SUMMARY]) } as Response);
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

  it("names the canonical decision state exactly as Portfolio and the Investment Case do", async () => {
    // Convergence Sprint 3B. `thesis_intact` reads "Tesen kvarstår"
    // everywhere. It used to read "Behåll" here, because this column
    // rendered the Investment Decision layer's `DecisionAction` -- a
    // pure 1:1 relabelling of the same canonical level -- through its
    // own translation bank.
    mockFetch({ summary: [{ ...SUMMARY, decisionSupportLevel: "thesis_intact" }] });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    const row = within((await screen.findByRole("button", { name: "Öppna investeringscase för NVDA" })) as HTMLElement);
    expect(row.getByText("Tesen kvarstår")).toBeInTheDocument();
    for (const actionWord of ["Behåll", "Minska", "Inget beslut ännu", "Vänta"]) {
      expect(row.queryByText(actionWord)).not.toBeInTheDocument();
    }
  });

  it("keeps the decision and the current view as separate, separately labelled columns", async () => {
    mockFetch({
      summary: [{ ...SUMMARY, decisionSupportLevel: "insufficient_evidence" }],
      stance: stance({ level: "maintain" }),
    });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    const row = within((await screen.findByRole("button", { name: "Öppna investeringscase för NVDA" })) as HTMLElement);
    // Two different concepts. Neither is collapsed into the other, and
    // each sits under a header that says which one it is.
    expect(row.getByText("Vet inte än")).toBeInTheDocument();
    expect(row.getByText("Synen är oförändrad")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Atlas beslut" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Nuvarande syn" })).toBeInTheDocument();
  });

  it("shows Fit only from the canonical Portfolio Fit verdict", async () => {
    mockFetch({ fit: { ...FIT, overall: "good" } });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    const row = within((await screen.findByRole("button", { name: "Öppna investeringscase för NVDA" })) as HTMLElement);
    expect(row.getByText("Bra passform")).toBeInTheDocument();
  });

  it("shows Fit's own unavailable rating rather than inventing a neutral one", async () => {
    mockFetch({ fit: { ...FIT, overall: "unavailable" } });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    const row = within((await screen.findByRole("button", { name: "Öppna investeringscase för NVDA" })) as HTMLElement);
    expect(row.getByText("Inte tillgängligt än")).toBeInTheDocument();
    expect(row.queryByText("Neutral passform")).not.toBeInTheDocument();
  });

  it("renders an unreachable signal as honestly unknown, never as a mediocre verdict", async () => {
    mockFetch({ summaryOk: false, fitOk: false });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    const row = within((await screen.findByRole("button", { name: "Öppna investeringscase för NVDA" })) as HTMLElement);
    await waitFor(() => expect(row.getAllByText("Ej bedömt").length).toBeGreaterThan(0));
    expect(row.queryByText("Neutral passform")).not.toBeInTheDocument();
    expect(row.queryByText("Vet inte än")).not.toBeInTheDocument();
  });

  it("introduces no Figma concept the engine does not compute", async () => {
    mockFetch();
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await screen.findByRole("button", { name: "Öppna investeringscase för NVDA" });
    const table = document.querySelector("table")!;
    const text = table.textContent ?? "";
    // No conviction: the field of that name measures analysis support,
    // not belief in the thesis. No probability-weighted return exists
    // anywhere in the engine, so no expected return, upside or
    // downside. No permanent-capital-loss risk model exists either.
    for (const forbidden of ["Övertygelse", "Förv. avkastning", "Uppsida", "Nedsida"]) {
      expect(text).not.toContain(forbidden);
    }
    // ...and no composite score standing in for any of them.
    expect(text).not.toMatch(/\d+\s*\/\s*10/);
    expect(text).not.toMatch(/(Investering|Poäng)\s\d/);
  });

  it("never calls the heavy case-analysis endpoint to compose the list", async () => {
    // Convergence Sprint 3B, Phase P. `/cases/{id}/analysis` depends on
    // the Alpha Vantage price provider, the quota tracker and the price
    // refresh coordinator, writes an evidence snapshot, and can
    // schedule a background price refresh. Watchlist called it once per
    // entry, for a company name.
    const requested: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        requested.push(url);
        if (url.includes("/api/alpha-watchlist/summary")) return Promise.resolve({ ok: true, json: () => Promise.resolve([SUMMARY]) } as Response);
        if (url.includes("/api/stance/case/")) return Promise.resolve({ ok: true, json: () => Promise.resolve(stance()) } as Response);
        if (url.includes("/api/portfolio-fit/case/")) return Promise.resolve({ ok: true, json: () => Promise.resolve(FIT) } as Response);
        if (url.includes("/api/alpha-watchlist")) return Promise.resolve({ ok: true, json: () => Promise.resolve([ENTRY]) } as Response);
        if (url.includes("/api/alpha-portfolio") && !url.includes("trade-log")) return Promise.resolve({ ok: true, json: () => Promise.resolve(EMPTY_PORTFOLIO) } as Response);
        if (url.includes("/api/monitoring/status")) return Promise.resolve({ ok: false, status: 500 } as Response);
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText("NVIDIA Corp").length).toBeGreaterThan(0));
    expect(requested.some((url) => url.includes("/analysis"))).toBe(false);
    // Positive control: the identity it needed did arrive, from the
    // lightweight summary -- so the assertion above is not passing
    // because nothing was fetched at all.
    expect(requested.some((url) => url.includes("/api/alpha-watchlist/summary"))).toBe(true);
  });

  it("composes the whole list from one summary request, not one per entry", async () => {
    const requested: string[] = [];
    const entries = [
      { ticker: "NVDA", caseId: "case-nvda", addedAt: "2026-01-01T00:00:00Z" },
      { ticker: "AAPL", caseId: "case-aapl", addedAt: "2026-01-01T00:00:00Z" },
      { ticker: "MSFT", caseId: "case-msft", addedAt: "2026-01-01T00:00:00Z" },
    ];
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        requested.push(url);
        if (url.includes("/api/alpha-watchlist/summary")) return Promise.resolve({ ok: true, json: () => Promise.resolve(entries.map((e) => ({ ...SUMMARY, ...e, companyName: `${e.ticker} Inc` }))) } as Response);
        if (url.includes("/api/stance/case/")) return Promise.resolve({ ok: true, json: () => Promise.resolve(stance()) } as Response);
        if (url.includes("/api/portfolio-fit/case/")) return Promise.resolve({ ok: true, json: () => Promise.resolve(FIT) } as Response);
        if (url.includes("/api/alpha-watchlist")) return Promise.resolve({ ok: true, json: () => Promise.resolve(entries) } as Response);
        if (url.includes("/api/alpha-portfolio") && !url.includes("trade-log")) return Promise.resolve({ ok: true, json: () => Promise.resolve(EMPTY_PORTFOLIO) } as Response);
        if (url.includes("/api/monitoring/status")) return Promise.resolve({ ok: false, status: 500 } as Response);
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText("NVDA Inc").length).toBeGreaterThan(0));
    expect(requested.filter((url) => url.includes("/api/alpha-watchlist/summary"))).toHaveLength(1);
  });

  it("shows analysis depth so an unevaluated prospect is not read as an unconvincing one", async () => {
    mockFetch({
      summary: [{ ...SUMMARY, decisionSupportLevel: "insufficient_evidence", analysisCoverageLevel: "no_coverage" }],
    });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    const row = within((await screen.findByRole("button", { name: "Öppna investeringscase för NVDA" })) as HTMLElement);
    expect(row.getByText("Vet inte än")).toBeInTheDocument();
    expect(row.getByText("Inte utvärderat")).toBeInTheDocument();
  });

  it("renders an unknown state honestly when the summary cannot be reached", async () => {
    mockFetch({ summaryOk: false });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    const row = within((await screen.findByRole("button", { name: "Öppna investeringscase för NVDA" })) as HTMLElement);
    await waitFor(() => expect(row.getAllByText("Ej bedömt").length).toBeGreaterThan(0));
    // The ticker still identifies the row (as both name-fallback and
    // ticker); no invented company name appears.
    expect(row.getAllByText("NVDA").length).toBeGreaterThan(0);
    expect(row.queryByText("NVIDIA Corp")).not.toBeInTheDocument();
  });

  it("sorts entries alphabetically by ticker, never implying an unstated urgency ranking", async () => {
    const entries = [
      { ticker: "NVDA", caseId: "case-nvda", addedAt: "2026-01-01T00:00:00Z" },
      { ticker: "AAPL", caseId: "case-aapl", addedAt: "2026-01-01T00:00:00Z" },
    ];
    mockFetch({
      entries,
      summary: [SUMMARY, { ...SUMMARY, ticker: "AAPL", caseId: "case-aapl", companyName: "Apple Inc" }],
    });
    renderWithProviders(<WatchlistPage />, { route: "/watchlist" });
    await waitFor(() => expect(screen.getAllByText(/^(AAPL|NVDA)$/).length).toBe(2));
    const tickerCells = screen.getAllByText(/^(AAPL|NVDA)$/);
    expect(tickerCells.map((el) => el.textContent)).toEqual(["AAPL", "NVDA"]);
  });
});
