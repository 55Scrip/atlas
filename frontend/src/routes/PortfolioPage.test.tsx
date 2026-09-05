import { describe, expect, it, vi, afterEach } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
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
      // The default fixture item is a real investment signal (Portfolio
      // Fit) -- AAPL's own Today's Biggest Opportunity/Risk card reads
      // this via `agendaItemByTicker`, the one remaining in-scope
      // consumer of the shared Daily Brief Agenda on this page (Alpha
      // Integration Fix, One Product Pass).
      {
        id: "portfolio_fit:AAPL",
        priority: "critical",
        kind: "review_portfolio_position",
        group: "portfolio",
        source: "portfolio_fit",
        headline: "AAPL: Risk fit is poor, which outweighs the other dimensions.",
        reason: ["AAPL: Risk fit is poor, which outweighs the other dimensions."],
        ticker: "AAPL",
        caseId: "case-aapl",
        portfolioContext: null,
        generatedAt: "2026-01-01T00:00:00Z",
        attentionCategory: null,
        attentionCount: null,
        reasonFacts: [null],
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
    overallReasoningCode: null,
    overallReasoningCount: null,
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
    // Atlas UX Freeze v1: percentages render at one consistent decimal
    // place (Design System, Numerical Display Rules) -- "5%"/"70%" were
    // the pre-freeze raw/unrounded rendering.
    expect(screen.getAllByText("5.0%").length).toBeGreaterThan(0);
    expect(screen.getByText("MSFT (70.0%)")).toBeInTheDocument();
    expect(screen.getAllByText("Förhöjd").length).toBeGreaterThan(0);
  });

  it("Alpha Integration Fix: the Hero leads with ownership, not an attention-count verdict", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Du äger 2 innehav.")).toBeInTheDocument());
  });

  it("Alpha Integration Fix: never renders Attention Required, Today's Story, or an Agenda-sourced critical pill -- that surface duplicated Daily Brief's own job", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Du äger 2 innehav.")).toBeInTheDocument());
    expect(screen.queryByText("Kräver uppmärksamhet")).not.toBeInTheDocument();
    expect(screen.queryByText("Vad som hänt idag")).not.toBeInTheDocument();
    expect(screen.queryByText(/kritiska/)).not.toBeInTheDocument();
  });

  it("Alpha Integration Fix: the Holdings Table's Reason column shows only Stance's own reasoning, never the Agenda headline or a Priority badge", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    const aaplRowButton = await screen.findByRole("button", { name: "Öppna AAPLs vy" });
    const aaplRow = within(aaplRowButton.closest("tr")!);
    // No stance is mocked for this fixture, so both the Current view
    // cell and the Reason cell show the honest "New" fallback.
    expect(aaplRow.getAllByText("Nytt")).toHaveLength(2);
    expect(aaplRow.queryByText(/Risk fit is poor/)).not.toBeInTheDocument();
    // The same real Agenda headline still renders once, in Today's
    // Biggest Risk/Opportunity's own "what changed" line -- it was
    // never deleted, only removed from the surfaces that duplicated
    // Daily Brief's own job.
    expect(screen.getAllByText(/Risk fit is poor/).length).toBe(1);
  });

  function orderedTickersFromRowButtons(): string[] {
    return screen.getAllByRole("button", { name: /^Öppna (AAPL|MSFT)s vy$/ }).map((button) => {
      const match = button.getAttribute("aria-label")!.match(/^Öppna (AAPL|MSFT)s vy$/);
      if (!match || !match[1]) throw new Error("expected row button aria-label to match");
      return match[1];
    });
  }

  it("Alpha Integration Fix: orders holdings by weight by default -- MSFT (70%) before AAPL (30%), ownership-first per Portfolio's own doctrine", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(orderedTickersFromRowButtons().length).toBe(2));
    expect(orderedTickersFromRowButtons()).toEqual(["MSFT", "AAPL"]);
  });

  it("re-sorts holdings alphabetically when A–Ö is selected", async () => {
    const user = (await import("@testing-library/user-event")).default.setup();
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(orderedTickersFromRowButtons().length).toBe(2));
    await user.click(screen.getByRole("link", { name: "A–Ö" }));
    expect(orderedTickersFromRowButtons()).toEqual(["AAPL", "MSFT"]);
  });

  it("shows the same Investment rating in the Holdings Table that Watchlist and Investment Case show, next to (not replacing) Stance (Atlas UX Phase 7B, Phase 5)", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(orderedTickersFromRowButtons().length).toBe(2));
    // AAPL: reduction_supported -> 3.0 (Weak). MSFT: thesis_intact -> 6.0 (Fair).
    expect(screen.getByText("Investering 3.0")).toBeInTheDocument();
    expect(screen.getByText("Investering 6.0")).toBeInTheDocument();
  });

  it("shows AAPL's weak Portfolio Fit rating once, in Portfolio Weaknesses (no longer duplicated across a separate Fit overview)", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    const heading = await screen.findByText("Portföljsvagheter");
    const section = within(heading.closest("div")!);
    expect(section.getByText("Svag passform")).toBeInTheDocument();
    expect(screen.getAllByText("Svag passform")).toHaveLength(1);
  });

  it("lists AAPL in Portfolio Weaknesses (weak fit + reduction-supported) but not MSFT", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    const heading = await screen.findByText("Portföljsvagheter");
    const section = within(heading.closest("div")!);
    // Exactly one holding (AAPL, weak fit + reduction-supported) qualifies
    // -- MSFT (excellent fit, thesis intact) does not -- so exactly one
    // "Compare alternatives" investigation link renders within this section
    // (MSFT's own such link, if any, lives in Portfolio Opportunities instead).
    expect(section.getAllByRole("link", { name: /Jämför alternativ/ })).toHaveLength(1);
    expect(section.queryByText("Inga innehav visar just nu svag portföljpassform eller ett reduktionsstött beslutsstöd.")).not.toBeInTheDocument();
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

describe("Product Simplification Sprint 6E -- Decision Status/Decision Layer Detail removed entirely", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    __resetAlphaPortfolioCacheForTests();
  });

  it("never renders Decision Status or Decision Layer Detail -- Phase 5 removed both sections, not just their old jargon labels", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Du äger 2 innehav.")).toBeInTheDocument());
    expect(screen.queryByText("Beslutsläge")).not.toBeInTheDocument();
    expect(screen.queryByText("Detaljerad beslutsstatus")).not.toBeInTheDocument();
  });

  it("never renders Recent Activity -- Phase 6 removed the portfolio-local activity log entirely", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Du äger 2 innehav.")).toBeInTheDocument());
    expect(screen.queryByText("Senaste aktivitet")).not.toBeInTheDocument();
  });
});

