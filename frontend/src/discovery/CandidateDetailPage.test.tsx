import { describe, expect, it, vi, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../testUtils";
import { CandidateDetailPage } from "./CandidateDetailPage";

const EMPTY_COVERAGE = {
  dimensions: [],
  overallCoverage: "no_coverage",
  overallConfidence: "very_limited",
  missingDimensions: [],
  notApplicableDimensions: [],
  reasoning: [],
};

function assessment(ticker: string, caseId: string) {
  return {
    caseId,
    ticker,
    isExistingHolding: false,
    currentWeightPercent: null,
    overall: "good",
    overallReasoning: ["More dimensions rated Good/Excellent than Weak/Poor."],
    dimensions: [{ kind: "business", rating: "good", reasoning: ["Strong business."], unavailableReason: null }],
    trend: "unavailable",
    dataGaps: [],
    coverage: EMPTY_COVERAGE,
    generatedAt: "2026-01-01T00:00:00Z",
  };
}

function mockFetch(opts: { fit?: unknown; fitStatus?: number; watchlist?: unknown[]; holdings?: unknown[]; holdingsFit?: unknown[]; agenda?: unknown } = {}) {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/portfolio-fit/ticker/")) {
        const status = opts.fitStatus ?? 200;
        return Promise.resolve({ ok: status !== 404, status, json: () => Promise.resolve(opts.fit ?? null) } as Response);
      }
      if (url.includes("/api/alpha-watchlist")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(opts.watchlist ?? []) } as Response);
      }
      if (url.includes("/api/alpha-portfolio")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ exists: true, holdings: opts.holdings ?? [] }) } as Response);
      }
      if (url.includes("/api/portfolio-fit/holdings")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(opts.holdingsFit ?? []) } as Response);
      }
      if (url.includes("/api/daily-brief-agenda")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve(
              opts.agenda ?? {
                generatedAt: "2026-01-01T00:00:00Z",
                summary: { holdingsCount: 0, criticalCount: 0, highCount: 0, watchlistOpportunityCount: 0, cashWeightPercent: null, concentrationLevel: null },
                items: [],
              },
            ),
        } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
}

describe("CandidateDetailPage", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the candidate card with a real Portfolio Fit assessment when one exists", async () => {
    mockFetch({ fit: assessment("NVDA", "case-nvda"), watchlist: [{ ticker: "NVDA", caseId: "case-nvda", addedAt: "2026-01-01T00:00:00Z" }] });
    renderWithProviders(<CandidateDetailPage />, { route: "/discovery/candidate/NVDA", path: "/discovery/candidate/:ticker" });

    await waitFor(() => expect(screen.getByText("NVDA")).toBeInTheDocument());
    expect(screen.getAllByText("Bra passform").length).toBeGreaterThan(0);
    expect(screen.getByText("På din bevakningslista")).toBeInTheDocument();
  });

  it("shows the honest no-Case gap and an Add-to-Watchlist action for a candidate with no Case yet", async () => {
    mockFetch({ fitStatus: 404, watchlist: [], holdings: [] });
    renderWithProviders(<CandidateDetailPage />, { route: "/discovery/candidate/ZZZZ", path: "/discovery/candidate/:ticker" });

    await waitFor(() =>
      expect(screen.getByText("Bygg investeringscaset innan Atlas kan utvärdera portföljpassform.")).toBeInTheDocument(),
    );
    expect(screen.getByRole("button", { name: "Lägg till i bevakningslistan för att utvärdera" })).toBeInTheDocument();
  });

  it("has a working back link to Discovery", async () => {
    mockFetch({ fitStatus: 404, watchlist: [], holdings: [] });
    renderWithProviders(<CandidateDetailPage />, { route: "/discovery/candidate/ZZZZ", path: "/discovery/candidate/:ticker" });

    await waitFor(() => expect(screen.getByRole("link", { name: "← Tillbaka till Discovery" })).toHaveAttribute("href", "/discovery"));
  });

  it("adds the ticker to the Watchlist and re-evaluates Portfolio Fit when the action is used", async () => {
    let fitCallCount = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/api/portfolio-fit/ticker/")) {
          fitCallCount += 1;
          const found = fitCallCount > 1;
          return Promise.resolve({
            ok: found,
            status: found ? 200 : 404,
            json: () => Promise.resolve(found ? assessment("ZZZZ", "case-zzzz") : null),
          } as Response);
        }
        if (url.includes("/api/alpha-watchlist") && init?.method === "POST") {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ ticker: "ZZZZ", caseId: "case-zzzz", addedAt: "2026-01-01T00:00:00Z" }),
          } as Response);
        }
        if (url.includes("/api/alpha-watchlist")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
        }
        if (url.includes("/api/alpha-portfolio")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve({ exists: true, holdings: [] }) } as Response);
        }
        if (url.includes("/api/portfolio-fit/holdings")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
        }
        if (url.includes("/api/daily-brief-agenda")) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ generatedAt: "2026-01-01T00:00:00Z", summary: { holdingsCount: 0, criticalCount: 0, highCount: 0, watchlistOpportunityCount: 0, cashWeightPercent: null, concentrationLevel: null }, items: [] }),
          } as Response);
        }
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(<CandidateDetailPage />, { route: "/discovery/candidate/ZZZZ", path: "/discovery/candidate/:ticker" });

    await waitFor(() => expect(screen.getByRole("button", { name: "Lägg till i bevakningslistan för att utvärdera" })).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "Lägg till i bevakningslistan för att utvärdera" }));

    await waitFor(() => expect(screen.getAllByText("Bra passform").length).toBeGreaterThan(0));
  });

  it("shows the real Daily Brief Agenda headline as the reason Atlas is showing this candidate (Deliverable 3)", async () => {
    mockFetch({
      fit: assessment("NVDA", "case-nvda"),
      watchlist: [{ ticker: "NVDA", caseId: "case-nvda", addedAt: "2026-01-01T00:00:00Z" }],
      agenda: {
        generatedAt: "2026-01-01T00:00:00Z",
        summary: { holdingsCount: 0, criticalCount: 0, highCount: 0, watchlistOpportunityCount: 1, cashWeightPercent: null, concentrationLevel: null },
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
    renderWithProviders(<CandidateDetailPage />, { route: "/discovery/candidate/NVDA", path: "/discovery/candidate/:ticker" });
    await waitFor(() => expect(screen.getByText("NVDA: Portfolio Fit is improving")).toBeInTheDocument());
  });
});
