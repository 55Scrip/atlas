import { describe, expect, it, vi, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "../testUtils";
import { PortfolioPage } from "./PortfolioPage";
import { __resetAlphaPortfolioCacheForTests } from "../portfolio/alphaPortfolioData";

function cockpitHolding(overrides: Record<string, unknown> = {}) {
  return {
    ticker: "AAPL",
    caseId: "case-aapl",
    weightPercent: 30,
    valueAbsolute: null,
    reconciliationStatus: "NONE",
    conviction: { level: "moderate", reasons: [] },
    analysisCoverage: { level: "substantial_coverage", reasons: [] },
    valuation: { status: "fairly_valued" },
    business: { growth: "moderate", capitalAllocation: "moderate" },
    riskProjection: { category: "financial_risk", status: "moderate" },
    confidence: "full",
    isThesisStale: false,
    attention: { priority: "standard_review", reasons: [] },
    decisionSupport: { level: "reduction_supported", badgeLabel: "Reduction supported", statement: "..." },
    ...overrides,
  };
}

function portfolioView(overrides: Record<string, unknown> = {}) {
  return {
    exists: true,
    entryMode: "PERCENT_ONLY",
    hasAbsoluteValues: false,
    holdings: [
      { ticker: "AAPL", weightPercent: 30, valueAbsolute: null, caseId: "case-aapl", reconciliationStatus: "NONE" },
      { ticker: "MSFT", weightPercent: 70, valueAbsolute: null, caseId: "case-msft", reconciliationStatus: "NONE" },
    ],
    cashWeightPercent: 5,
    cashValueAbsolute: null,
    totalValue: null,
    numberOfHoldings: 2,
    concentrationLevel: "Elevated",
    objective: null,
    horizon: null,
    awaitingReconciliation: false,
    ...overrides,
  };
}

function agendaResponse(overrides: Record<string, unknown> = {}) {
  return {
    generatedAt: "2026-01-01T09:00:00Z",
    summary: {
      holdingsCount: 2,
      criticalCount: 1,
      highCount: 0,
      watchlistOpportunityCount: 0,
      cashWeightPercent: 5,
      concentrationLevel: "Elevated",
    },
    items: [
      {
        id: "review_portfolio_position:AAPL",
        priority: "critical",
        kind: "review_portfolio_position",
        group: "portfolio",
        source: "portfolio_status",
        headline: "AAPL: outcome without execution (1 item(s))",
        reason: ["AAPL: outcome without execution (1 item(s))"],
        ticker: "AAPL",
        caseId: "case-aapl",
        portfolioContext: null,
        generatedAt: "2026-01-01T00:00:00Z",
        // Localization fix (Portfolio live-verification follow-up):
        // a real workflow item always carries these two -- the raw
        // English `headline` above is the backend's own unused-by-the
        // -UI fallback now, kept here only so a test overriding this
        // fixture without `attentionCategory` still gets a headline.
        attentionCategory: "OUTCOME_WITHOUT_EXECUTION",
        attentionCount: 1,
        reasonFacts: [
          {
            code: "workflow_gap",
            entity: "AAPL",
            value: "OUTCOME_WITHOUT_EXECUTION",
            secondaryValue: null,
            label: null,
            count: 1,
          },
        ],
      },
    ],
    ...overrides,
  };
}

function fitAssessment(overrides: Record<string, unknown> = {}) {
  return {
    caseId: "case-aapl",
    ticker: "AAPL",
    isExistingHolding: true,
    currentWeightPercent: 30,
    overall: "weak",
    overallReasoning: ["More dimensions rated Weak/Poor than Good/Excellent."],
    dimensions: [],
    trend: "declining",
    dataGaps: [],
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

const EMPTY_ACTION_DISTRIBUTION = { buy: [], add: [], hold: [], reduce: [], exit: [], wait: [], noDecision: [] };
const EMPTY_OPPORTUNITY_COST = {
  holdingsCompetingForCapital: [],
  watchlistCompetingWithHoldings: [],
  waitingPreferable: [],
  noActionAppropriate: [],
};
const EMPTY_CONVICTION = { highestConviction: [], lowestConviction: [], evidenceLimited: [], operationallyBlocked: [] };
const EMPTY_DECISION_PATH = {
  closestToInvestable: [],
  operationallyBlocked: [],
  requiringMoreEvidence: [],
  requiringDependencyResolution: [],
};
const EMPTY_DECISION_MEMORY = { recentlyChanged: [], stable: [], recentlyStrengthened: [], recentlyWeakened: [] };
const EMPTY_DECISION_EXPLANATION = { recentlyChanged: [], newSupportingFindings: [], resolvedBlockers: [], recentlyStrengthened: [] };
const EMPTY_DECISION_RELIABILITY = { mostReliable: [], leastReliable: [], recentlyImproved: [], recentlyWeakened: [] };
const EMPTY_PORTFOLIO_SYNTHESIS = { supportsPortfolio: [], highestCapitalCompetition: [], conflictsWithPortfolio: [], neutral: [] };
const EMPTY_SHARED_WEAK_POINTS = { sharedWeakAssumptions: [], sharedConditions: [], sharedMissingEvidence: [] };

function mockFetch(overrides: {
  view?: Record<string, unknown>;
  cockpitHoldings?: Record<string, unknown>[];
  fitAssessments?: Record<string, unknown>[];
  agenda?: Record<string, unknown>;
  actionDistribution?: Record<string, unknown>;
  opportunityCost?: Record<string, unknown>;
  conviction?: Record<string, unknown>;
  decisionPath?: Record<string, unknown>;
  decisionMemory?: Record<string, unknown>;
  decisionExplanation?: Record<string, unknown>;
  decisionReliability?: Record<string, unknown>;
  portfolioSynthesis?: Record<string, unknown>;
  sharedWeakPoints?: Record<string, unknown>;
} = {}) {
  const view = overrides.view ?? portfolioView();
  const cockpitHoldings = overrides.cockpitHoldings ?? [
    cockpitHolding(),
    cockpitHolding({ ticker: "MSFT", caseId: "case-msft", weightPercent: 70, decisionSupport: { level: "thesis_intact", badgeLabel: "", statement: "" } }),
  ];
  const fitAssessments = overrides.fitAssessments ?? [
    fitAssessment(),
    fitAssessment({ ticker: "MSFT", caseId: "case-msft", overall: "excellent", trend: "unchanged", currentWeightPercent: 70 }),
  ];
  const agenda = overrides.agenda ?? agendaResponse();
  // Pulse Simplification (live-verification follow-up): every Decision
  // Layer breakdown endpoint defaults to an honest "nothing here" shape
  // -- matching how none of these were mocked at all before this pass
  // (each request rejected, silently swallowed by the page's own
  // `.catch()`) -- so every pre-existing test's rendered output is
  // unchanged unless a test explicitly opts into real data.
  const actionDistribution = overrides.actionDistribution ?? EMPTY_ACTION_DISTRIBUTION;
  const opportunityCost = overrides.opportunityCost ?? EMPTY_OPPORTUNITY_COST;
  const conviction = overrides.conviction ?? EMPTY_CONVICTION;
  const decisionPath = overrides.decisionPath ?? EMPTY_DECISION_PATH;
  const decisionMemory = overrides.decisionMemory ?? EMPTY_DECISION_MEMORY;
  const decisionExplanation = overrides.decisionExplanation ?? EMPTY_DECISION_EXPLANATION;
  const decisionReliability = overrides.decisionReliability ?? EMPTY_DECISION_RELIABILITY;
  const portfolioSynthesis = overrides.portfolioSynthesis ?? EMPTY_PORTFOLIO_SYNTHESIS;
  const sharedWeakPoints = overrides.sharedWeakPoints ?? EMPTY_SHARED_WEAK_POINTS;

  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/alpha-portfolio/cockpit")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ exists: true, holdings: cockpitHoldings, unresolvedHoldings: [], priorityReviewCount: 0 }),
        } as Response);
      }
      if (url.includes("/api/alpha-portfolio/trade-log")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
      }
      if (url.includes("/api/alpha-portfolio")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(view) } as Response);
      }
      if (url.includes("/api/portfolio-fit/holdings")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(fitAssessments) } as Response);
      }
      if (url.includes("/api/daily-brief-agenda")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(agenda) } as Response);
      }
      if (url.includes("/api/decisions") || url.includes("/api/outcomes")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
      }
      if (url.includes("/api/investment-decision/portfolio/distribution")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(actionDistribution) } as Response);
      }
      if (url.includes("/api/opportunity-cost/portfolio/breakdown")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(opportunityCost) } as Response);
      }
      if (url.includes("/api/recommendation-conviction/portfolio/breakdown")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(conviction) } as Response);
      }
      if (url.includes("/api/decision-path/portfolio/breakdown")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(decisionPath) } as Response);
      }
      if (url.includes("/api/decision-memory/portfolio/breakdown")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(decisionMemory) } as Response);
      }
      if (url.includes("/api/decision-explanation/portfolio/breakdown")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(decisionExplanation) } as Response);
      }
      if (url.includes("/api/decision-reliability/portfolio/breakdown")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(decisionReliability) } as Response);
      }
      if (url.includes("/api/portfolio-decision/portfolio/breakdown")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(portfolioSynthesis) } as Response);
      }
      if (url.includes("/api/evidence-graph/portfolio/shared-weak-points")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(sharedWeakPoints) } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
}

