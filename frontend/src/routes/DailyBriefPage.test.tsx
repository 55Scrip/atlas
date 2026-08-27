import { describe, expect, it, vi, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "../testUtils";
import { DailyBriefPage } from "./DailyBriefPage";

function agendaItem(overrides: Record<string, unknown> = {}) {
  return {
    id: "evaluate_case_condition:AAPL",
    priority: "critical",
    kind: "evaluate_case_condition",
    group: "portfolio",
    source: "case_condition",
    headline: "AAPL: China revenue declines (satisfied)",
    reason: ["AAPL: China revenue declines (satisfied)"],
    ticker: "AAPL",
    caseId: "case-aapl",
    portfolioContext: null,
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function agendaResponse(overrides: Record<string, unknown> = {}) {
  return {
    generatedAt: "2026-01-01T09:00:00Z",
    summary: {
      holdingsCount: 3,
      criticalCount: 1,
      highCount: 0,
      watchlistOpportunityCount: 0,
      cashWeightPercent: 5.0,
      concentrationLevel: "Elevated",
    },
    items: [agendaItem()],
    ...overrides,
  };
}

function changeGroup(overrides: Record<string, unknown> = {}) {
  return {
    ticker: "NVDA",
    primary: {
      id: "change-nvda-1",
      ticker: "NVDA",
      caseId: "case-nvda",
      reasonCode: "investment_decision_transition",
      value: "reduce",
      secondaryValue: "hold",
      label: null,
      headline: "NVDA: Decision changed from Hold to Reduce.",
      detectedAt: "2026-08-27T08:00:00Z",
      seenAt: null,
    },
    additionalCount: 0,
    isNew: true,
    ...overrides,
  };
}

/** `lastViewedAt: null` means a genuine first-ever visit (Phase 6);
 * pass an ISO string for the "real, prior visit" scenarios. */
function mockFetch(options: {
  agenda?: unknown;
  openDrafts?: unknown[];
  lastViewedAt?: string | null;
  changeGroups?: unknown[];
}) {
  const { agenda = agendaResponse(), openDrafts = [], lastViewedAt = "2026-08-26T09:00:00Z", changeGroups = [] } = options;
  const markSeenCalls: unknown[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/api/daily-brief-change-log/mark-seen")) {
        markSeenCalls.push(init?.body);
        return Promise.resolve({ ok: true, json: () => Promise.resolve(changeGroups) } as Response);
      }
      if (url.includes("/api/daily-brief-change-log")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(changeGroups) } as Response);
      }
      if (url.includes("/api/daily-brief/view-state/mark-viewed")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ lastViewedAt: "2026-08-27T09:00:00Z" }) } as Response);
      }
      if (url.includes("/api/daily-brief/view-state")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ lastViewedAt }) } as Response);
      }
      if (url.includes("/api/daily-brief-agenda")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(agenda) } as Response);
      }
      if (url.includes("/api/decision-drafts/daily-brief-summary")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(openDrafts) } as Response);
      }
      if (url.includes("/api/monitoring/status")) {
        return Promise.resolve({ ok: false, status: 500 } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
  return { markSeenCalls };
}

describe("DailyBriefPage (Daily Brief 2.0 -- Since your last visit)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the calm onboarding state on a genuine first-ever visit, never a raw change count (Phase 6)", async () => {
    mockFetch({ lastViewedAt: null });
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() =>
      expect(
        screen.getByText("Atlas har slutfört sin första genomgång. Inga förändringar har skett sedan din portfölj analyserades."),
      ).toBeInTheDocument(),
    );
  });

  it("shows the honest quiet state on a real return visit with no eligible changes", async () => {
    mockFetch({ lastViewedAt: "2026-08-26T09:00:00Z", changeGroups: [] });
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Allt är under kontroll. Inget har förändrats sedan ditt senaste besök.")).toBeInTheDocument());
  });

  it("renders a real change group with its own synthesized sentence and a NEW label", async () => {
    mockFetch({ changeGroups: [changeGroup()] });
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("NVDA")).toBeInTheDocument());
    expect(screen.getByText("Rekommendationen ändrades från Behåll till Minska.")).toBeInTheDocument();
    expect(screen.getByText("Nytt")).toBeInTheDocument();
  });

  it("never shows the NEW label for a change already marked seen", async () => {
    mockFetch({ changeGroups: [changeGroup({ isNew: false, primary: { ...changeGroup().primary as object, seenAt: "2026-08-27T08:30:00Z" } })] });
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("NVDA")).toBeInTheDocument());
    expect(screen.queryByText("Nytt")).not.toBeInTheDocument();
  });

  it("collapses more than 3 change groups behind one disclosure, never dropping any", async () => {
    mockFetch({
      changeGroups: [
        changeGroup({ ticker: "AAA", primary: { ...changeGroup().primary as object, id: "a", ticker: "AAA", caseId: "case-aaa" } }),
        changeGroup({ ticker: "BBB", primary: { ...changeGroup().primary as object, id: "b", ticker: "BBB", caseId: "case-bbb" } }),
        changeGroup({ ticker: "CCC", primary: { ...changeGroup().primary as object, id: "c", ticker: "CCC", caseId: "case-ccc" } }),
        changeGroup({ ticker: "DDD", primary: { ...changeGroup().primary as object, id: "d", ticker: "DDD", caseId: "case-ddd" } }),
      ],
    });
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("AAA")).toBeInTheDocument());
    // A native <details> keeps its children in the DOM while collapsed
    // (only hidden visually) -- "1 more item" is the real signal that
    // DDD is behind a disclosure, not absent from the page entirely.
    expect(screen.getByText("1 punkt till")).toBeInTheDocument();
    expect(screen.getByText("DDD")).toBeInTheDocument();
  });

  it("shows a 'more updates' link when a company has more than one real eligible change (Phase 10)", async () => {
    mockFetch({ changeGroups: [changeGroup({ additionalCount: 2 })] });
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("+2 uppdateringar till för NVDA →")).toBeInTheDocument());
  });

  it("navigates to the Investment Case when its card is opened, without a second mark-seen call of its own (RC-3, Phase 4)", async () => {
    // Marking a change SEEN moved to InvestmentCasePage itself (the one
    // real convergence point for every navigation path into a case) --
    // this card now only navigates.
    const { markSeenCalls } = mockFetch({ changeGroups: [changeGroup()] });
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("NVDA")).toBeInTheDocument());
    screen.getByText("Öppna investeringscase →").click();
    expect(markSeenCalls.length).toBe(0);
  });

  it("always shows the calm 'Atlas is watching today' fallback -- no scheduled-catalyst data source exists (documented gap)", async () => {
    mockFetch({});
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() =>
      expect(screen.getByText("Idag ser lugnt ut. Inga schemalagda händelser väntas påverka din portfölj väsentligt.")).toBeInTheDocument(),
    );
  });
});