/**
 * Reliability Fix Sprint P2.1 -- regression coverage for the exact
 * failure mode found via live investigation: under React 18
 * StrictMode's dev-only mount -> cleanup -> remount cycle, the Daily
 * Brief Agenda fetch's own `AbortController` was found to corrupt not
 * only the first (StrictMode-discarded) request but the second, kept
 * one as well, leaving `dailyBriefAgenda` stuck at its initial loading
 * state forever, even though the endpoint itself returned a valid 200.
 * These tests don't assert on StrictMode directly (this test harness
 * doesn't render inside it, matching every other test in this file);
 * they instead simulate its observable shape -- an early, superseded
 * request whose result must never win against a later, current one --
 * directly at the fetch layer, which is what the fix (a plain
 * `cancelled` flag on the effect, replacing `AbortController`) actually
 * guards against.
 *
 * Alpha Integration Fix (One Product Pass): Attention Required, the
 * surface these tests originally watched to observe the Agenda fetch's
 * loaded/error state, is gone (it duplicated Daily Brief's own job).
 * The Agenda fetch itself is unchanged and still feeds one remaining,
 * in-scope surface -- Today's Biggest Opportunity/Risk's own "what
 * changed" line, which reads the real headline once loaded and an
 * honest "no significant changes" fallback otherwise. These tests now
 * watch that line instead.
 */
describe("PortfolioPage -- Daily Brief Agenda loading reliability (Reliability Fix Sprint P2.1)", () => {
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

  it("Scenario A -- a single successful response replaces the honest fallback with the real Agenda signal", async () => {
    const deferred = mockFetchWithControllableAgenda();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(deferred.length).toBe(1));
    // AAPL's own card (Today's Biggest Opportunity, per this fixture's
    // fit ordering) shows the honest "no significant changes" fallback
    // until the Agenda resolves -- there is no fabricated headline.
    await waitFor(() => expect(screen.getAllByText(/Inga betydande förändringar/).length).toBeGreaterThan(0));
    deferred[0]!.resolve(agendaResponse());
    await waitFor(() => expect(screen.getByText(/Risk fit is poor/)).toBeInTheDocument());
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
    await waitFor(() => expect(screen.getByText(/Risk fit is poor/)).toBeInTheDocument());
    // ...and only then does the first, superseded request's own result
    // arrive late, on an already-unmounted instance. Under the pre-fix
    // `AbortController` version this path never mattered because the
    // second (current) request itself never resolved at all; the
    // guarantee this test protects is that a late, stale response --
    // real or superseded -- can never corrupt state that has already
    // moved on. Resolving it must not throw and must not disturb the
    // still-mounted instance's own loaded content.
    expect(() => deferred[0]!.resolve(agendaResponse({ items: [] }))).not.toThrow();
    expect(screen.getByText(/Risk fit is poor/)).toBeInTheDocument();
  });

  it("Scenario C -- a genuine request failure resolves honestly, never an indefinite loading state or a crash", async () => {
    const deferred = mockFetchWithControllableAgenda();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(deferred.length).toBe(1));
    deferred[0]!.reject(new Error("network failure"));
    // The page keeps rendering normally -- the Hero's own ownership
    // fact never depends on the Agenda fetch -- and the risk/
    // opportunity card keeps its honest fallback rather than hanging.
    await waitFor(() => expect(screen.getByText("Du äger 2 innehav.")).toBeInTheDocument());
    expect(screen.getAllByText(/Inga betydande förändringar/).length).toBeGreaterThan(0);
  });
});