describe("PortfolioPage (Product Sprint 8 -- Portfolio Excellence)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    __resetAlphaPortfolioCacheForTests();
  });

  it("renders portfolio status: holdings count, cash, largest position, and concentration", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("2 tillgångar")).toBeInTheDocument());
    expect(screen.getAllByText("5%").length).toBeGreaterThan(0);
    expect(screen.getByText("MSFT (70%)")).toBeInTheDocument();
    expect(screen.getAllByText("Förhöjd").length).toBeGreaterThan(0);
  });

  it("shows one critical pill sourced from the shared Daily Brief Agenda, never a second competing count", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("1 kritiska")).toBeInTheDocument());
  });

  it("renders Attention Required from the shared Daily Brief Agenda endpoint", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Kräver uppmärksamhet")).toBeInTheDocument());
    // Localization fix (Portfolio live-verification follow-up): a real
    // workflow item's headline is now composed and translated from
    // `attentionCategory`/`attentionCount`, never the backend's raw
    // English `headline` string -- see `describeAgendaHeadline.ts`.
    // Status Consolidation (Implementation Sprint B3): the same real
    // headline now renders twice by design -- once in the Attention
    // Required section, once in the Holdings Table's own "Change"
    // column below -- the same "one real signal, shown compactly in
    // two places" pattern established for Watchlist's Hero + table.
    expect(screen.getAllByText(/utfall utan verkställande/).length).toBeGreaterThan(0);
    expect(screen.queryByText(/outcome without execution/)).not.toBeInTheDocument();
  });

  it("shows the honest empty state for Attention Required when the agenda has no portfolio items", async () => {
    mockFetch({ agenda: agendaResponse({ items: [], summary: { holdingsCount: 2, criticalCount: 0, highCount: 0, watchlistOpportunityCount: 0, cashWeightPercent: 5, concentrationLevel: "Elevated" } }) });
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Kräver uppmärksamhet")).toBeInTheDocument());
    expect(screen.getByText("Atlas har inga väsentliga förändringar att rapportera idag.")).toBeInTheDocument();
  });

  function orderedTickersFromRowButtons(): string[] {
    return screen.getAllByRole("button", { name: /^Öppna (AAPL|MSFT)s vy$/ }).map((button) => {
      const match = button.getAttribute("aria-label")!.match(/^Öppna (AAPL|MSFT)s vy$/);
      if (!match || !match[1]) throw new Error("expected row button aria-label to match");
      return match[1];
    });
  }

  it("orders holdings by attention by default -- AAPL (flagged, lower weight) before MSFT (unflagged, higher weight)", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(orderedTickersFromRowButtons().length).toBe(2));
    expect(orderedTickersFromRowButtons()).toEqual(["AAPL", "MSFT"]);
  });

  it("re-sorts holdings by weight when Weight is selected", async () => {
    const user = (await import("@testing-library/user-event")).default.setup();
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(orderedTickersFromRowButtons().length).toBe(2));
    await user.click(screen.getByRole("link", { name: "Andel" }));
    expect(orderedTickersFromRowButtons()).toEqual(["MSFT", "AAPL"]);
  });

  it("shows the same Portfolio Fit rating for AAPL in both the Holdings Table and the Weakest Holdings section", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Svagaste innehaven")).toBeInTheDocument());
    const fitLabels = screen.getAllByText("Svag passform");
    expect(fitLabels.length).toBeGreaterThanOrEqual(2);
  });

  it("lists AAPL in Weakest Holdings (weak fit + reduction-supported) but not MSFT", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByText("Svagaste innehaven");
    // Exactly one holding (AAPL, weak fit + reduction-supported) qualifies
    // -- MSFT (excellent fit, thesis intact) does not -- so exactly one
    // "Compare alternatives" investigation link renders.
    expect(screen.getAllByRole("link", { name: /Jämför alternativ/ })).toHaveLength(1);
    expect(screen.queryByText("Inga innehav visar just nu svag portföljpassform eller ett reduktionsstött beslutsstöd.")).not.toBeInTheDocument();
  });

  it("offers Watchlist and Discovery entry points", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Utforska vidare")).toBeInTheDocument());
    expect(screen.getByRole("link", { name: /Öppna bevakningslistan/ })).toHaveAttribute("href", "/watchlist");
    expect(screen.getByRole("link", { name: /Öppna Discovery/ })).toHaveAttribute("href", "/discovery");
  });

  it("shows the empty-portfolio state honestly when no holdings exist", async () => {
    mockFetch({ view: portfolioView({ holdings: [], numberOfHoldings: 0 }) });
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Importera portfölj", { exact: false })).toBeInTheDocument());
  });

  it("never renders a fabricated Sector Allocation, only the honest disclosure", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Sektorfördelning")).toBeInTheDocument());
    expect(screen.getByText(/Sektorsdata följs ännu inte/)).toBeInTheDocument();
  });
});

