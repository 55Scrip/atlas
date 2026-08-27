import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
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

function mockFetch(response: unknown, openDrafts: unknown[] = [], monitoringRun: unknown = EMPTY_MONITORING_RUN) {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/daily-brief-agenda")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(response) } as Response);
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
}

describe("DailyBriefPage (Daily Brief Engine & Prioritization)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the unified agenda from the one shared endpoint", async () => {
    mockFetch(agendaResponse());
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Kritisk")).toBeInTheDocument());
    expect(screen.getByText("China revenue declines (satisfied)", { exact: false })).toBeInTheDocument();
  });

  it("shows the honest empty state when there are no agenda items", async () => {
    mockFetch(agendaResponse({ items: [], summary: { holdingsCount: 2, criticalCount: 0, highCount: 0, watchlistOpportunityCount: 0, cashWeightPercent: null, concentrationLevel: "Low" } }));
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Atlas har inga väsentliga förändringar att rapportera idag.")).toBeInTheDocument());
  });

  it("shows the all-stable summary line when there are no critical or high items", async () => {
    mockFetch(agendaResponse({ summary: { holdingsCount: 2, criticalCount: 0, highCount: 0, watchlistOpportunityCount: 0, cashWeightPercent: null, concentrationLevel: "Low" }, items: [] }));
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Portföljen är stabil. Inget behöver din uppmärksamhet idag.")).toBeInTheDocument());
  });

  it("shows the one primary attention count when a real critical item exists", async () => {
    mockFetch(agendaResponse());
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("1 sak behöver din uppmärksamhet idag.")).toBeInTheDocument());
  });

  it("combines critical and high-priority tickers into the one primary count -- never two competing numbers (Atlas UX Phase 7B, Phase 1)", async () => {
    mockFetch(
      agendaResponse({
        items: [
          agendaItem({ id: "e1:AAPL", ticker: "AAPL", priority: "critical" }),
          agendaItem({ id: "e2:MSFT", ticker: "MSFT", caseId: "case-msft", priority: "critical", headline: "MSFT: real signal", reason: ["MSFT: real signal"] }),
          agendaItem({ id: "e3:NVDA", ticker: "NVDA", caseId: "case-nvda", priority: "high", headline: "NVDA: real signal", reason: ["NVDA: real signal"] }),
        ],
      }),
    );
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("3 saker behöver din uppmärksamhet idag.")).toBeInTheDocument());
    // Never a second, separately-worded "high-priority" statement --
    // one primary number only, matching what the agenda list below it
    // actually shows.
    expect(screen.queryByText(/högprioriterad/)).not.toBeInTheDocument();
  });

  it("counts a high-priority-only ticker in the same one primary number, never a second line", async () => {
    mockFetch(
      agendaResponse({
        items: [agendaItem({ priority: "high" })],
      }),
    );
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("1 sak behöver din uppmärksamhet idag.")).toBeInTheDocument());
    expect(screen.queryByText(/högprioriterad/)).not.toBeInTheDocument();
  });

  it("never counts Atlas's own bookkeeping toward the attention count, and never gives it a card (Atlas UX Phase 7B, Phase 1)", async () => {
    mockFetch(
      agendaResponse({
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
    );
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Portföljen är stabil. Inget behöver din uppmärksamhet idag.")).toBeInTheDocument());
    expect(screen.queryByText("MSFT")).not.toBeInTheDocument();
    expect(screen.queryByText(/^\d+ sak(er)? behöver din uppmärksamhet idag\.$/)).not.toBeInTheDocument();
  });

  it("never shows a watchlist-opportunity line when the count is zero", async () => {
    mockFetch(agendaResponse());
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("1 sak behöver din uppmärksamhet idag.")).toBeInTheDocument());
    expect(screen.queryByText(/bevakningslistemöjlighet/)).not.toBeInTheDocument();
  });

  it("shows the real cash fact, never an invented 'unchanged' claim", async () => {
    mockFetch(agendaResponse());
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Kassa: 5.0% av portföljen.")).toBeInTheDocument());
    expect(screen.queryByText(/oförändrad/)).not.toBeInTheDocument();
  });

  it("omits the cash line entirely when cash is unrecorded, rather than fabricating a value", async () => {
    mockFetch(agendaResponse({ summary: { holdingsCount: 1, criticalCount: 1, highCount: 0, watchlistOpportunityCount: 0, cashWeightPercent: null, concentrationLevel: null } }));
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("1 sak behöver din uppmärksamhet idag.")).toBeInTheDocument());
    expect(screen.queryByText(/Kassa:/)).not.toBeInTheDocument();
  });

  it("surfaces an open decision draft with a resume link (Product Sprint 12, Deliverable 4/7 -- previously invisible everywhere)", async () => {
    mockFetch(agendaResponse(), [
      { draftId: "draft-1", caseId: "case-nvda", subject: "NVDA", createdAt: "2026-08-20T00:00:00Z" },
    ]);
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Pågående beslut")).toBeInTheDocument());
    expect(screen.getByRole("link", { name: "Återuppta: NVDA →" })).toHaveAttribute(
      "href",
      "/decision-drafts/draft-1/commit",
    );
  });

  it("omits the open-drafts section entirely when there are none", async () => {
    mockFetch(agendaResponse(), []);
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Kritisk")).toBeInTheDocument());
    expect(screen.queryByText("Pågående beslut")).not.toBeInTheDocument();
  });

  it("shows an error message when the agenda fails to load", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: false, status: 500 } as Response)));
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText(/Backend responded with 500/)).toBeInTheDocument());
  });
});

describe("DailyBriefPage Monitoring section (Product Intelligence Sprint 3 -- Monitoring Intelligence Activation)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("surfaces a real Monitoring change -- previously computed and never shown anywhere", async () => {
    mockFetch(agendaResponse(), [], { generatedAt: "2026-01-01T00:00:00Z", results: [monitoringResult()] });
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Atlas syn har försvagats.")).toBeInTheDocument());
  });

  it("shows the honest empty state when Monitoring has found no changes", async () => {
    mockFetch(agendaResponse());
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Kritisk")).toBeInTheDocument());
    expect(
      await screen.findByText("Atlas har inte hittat några förändringar att rapportera för dina bolag."),
    ).toBeInTheDocument();
  });

  it("shows a distinct unavailable state, never blank, when the Monitoring fetch fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/daily-brief-agenda")) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(agendaResponse()) } as Response);
        }
        if (url.includes("/api/monitoring/results")) {
          return Promise.resolve({ ok: false, status: 500 } as Response);
        }
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    renderWithProviders(<DailyBriefPage />, { route: "/daily-brief" });
    await waitFor(() => expect(screen.getByText("Kritisk")).toBeInTheDocument());
    expect(await screen.findByText("Förändringar är inte tillgängliga just nu.")).toBeInTheDocument();
  });
});