describe("DailyBriefPage summary strip (RC-3, Phase 1/2 -- current-portfolio-state language removed)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("states a single calm, factual holdings-monitored count -- never a raw attention count competing with Since your last visit", async () => {
    mockFetch({});
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Atlas bevakar 3 innehav.")).toBeInTheDocument());
    // The former "N things need your attention today" line is gone --
    // it directly contradicted a real "Since your last visit" count.
    expect(screen.queryByText(/behöver din uppmärksamhet/)).not.toBeInTheDocument();
  });

  it("never shows current portfolio state (cash, watchlist opportunities) -- that belongs to Portfolio/Watchlist", async () => {
    mockFetch({});
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Atlas bevakar 3 innehav.")).toBeInTheDocument());
    expect(screen.queryByText(/Kassa:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/bevakningslistemöjlighet/)).not.toBeInTheDocument();
  });

  it("surfaces an open decision draft with a resume link", async () => {
    mockFetch({ openDrafts: [{ draftId: "draft-1", caseId: "case-nvda", subject: "NVDA", createdAt: "2026-08-20T00:00:00Z" }] });
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Pågående beslut")).toBeInTheDocument());
    expect(screen.getByRole("link", { name: "Återuppta: NVDA →" })).toHaveAttribute("href", "/decision-drafts/draft-1/commit");
  });

  it("omits the open-drafts section entirely when there are none", async () => {
    mockFetch({});
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Atlas bevakar 3 innehav.")).toBeInTheDocument());
    expect(screen.queryByText("Pågående beslut")).not.toBeInTheDocument();
  });

  it("shows an error message when the agenda fails to load", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/daily-brief/view-state")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve({ lastViewedAt: "2026-08-26T09:00:00Z" }) } as Response);
        }
        return Promise.resolve({ ok: false, status: 500 } as Response);
      }),
    );
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText(/Backend responded with 500/)).toBeInTheDocument());
  });
});
