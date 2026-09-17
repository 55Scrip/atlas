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
    // The allocation dimension is what the cockpit's Fit cell reads:
    // this position's weight against the portfolio's concentration,
    // which is the one genuinely portfolio-relational dimension the
    // engine produces.
    dimensions: [
      { kind: "allocation", rating: "weak", reasoning: ["This holding is 30.0% of the portfolio."] },
      { kind: "valuation", rating: "weak", reasoning: ["Relative valuation: expensive."] },
      { kind: "risk", rating: "weak", reasoning: ["1 of 4 risk categories High."] },
    ],
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

  it("Portfolio Control Room: the Holdings Table compares positions with categorical columns, never per-row prose", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    const aaplRowButton = await screen.findByRole("button", { name: "Öppna AAPLs vy" });
    const aaplRow = within(aaplRowButton.closest("tr")!);
    // Canonical recommendation, in the Investment Case's own words.
    expect(aaplRow.getByText("Minskning stöds")).toBeInTheDocument();
    // Fit and the largest identified risk, both categorical.
    // Holdings Cockpit v1: the risk cell leads with the status and
    // names the category beneath it, so a reader scanning the column
    // compares severities rather than parsing "Category: Status" prose.
    // The Fit cell now carries the allocation dimension -- this
    // position's weight against the portfolio's concentration -- and
    // says so, rather than an overall verdict driven by case analysis.
    expect(aaplRow.getByText("endast positionsstorlek")).toBeInTheDocument();
    expect(aaplRow.getByText("Måttlig")).toBeInTheDocument();
    expect(aaplRow.getByText("Finansiell")).toBeInTheDocument();
    // Analysis depth lost its column: it would have crowded out a more
    // decision-useful dimension, and it now surfaces only as an
    // exception line under the Atlas action when evidence is limited.
    // A fully-evaluated holding says nothing about its own coverage.
    expect(aaplRow.queryByText("Utvärderat")).not.toBeInTheDocument();
    // The Stance prose that used to fill a 320px column is gone from
    // the row -- the reasoning it summarised lives in the Investment
    // Case, which owns that explanation.
    expect(aaplRow.queryByText(/Risk fit is poor/)).not.toBeInTheDocument();
    // The same real Agenda headline still renders once, in Today's
    // Biggest Risk/Opportunity's own "what changed" line.
    expect(screen.getAllByText(/Risk fit is poor/).length).toBe(1);
  });

  it("does not introduce Figma concepts the engine does not support", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna AAPLs vy" });
    const table = document.querySelector("table")!;
    const text = table.textContent ?? "";
    // Conviction: the field of that name measures how well the
    // available analysis supports a conclusion -- coverage,
    // contradiction, open questions -- which is analytical confidence,
    // the very thing investment conviction is defined against.
    expect(text).not.toContain("Övertygelse");
    // No probability-weighted return exists anywhere in the engine.
    expect(text).not.toContain("Förv. avkastning");
    expect(text).not.toContain("Uppsida");
    expect(text).not.toContain("Nedsida");
    // `RiskProjection` is the highest-severity risk *category*, not a
    // permanent-capital-loss estimate. Holdings Cockpit v1 shortened
    // the header to "Risk" so nine columns fit, and the cell now
    // carries the disclosure the header used to: it names the category
    // beneath the status, so nothing reads as an aggregate risk score.
    expect(text).toContain("Risk");
    expect(text).not.toContain("Riskpoäng");
    // Business stays its own column. Investment is gone from the
    // cockpit: it read `decisionSupport.level` -- the same field the
    // Atlas column states in words -- on a 0-10 scale, so on an owned
    // position it read as a grade on the holding while carrying no
    // information the row did not already have.
    expect(text).toContain("Verksamhet");
    expect(text).not.toContain("Investering");
    // Forward may never be labelled as a forecast.
    expect(text).toContain("Framåt");
    expect(text).not.toContain("Prognos");
  });

  it("shows no frontend-invented numeric score for the canonical recommendation", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna AAPLs vy" });
    const table = document.querySelector("table")!;
    // `deriveInvestmentRating` turned a categorical canonical value into
    // a 0-10 score. The cockpit no longer shows it at all; the
    // canonical badge is the only rendering of that field here.
    expect(table.textContent ?? "").not.toMatch(/Investering/);
    expect(table.textContent ?? "").toContain("Minskning stöds");
  });

  it("renders unknown analytics honestly rather than as a neutral value", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    const msftRowButton = await screen.findByRole("button", { name: "Öppna MSFTs vy" });
    const msftRow = within(msftRowButton.closest("tr")!);
    // No stance is mocked for this fixture, so the Atlas-view cell is
    // genuinely unknown and must say so.
    expect(msftRow.getAllByText("Ej bedömt").length).toBeGreaterThan(0);
  });

  function orderedTickersFromRowButtons(): string[] {
    return screen.getAllByRole("button", { name: /^Öppna (AAPL|MSFT)s vy$/ }).map((button) => {
      const match = button.getAttribute("aria-label")!.match(/^Öppna (AAPL|MSFT)s vy$/);
      if (!match || !match[1]) throw new Error("expected row button aria-label to match");
      return match[1];
    });
  }

  it("keeps every row a direct route into that holding's own Investment Case", async () => {
    mockFetch();
    renderWithProviders(
      <PortfolioPage />,
      { route: "/portfolio" },
    );
    const aaplRow = await screen.findByRole("button", { name: "Öppna AAPLs vy" });
    // Row activation is the navigation affordance -- the separate
    // "Öppna" link column was removed as a redundant second copy of the
    // same action, so the row must stay keyboard- and pointer-operable.
    expect(aaplRow.tagName).toBe("TR");
    expect(aaplRow).toHaveAttribute("tabIndex", "0");
    expect(screen.getByRole("button", { name: "Öppna MSFTs vy" })).toBeInTheDocument();
  });

  it("keeps Portfolio Health as one compact strip carrying every statistic", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Du äger 2 innehav.")).toBeInTheDocument());
    // The Hero card and the Pulse strip were merged into one. Nothing
    // was dropped: ownership, concentration, cash, largest position and
    // Atlas coverage all still render.
    expect(screen.getAllByText("5.0%").length).toBeGreaterThan(0);
    expect(screen.getByText("MSFT (70.0%)")).toBeInTheDocument();
    expect(screen.getAllByText("Förhöjd").length).toBeGreaterThan(0);
    expect(screen.getByText("2 tillgångar")).toBeInTheDocument();
  });

  it("Alpha Integration Fix: orders holdings by weight by default -- MSFT (70%) before AAPL (30%), ownership-first per Portfolio's own doctrine", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(orderedTickersFromRowButtons().length).toBe(2));
    expect(orderedTickersFromRowButtons()).toEqual(["MSFT", "AAPL"]);
  });

  it("Holdings Cockpit v1: renders every holding, with nothing hidden behind a toggle", async () => {
    // The cockpit exists to let the investor scan the portfolio as a
    // whole. The table used to cap at 15 rows behind "View All
    // Holdings" -- reasonable at 99px a row, wrong at 53px, where all
    // 25 of the real Internal Alpha portfolio fit in ~1,334px, barely
    // more than the old capped table occupied.
    //
    // Sized at the real portfolio's 25 holdings deliberately: 25 is the
    // number that used to be truncated, so a reintroduced cap of 15 --
    // or of 20, or of 24 -- fails here.
    const tickers = Array.from({ length: 25 }, (_, index) => `T${String(index + 1).padStart(2, "0")}`);
    mockFetch({
      view: portfolioView({
        holdings: tickers.map((ticker, index) => ({
          ticker,
          weightPercent: 25 - index,
          valueAbsolute: null,
          caseId: `case-${ticker}`,
          reconciliationStatus: "NONE",
        })),
        numberOfHoldings: 25,
      }),
      cockpitHoldings: tickers.map((ticker, index) =>
        cockpitHolding({ ticker, caseId: `case-${ticker}`, weightPercent: 25 - index }),
      ),
      fitAssessments: tickers.map((ticker, index) =>
        fitAssessment({ ticker, caseId: `case-${ticker}`, currentWeightPercent: 25 - index }),
      ),
    });
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna T01s vy" });

    const body = document.querySelector("table tbody")!;
    expect(body.querySelectorAll("tr")).toHaveLength(25);
    // Both ends of the list, so a cap at either end would fail.
    expect(screen.getByRole("button", { name: "Öppna T25s vy" })).toBeInTheDocument();

    // No paging affordance survives, and no "showing N of M" caveat --
    // both would be lying now that nothing is hidden.
    const table = document.querySelector("table")!.parentElement!.parentElement!;
    expect(table.textContent ?? "").not.toMatch(/Visa alla|Visa färre|Visar \d+ av/);
  });

  it("re-sorts holdings alphabetically when A–Ö is selected", async () => {
    const user = (await import("@testing-library/user-event")).default.setup();
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(orderedTickersFromRowButtons().length).toBe(2));
    await user.click(screen.getByRole("link", { name: "A–Ö" }));
    expect(orderedTickersFromRowButtons()).toEqual(["AAPL", "MSFT"]);
  });

  it("shows the canonical recommendation in the same words the Investment Case uses", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(orderedTickersFromRowButtons().length).toBe(2));
    // The identical `DECISION_SUPPORT_BADGE_KEY` vocabulary the
    // Investment Case hero renders, so one holding reads the same
    // judgment on both surfaces. AAPL: reduction_supported.
    // MSFT: thesis_intact.
    const aapl = within(screen.getByRole("button", { name: "Öppna AAPLs vy" }).closest("tr")!);
    const msft = within(screen.getByRole("button", { name: "Öppna MSFTs vy" }).closest("tr")!);
    expect(aapl.getByText("Minskning stöds")).toBeInTheDocument();
    expect(msft.getByText("Tesen kvarstår")).toBeInTheDocument();
  });

  it("shows AAPL's weak Portfolio Fit rating once, in Portfolio Weaknesses (no longer duplicated across a separate Fit overview)", async () => {
    mockFetch();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    const heading = await screen.findByText("Portföljsvagheter");
    const section = within(heading.closest("div")!);
    expect(section.getByText("Svag passform")).toBeInTheDocument();
    // The Holdings Table used to show this same *overall* verdict in
    // its Fit cell. That verdict is a vote across five dimensions, of
    // which Business, Valuation and Risk are properties of the case --
    // so it largely restated the two columns beside it under a
    // portfolio-sounding name, and a Poor Risk Fit could gate the whole
    // thing. The cockpit now reads the allocation dimension, which is
    // genuinely about how this position sits in the portfolio, and
    // labels it as such.
    const table = document.querySelector("table")!;
    expect(within(table).getAllByText("endast positionsstorlek").length).toBeGreaterThan(0);
    expect(section.getByText("Svag passform")).toBeInTheDocument();
  });

  it("reads the allocation dimension in the Fit cell, not the overall vote", async () => {
    // The distinguishing case: a holding whose overall fit is Weak --
    // because the case is expensive and risky -- but whose *size* in
    // the portfolio is unremarkable. Before this sprint the cockpit
    // showed "Svag passform" here, which read as "this position does
    // not belong in your portfolio" when Atlas had assessed no such
    // thing. The two ratings must be able to disagree, and the cell
    // must follow allocation.
    mockFetch({
      fitAssessments: [
        fitAssessment({
          overall: "weak",
          dimensions: [
            { kind: "allocation", rating: "excellent", reasoning: ["This holding is 3.0% of the portfolio."] },
            { kind: "valuation", rating: "poor", reasoning: ["Relative valuation: expensive."] },
          ],
        }),
      ],
    });
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByText("Portföljsvagheter");
    const table = within(document.querySelector("table")!);
    expect(table.getAllByText("Utmärkt passform").length).toBeGreaterThan(0);
    expect(table.queryByText("Svag passform")).not.toBeInTheDocument();
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


/**
 * Portfolio Opportunity / Action Consistency. The headline used to be the
 * best Portfolio Fit and nothing else, so it announced ASSA-B as "today's
 * biggest opportunity" while ASSA-B's own Case said there was nothing to
 * act on. Fit describes suitability; only the Decision Layer describes
 * whether Atlas supports doing anything.
 */
describe("PortfolioPage -- opportunity means a supported action", () => {
  /** ASSA-B fits best and is withheld; MA fits next and is the one Atlas
   * supports adding to -- the real shape that produced the contradiction. */
  const withheldBestFit = {
    cockpitHoldings: [
      cockpitHolding({ ticker: "ASSA-B", caseId: "case-assa", weightPercent: 3, decisionSupport: { level: "insufficient_evidence", badgeLabel: "", statement: "" } }),
      cockpitHolding({ ticker: "MA", caseId: "case-ma", weightPercent: 3, decisionSupport: { level: "increase_supported", badgeLabel: "", statement: "" } }),
      cockpitHolding({ ticker: "VST", caseId: "case-vst", weightPercent: 3, decisionSupport: { level: "reduction_supported", badgeLabel: "", statement: "" } }),
    ],
    fitAssessments: [
      fitAssessment({ ticker: "ASSA-B", caseId: "case-assa", overall: "excellent", currentWeightPercent: 3 }),
      fitAssessment({ ticker: "MA", caseId: "case-ma", overall: "excellent", currentWeightPercent: 3 }),
      fitAssessment({ ticker: "VST", caseId: "case-vst", overall: "poor", currentWeightPercent: 3 }),
    ],
  };

  it("names the holding Atlas supports adding to, not the best-fitting withheld one", async () => {
    mockFetch(withheldBestFit);
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText("Dagens största möjlighet")).toBeInTheDocument());
    // "MA" also appears in the holdings table, so the assertion is scoped
    // to the card the label belongs to.
    const card = screen.getByText("Dagens största möjlighet").closest("div");
    expect(card?.textContent).toContain("MA");
    expect(card?.textContent).not.toContain("ASSA-B");
  });

  it("does not call it an opportunity when no holding has a supported action", async () => {
    mockFetch({
      cockpitHoldings: [
        cockpitHolding({ ticker: "ASSA-B", caseId: "case-assa", weightPercent: 3, decisionSupport: { level: "insufficient_evidence", badgeLabel: "", statement: "" } }),
        cockpitHolding({ ticker: "VST", caseId: "case-vst", weightPercent: 3, decisionSupport: { level: "reduction_supported", badgeLabel: "", statement: "" } }),
      ],
      fitAssessments: withheldBestFit.fitAssessments.filter((f) => f.ticker !== "MA"),
    });
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() =>
      expect(screen.getByText(/Starkast underliggande förutsättningar/)).toBeInTheDocument(),
    );
    expect(screen.queryByText("Dagens största möjlighet")).not.toBeInTheDocument();
  });
});