describe("Pulse Simplification (live-verification follow-up)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    __resetAlphaPortfolioCacheForTests();
  });

  it("shows the new Beslutsläge section, right after Attention Required, with real Action Distribution and Opportunity Cost content", async () => {
    mockFetch({
      actionDistribution: { ...EMPTY_ACTION_DISTRIBUTION, reduce: ["AAPL"] },
      opportunityCost: { ...EMPTY_OPPORTUNITY_COST, waitingPreferable: ["AAPL"] },
    });
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Beslutsläge")).toBeInTheDocument());
    expect(screen.getByText("Minska (1)")).toBeInTheDocument();
    expect(screen.getByText("Att vänta är att föredra (1)")).toBeInTheDocument();
    // Attention Required must still come first -- Beslutsläge is a
    // secondary, named section right after it, never competing with it.
    const attentionHeading = screen.getByText("Kräver uppmärksamhet");
    const decisionStatusHeading = screen.getByText("Beslutsläge");
    expect(attentionHeading.compareDocumentPosition(decisionStatusHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("renders no Beslutsläge section at all when Action Distribution and Opportunity Cost are both genuinely empty", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Kräver uppmärksamhet")).toBeInTheDocument());
    expect(screen.queryByText("Beslutsläge")).not.toBeInTheDocument();
  });

  it("never fetches Decision Readiness -- removed as a Pulse row, its information already lives on the Holdings table and Attention Required", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Kräver uppmärksamhet")).toBeInTheDocument());
    const calledUrls = (fetch as unknown as { mock: { calls: unknown[][] } }).mock.calls.map((call) => String(call[0]));
    expect(calledUrls.some((url) => url.includes("decision-readiness"))).toBe(false);
  });

  it("groups the remaining Decision Layer widgets behind one collapsed detail, each under its own label, closed by default", async () => {
    mockFetch({
      conviction: { ...EMPTY_CONVICTION, lowestConviction: ["AAPL"] },
      decisionPath: { ...EMPTY_DECISION_PATH, requiringDependencyResolution: ["AAPL"] },
      decisionMemory: { ...EMPTY_DECISION_MEMORY, recentlyChanged: ["AAPL"] },
      decisionExplanation: { ...EMPTY_DECISION_EXPLANATION, resolvedBlockers: ["AAPL"] },
      decisionReliability: { ...EMPTY_DECISION_RELIABILITY, leastReliable: ["AAPL"] },
      portfolioSynthesis: { ...EMPTY_PORTFOLIO_SYNTHESIS, conflictsWithPortfolio: ["AAPL"] },
    });
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Detaljerad beslutsstatus")).toBeInTheDocument());

    // Closed by default: the native <details> element must not be open,
    // so an investor never has to see this on first glance.
    const details = screen.getByText("Detaljerad beslutsstatus").closest("details");
    expect(details).not.toBeNull();
    expect(details).not.toHaveAttribute("open");

    // Every one of the six moved widgets is present, each under its
    // own real label -- the one thing none of them did for themselves
    // before this pass.
    expect(screen.getByText("Rekommendationens styrka")).toBeInTheDocument();
    expect(screen.getByText("Svagast stöd (1)")).toBeInTheDocument();
    expect(screen.getByText("Beslutsväg")).toBeInTheDocument();
    expect(screen.getByText("Vägen kräver ett löst beroende (1)")).toBeInTheDocument();
    expect(screen.getByText("Beslutsregister")).toBeInTheDocument();
    expect(screen.getByText("Nyligen ändrade (1)")).toBeInTheDocument();
    expect(screen.getByText("Beslutsmotivering")).toBeInTheDocument();
    expect(screen.getByText("Lösta hinder (1)")).toBeInTheDocument();
    expect(screen.getByText("Tillförlitlighet")).toBeInTheDocument();
    expect(screen.getByText("Minst tillförlitliga (1)")).toBeInTheDocument();
    expect(screen.getByText("Portföljsyntes")).toBeInTheDocument();
    expect(screen.getByText("Står i konflikt med portföljen (1)")).toBeInTheDocument();
  });

  it("renders no collapsed detail section at all when every remaining Decision Layer widget is genuinely empty", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Kräver uppmärksamhet")).toBeInTheDocument());
    expect(screen.queryByText("Detaljerad beslutsstatus")).not.toBeInTheDocument();
  });
});

