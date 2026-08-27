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

const EMPTY_MONITORING_RUN = { generatedAt: "2026-01-01T00:00:00Z", results: [] };

function monitoringResult(overrides: Record<string, unknown> = {}) {
  return {
    caseId: "case-aapl",
    ticker: "AAPL",
    scope: "portfolio",
    status: "changed_high_importance",
    changes: [
      {
        id: "change-1",
        category: "stance_weakened",
        materiality: "material",
        direction: "negative",
        reason: "Atlas's view on AAPL weakened.",
        sourceCapability: "evidence_timeline",
        evidenceReference: "evidence-1",
      },
    ],
    stanceLevel: null,
    confidenceLevel: null,
    coverageLevel: null,
    latestMeaningfulEvidenceAt: null,
    recommendedAction: null,
    generatedAt: "2026-01-01T00:00:00Z",
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
  monitoringRun?: unknown;
  lastViewedAt?: string | null;
  changeGroups?: unknown[];
}) {
  const {
    agenda = agendaResponse(),
    openDrafts = [],
    monitoringRun = EMPTY_MONITORING_RUN,
    lastViewedAt = "2026-08-26T09:00:00Z",
    changeGroups = [],
  } = options;
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
      if (url.includes("/api/monitoring/results")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(monitoringRun) } as Response);
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

  it("marks a NEW change seen when its Investment Case is opened from the card", async () => {
    const { markSeenCalls } = mockFetch({ changeGroups: [changeGroup()] });
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("NVDA")).toBeInTheDocument());
    screen.getByText("Öppna investeringscase →").click();
    await waitFor(() => expect(markSeenCalls.length).toBe(1));
    expect(JSON.parse(markSeenCalls[0] as string)).toEqual({ changeIds: ["change-nvda-1"] });
  });

  it("always shows the calm 'Atlas is watching today' fallback -- no scheduled-catalyst data source exists (documented gap)", async () => {
    mockFetch({});
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() =>
      expect(screen.getByText("Idag ser lugnt ut. Inga schemalagda händelser väntas påverka din portfölj väsentligt.")).toBeInTheDocument(),
    );
  });
});

describe("DailyBriefPage summary strip (unchanged by Daily Brief 2.0)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the all-stable summary line when there are no critical or high items", async () => {
    mockFetch({
      agenda: agendaResponse({
        summary: { holdingsCount: 2, criticalCount: 0, highCount: 0, watchlistOpportunityCount: 0, cashWeightPercent: null, concentrationLevel: "Low" },
        items: [],
      }),
    });
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Portföljen är stabil. Inget behöver din uppmärksamhet idag.")).toBeInTheDocument());
  });

  it("shows the one primary attention count when a real critical item exists", async () => {
    mockFetch({});
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("1 sak behöver din uppmärksamhet idag.")).toBeInTheDocument());
  });

  it("never counts Atlas's own bookkeeping toward the attention count (Atlas UX Phase 7B, Phase 1)", async () => {
    mockFetch({
      agenda: agendaResponse({
        items: [
          agendaItem({
            priority: "critical",
            headline: "MSFT: a decision is missing a note explaining why",
            reason: ["MSFT: a decision is missing a note explaining why"],
            reasonFacts: [{ code: "workflow_gap", value: "decision_without_outcome" }],
            ticker: "MSFT",
            caseId: "case-msft",
          }),
        ],
      }),
    });
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Portföljen är stabil. Inget behöver din uppmärksamhet idag.")).toBeInTheDocument());
    expect(screen.queryByText(/^\d+ sak(er)? behöver din uppmärksamhet idag\.$/)).not.toBeInTheDocument();
  });

  it("shows the real cash fact, never an invented 'unchanged' claim", async () => {
    mockFetch({});
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Kassa: 5.0% av portföljen.")).toBeInTheDocument());
    expect(screen.queryByText(/oförändrad/)).not.toBeInTheDocument();
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
    await waitFor(() => expect(screen.getByText("1 sak behöver din uppmärksamhet idag.")).toBeInTheDocument());
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

describe("DailyBriefPage Monitoring section (unchanged by Daily Brief 2.0)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("surfaces a real Monitoring change", async () => {
    mockFetch({ monitoringRun: { generatedAt: "2026-01-01T00:00:00Z", results: [monitoringResult()] } });
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Atlas syn har försvagats.")).toBeInTheDocument());
  });

  it("shows the honest empty state when Monitoring has found no changes", async () => {
    mockFetch({});
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() =>
      expect(screen.getByText("Atlas har inte hittat några förändringar att rapportera för dina bolag.")).toBeInTheDocument(),
    );
  });

  it("shows a distinct unavailable state, never blank, when the Monitoring fetch fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/daily-brief-change-log")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
        }
        if (url.includes("/api/daily-brief/view-state")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve({ lastViewedAt: "2026-08-26T09:00:00Z" }) } as Response);
        }
        if (url.includes("/api/daily-brief-agenda")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(agendaResponse()) } as Response);
        }
        if (url.includes("/api/monitoring/results")) {
          return Promise.resolve({ ok: false, status: 500 } as Response);
        }
        if (url.includes("/api/decision-drafts/daily-brief-summary")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
        }
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Förändringar är inte tillgängliga just nu.")).toBeInTheDocument());
  });
});