/**
 * Portfolio Reduction-Exposure Aggregation. Each row already said
 * "Reduction supported" and each Case agreed; the share of the portfolio
 * they add up to was never stated anywhere.
 */
describe("PortfolioPage -- reduction-supported exposure", () => {
  const reducing = (ticker: string, weightPercent: number) =>
    cockpitHolding({
      ticker,
      caseId: `case-${ticker}`,
      weightPercent,
      decisionSupport: { level: "reduction_supported", badgeLabel: "", statement: "" },
    });

  it("states the total, the count and the holdings without manual arithmetic", async () => {
    mockFetch({
      cockpitHoldings: [
        reducing("AMZN", 6.6163),
        reducing("GOOG", 5.181),
        cockpitHolding({ ticker: "MSFT", caseId: "case-msft", weightPercent: 7.5636, decisionSupport: { level: "thesis_intact", badgeLabel: "", statement: "" } }),
      ],
    });
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() => expect(screen.getByText(/minskad exponering/)).toBeInTheDocument());
    const line = screen.getByText(/minskad exponering/).textContent ?? "";
    expect(line).toContain("11.8");   // 6.6163 + 5.181, MSFT excluded
    expect(line).toContain("AMZN");
    expect(line).toContain("GOOG");
    expect(line).not.toContain("MSFT");
  });

  it("says plainly that it is not an amount to sell", async () => {
    mockFetch({ cockpitHoldings: [reducing("AMZN", 6.6163)] });
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await waitFor(() =>
      expect(screen.getByText(/inte ett belopp Atlas föreslår att sälja/)).toBeInTheDocument(),
    );
  });

  it("stays quiet when no holding has a supported reduction", async () => {
    mockFetch({
      cockpitHoldings: [
        cockpitHolding({ ticker: "MSFT", caseId: "case-msft", weightPercent: 50, decisionSupport: { level: "thesis_intact", badgeLabel: "", statement: "" } }),
      ],
    });
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    // "Innehav" appears in more than one place; wait on something unique
    // to a rendered page instead.
    await waitFor(() => expect(screen.getByText("Totalt portföljvärde")).toBeInTheDocument());
    expect(screen.queryByText(/minskad exponering/)).not.toBeInTheDocument();
  });
});