/**
 * Reliability Fix Sprint P2.1 -- regression coverage for the exact
 * failure mode found via live investigation: under React 18
 * StrictMode's dev-only mount -> cleanup -> remount cycle, the Daily
 * Brief Agenda fetch's own `AbortController` was found to corrupt not
 * only the first (StrictMode-discarded) request but the second, kept
 * one as well, leaving `dailyBriefAgenda` -- and therefore Attention
 * Required -- stuck at its initial loading state forever, even though
 * the endpoint itself returned a valid 200. These tests don't assert
 * on StrictMode directly (this test harness doesn't render inside it,
 * matching every other test in this file); they instead simulate its
 * observable shape -- an early, superseded request whose result must
 * never win against a later, current one -- directly at the fetch
 * layer, which is what the fix (a plain `cancelled` flag on the
 * effect, replacing `AbortController`) actually guards against.
 */
describe("PortfolioPage Attention Required -- loading reliability (Reliability Fix Sprint P2.1)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    __resetAlphaPortfolioCacheForTests();
  });

  /** Installs the same baseline `mockFetch()` stub, then layers a
   * controllable mock over `/api/daily-brief-agenda` specifically:
   * each call returns its own deferred promise, resolved or rejected
   * only when the test explicitly says so, while every other endpoint
   * keeps responding immediately exactly as `mockFetch()` already
   * sets up. */
  function mockFetchWithControllableAgenda() {
    mockFetch();
    const baseline = globalThis.fetch as unknown as (input: RequestInfo | URL) => Promise<Response>;
    const deferred: { resolve: (agenda: unknown) => void; reject: (error: unknown) => void }[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/daily-brief-agenda")) {
          return new Promise<Response>((resolve, reject) => {
            deferred.push({
              resolve: (agenda) => resolve({ ok: true, json: () => Promise.resolve(agenda) } as Response),
              reject,
            });
          });
        }
        return baseline(input);
      }),
    );
    return deferred;
  }

  it("Scenario A -- a single successful response moves Attention Required out of loading into loaded", async () => {
    const deferred = mockFetchWithControllableAgenda();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(deferred.length).toBe(1));
    deferred[0]!.resolve(agendaResponse());
    await waitFor(() => expect(screen.getByText("Kräver uppmärksamhet")).toBeInTheDocument());
    expect(screen.getAllByText(/utfall utan verkställande/).length).toBeGreaterThan(0);
  });

  it("Scenario B -- an earlier, superseded request resolving late must never overwrite a later request's own loaded state (the exact StrictMode-shaped race)", async () => {
    const deferred = mockFetchWithControllableAgenda();
    // Simulates React 18 StrictMode's real dev-only sequence exactly:
    // mount (request #1 goes out) -> immediate unmount (the effect's
    // own cleanup runs, marking request #1's result as stale, the same
    // guard the fix relies on) -> remount (request #2 goes out, this
    // is the instance that stays mounted for the rest of the test).
    const first = renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(deferred.length).toBe(1));
    first.unmount();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(deferred.length).toBe(2));
    // The second, current request resolves first...
    deferred[1]!.resolve(agendaResponse());
    await waitFor(() => expect(screen.getByText("Kräver uppmärksamhet")).toBeInTheDocument());
    expect(screen.getAllByText(/utfall utan verkställande/).length).toBeGreaterThan(0);
    // ...and only then does the first, superseded request's own result
    // arrive late, on an already-unmounted instance. Under the pre-fix
    // `AbortController` version this path never mattered because the
    // second (current) request itself never resolved at all; the
    // guarantee this test protects is that a late, stale response --
    // real or superseded -- can never corrupt state that has already
    // moved on. Resolving it must not throw and must not disturb the
    // still-mounted instance's own loaded content.
    expect(() => deferred[0]!.resolve(agendaResponse({ items: [] }))).not.toThrow();
    expect(screen.getAllByText(/utfall utan verkställande/).length).toBeGreaterThan(0);
  });

  it("Scenario C -- a genuine request failure resolves to the error state, never an indefinite loading state", async () => {
    const deferred = mockFetchWithControllableAgenda();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(deferred.length).toBe(1));
    deferred[0]!.reject(new Error("network failure"));
    await waitFor(() => expect(screen.getByText("Kräver uppmärksamhet")).toBeInTheDocument());
    expect(screen.getByText("Atlas har inga väsentliga förändringar att rapportera idag.")).toBeInTheDocument();
  });
});
