import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../testUtils";
import { PortfolioPage } from "./PortfolioPage";

/**
 * Portfolio Editing & Simulation Layer v1 -- the firewall.
 *
 * The model's own arithmetic is covered in
 * `portfolioSimulation/simulationModel.test.ts`. What these assert is
 * the product promise the arithmetic exists to keep: exploring a change
 * in the cockpit must be indistinguishable, from every persistent
 * system's point of view, from not touching the page at all.
 */

const HOLDINGS = [
  { ticker: "META", weightPercent: 40, valueAbsolute: 400000, caseId: "case-meta", reconciliationStatus: "NONE" },
  { ticker: "MA", weightPercent: 35, valueAbsolute: 350000, caseId: "case-ma", reconciliationStatus: "NONE" },
  { ticker: "MSFT", weightPercent: 25, valueAbsolute: 250000, caseId: "case-msft", reconciliationStatus: "NONE" },
];

const VIEW = {
  exists: true,
  entryMode: "IMPORTED",
  hasAbsoluteValues: true,
  holdings: HOLDINGS,
  cashWeightPercent: null,
  cashValueAbsolute: null,
  totalValue: 1000000,
  numberOfHoldings: 3,
  concentrationLevel: "Elevated",
  objective: null,
  horizon: null,
  awaitingReconciliation: false,
};

function cockpitHolding(
  ticker: string,
  caseId: string,
  weightPercent: number,
  level: string,
  valuationRisk = "high",
  financialRisk = "low",
) {
  return {
    ticker,
    caseId,
    weightPercent,
    valueAbsolute: null,
    reconciliationStatus: "NONE",
    conviction: { level: "low", reasons: [] },
    analysisCoverage: { level: "substantial_coverage", reasons: [] },
    valuation: {
      kind: "fcf_yield_relative", status: "expensive", severity: "info", supportingFacts: [],
      contradictingFacts: [], assumptions: [], missingEvidence: [], confidence: "moderate", currentYield: 0.02,
    },
    business: { growth: "moderate", capitalAllocation: "moderate" },
    businessCategories: [
      { kind: "growth", status: "moderate" },
      { kind: "capital_allocation", status: "moderate" },
      { kind: "durability", status: "moderate" },
    ],
    forwardEvidence: null,
    riskProjection: { category: "valuation_risk", status: "high" },
    riskFindings: [
      { category: "valuation_risk", status: valuationRisk },
      { category: "financial_risk", status: financialRisk },
      { category: "business_risk", status: "moderate" },
      { category: "thesis_risk", status: "insufficient_input" },
    ],
    confidence: "not_applicable",
    isThesisStale: false,
    attention: { priority: "standard_review", reasons: [] },
    decisionSupport: { level, badgeLabel: "", statement: "" },
    coverage: {
      dimensions: [], overallCoverage: "substantial_coverage", overallConfidence: "moderate",
      missingDimensions: [], notApplicableDimensions: [], reasoning: [],
    },
  };
}

const COCKPIT = [
  // META: high valuation risk, low financial risk -- the position whose
  // removal should visibly move valuation-risk exposure.
  cockpitHolding("META", "case-meta", 40, "reduction_supported", "high", "low"),
  cockpitHolding("MA", "case-ma", 35, "increase_supported", "low", "low"),
  // MSFT: Atlas could not evaluate its valuation risk. The honesty
  // control -- this weight must never count as low.
  cockpitHolding("MSFT", "case-msft", 25, "thesis_intact", "insufficient_input", "low"),
];

let fetchMock: ReturnType<typeof vi.fn>;

function mockApi() {
  fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    void init;
    const json = (body: unknown) => Promise.resolve({ ok: true, json: () => Promise.resolve(body) } as Response);
    if (url.includes("/api/alpha-portfolio/cockpit"))
      return json({ exists: true, holdings: COCKPIT, unresolvedHoldings: [], priorityReviewCount: 0 });
    if (url.includes("/api/alpha-portfolio/trade-log")) return json([]);
    if (url.includes("/api/alpha-portfolio")) return json(VIEW);
    if (url.includes("/api/portfolio-fit/holdings")) return json([]);
    if (url.includes("/api/monitoring/status"))
      return json({
        status: "idle", lastRunStartedAt: null, lastRunCompletedAt: null,
        pendingCases: [], failedCases: [],
        portfolioFreshness: { waitingForAnalysis: 0, noNewData: 3, needsAttention: 0 },
        watchlistFreshness: { waitingForAnalysis: 0, noNewData: 0, needsAttention: 0 },
      });
    if (url.includes("/api/daily-brief-agenda"))
      return json({
        generatedAt: "2026-09-17T09:00:00Z",
        summary: { holdingsCount: 3, criticalCount: 0, highCount: 0, watchlistOpportunityCount: 0, cashWeightPercent: 0, concentrationLevel: "Elevated" },
        items: [],
      });
    return json([]);
  });
  vi.stubGlobal("fetch", fetchMock);
}

/** Every request this page made that was not a plain read. The
 * simulation must never add one. */
function mutatingCalls(): string[] {
  return fetchMock.mock.calls
    .filter(([, init]) => {
      const method = String((init as RequestInit | undefined)?.method ?? "GET").toUpperCase();
      return method !== "GET" && method !== "HEAD";
    })
    .map(([input, init]) => `${String((init as RequestInit).method)} ${String(input)}`);
}

function rowEl(ticker: string): HTMLTableRowElement {
  return screen.getByRole("button", { name: `Öppna ${ticker}s vy` }).closest("tr")! as HTMLTableRowElement;
}

function row(ticker: string) {
  return within(rowEl(ticker));
}

/** Cells by position, because several columns legitimately share an
 * accessible name.
 *
 * Position Editor v1 removed the Investment column, so every index from
 * here on shifted left by one. Leaving the old map in place did not
 * fail: each index still found *a* cell, so the invariance test below
 * silently compared Risk against Valuation and Fit against the action
 * cell -- passing while checking nothing it claimed to check. Indices
 * are asserted against the header row in `cellText` for that reason. */
const CELL = { holding: 0, position: 1, atlas: 2, business: 3, risk: 4, valuation: 5, forward: 6, fit: 7, action: 8 } as const;

/** Header labels in column order, so a column added, removed or moved
 * in the page breaks this map loudly instead of shifting every
 * assertion below it onto its neighbour. */
const CELL_HEADER: Record<keyof typeof CELL, string> = {
  holding: "Innehav",
  position: "Position",
  atlas: "Atlas",
  business: "Verksamhet",
  risk: "Risk",
  valuation: "Värdering",
  forward: "Framåt",
  fit: "Passform",
  action: "Utforska position",
};

function cellText(ticker: string, cell: keyof typeof CELL): string {
  const headers = [...document.querySelectorAll("table thead th")].map((th) =>
    (th.textContent ?? "").trim(),
  );
  expect(headers[CELL[cell]], `column ${cell} is not where CELL says it is`).toBe(CELL_HEADER[cell]);
  return rowEl(ticker).querySelectorAll("td")[CELL[cell]]!.textContent ?? "";
}

/** Open a holding's Position Editor. */
async function openEditor(user: ReturnType<typeof userEvent.setup>, ticker: string) {
  await user.click(row(ticker).getByRole("button", { name: "Ändra position" }));
  return within(screen.getByRole("dialog", { name: new RegExp(`^${ticker} —`) }));
}

/** Press `−10%` inside the editor `times` times, then apply. */
async function reduce(user: ReturnType<typeof userEvent.setup>, ticker: string, times = 1) {
  const editor = await openEditor(user, ticker);
  for (let i = 0; i < times; i += 1) {
    await user.click(editor.getByRole("button", { name: "−10%" }));
  }
  await user.click(editor.getByRole("button", { name: "Tillämpa i simuleringen" }));
}

/** Set a holding's hypothetical position to an exact value. */
async function setTarget(user: ReturnType<typeof userEvent.setup>, ticker: string, value: number) {
  const editor = await openEditor(user, ticker);
  const input = editor.getByRole("spinbutton", { name: new RegExp(`Målvärde.*${ticker}`) });
  await user.clear(input);
  await user.type(input, String(value));
  await user.click(editor.getByRole("button", { name: "Tillämpa i simuleringen" }));
}

beforeEach(() => {
  mockApi();
});

describe("simulation -- baseline", () => {
  it("shows no simulation state, and no altered value, before any edit", async () => {
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    // No banner: an untouched Portfolio must look exactly as it did
    // before this layer existed.
    expect(screen.queryByText("Hypotetiskt")).not.toBeInTheDocument();
    expect(row("META").getByText("40.0%")).toBeInTheDocument();
    expect(row("META").queryByText(/→/)).not.toBeInTheDocument();
  });

  it("does not shift a percent-only portfolio's weights when it has stated cash", async () => {
    // Regression: the simulation first folded a separately-stated cash
    // weight into the denominator of a percent-only portfolio, whose
    // holdings already sum to 100. Every displayed weight moved without
    // the investor editing anything. With no edits the hypothetical
    // portfolio must be the persisted one, digit for digit.
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        const json = (body: unknown) => Promise.resolve({ ok: true, json: () => Promise.resolve(body) } as Response);
        if (url.includes("/api/alpha-portfolio/cockpit"))
          return json({ exists: true, holdings: COCKPIT, unresolvedHoldings: [], priorityReviewCount: 0 });
        if (url.includes("/api/alpha-portfolio/trade-log")) return json([]);
        if (url.includes("/api/alpha-portfolio"))
          return json({
            ...VIEW,
            hasAbsoluteValues: false,
            cashWeightPercent: 5,
            holdings: HOLDINGS.map((h) => ({ ...h, valueAbsolute: null })),
          });
        if (url.includes("/api/monitoring/status"))
          return json({
            status: "idle", lastRunStartedAt: null, lastRunCompletedAt: null, pendingCases: [], failedCases: [],
            portfolioFreshness: { waitingForAnalysis: 0, noNewData: 3, needsAttention: 0 },
            watchlistFreshness: { waitingForAnalysis: 0, noNewData: 0, needsAttention: 0 },
          });
        if (url.includes("/api/daily-brief-agenda"))
          return json({
            generatedAt: "2026-09-17T09:00:00Z",
            summary: { holdingsCount: 3, criticalCount: 0, highCount: 0, watchlistOpportunityCount: 0, cashWeightPercent: 5, concentrationLevel: "Elevated" },
            items: [],
          });
        return json([]);
      }),
    );
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    expect(cellText("META", "position")).toContain("40.0%");
    expect(cellText("MA", "position")).toContain("35.0%");
    expect(cellText("MSFT", "position")).toContain("25.0%");
    expect(cellText("META", "position")).not.toContain("→");
  });
});

describe("simulation -- editing", () => {
  it("reduces a position and states current → after", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });

    await reduce(user, "META");
    // One tenth of the persisted position: 400,000 -> 360,000, i.e.
    // 40% -> 36% of an unchanged 1,000,000 total.
    expect(row("META").getByText(/36\.0%/)).toBeInTheDocument();
    expect(row("META").getByText(/40\.0%/)).toBeInTheDocument();
    expect(screen.getByText("Hypotetiskt")).toBeInTheDocument();
  });

  it("leaves every other holding's position untouched", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    await reduce(user, "META");
    // The freed capital becomes unallocated; it is not redistributed,
    // so reducing META is not silently a decision to increase MA.
    expect(row("MA").getByText("35.0%")).toBeInTheDocument();
    expect(row("MSFT").getByText("25.0%")).toBeInTheDocument();
  });

  it("removes a position to zero without removing the row", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    await reduce(user, "META", 10);
    expect(cellText("META", "position")).toContain("→ 0.0%");
    // Still a row, still restorable -- removal is a value of zero, never
    // a deletion.
    const editor = await openEditor(user, "META");
    expect(editor.getByRole("button", { name: "Återställ nuvarande position" })).toBeInTheDocument();
  });

  it("restores one position exactly, leaving the rest explored", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    await reduce(user, "META");
    await reduce(user, "MSFT");
    const editor = await openEditor(user, "META");
    await user.click(editor.getByRole("button", { name: "Återställ nuvarande position" }));
    await user.click(editor.getByRole("button", { name: "Tillämpa i simuleringen" }));
    expect(row("META").getByText("40.0%")).toBeInTheDocument();
    expect(row("META").queryByText(/→/)).not.toBeInTheDocument();
    expect(screen.getByText("Hypotetiskt")).toBeInTheDocument();
  });

  it("resets everything to the persisted portfolio", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    await reduce(user, "META", 3);
    await reduce(user, "MSFT", 2);
    await user.click(screen.getByRole("button", { name: "Återställ till nuvarande portfölj" }));

    expect(screen.queryByText("Hypotetiskt")).not.toBeInTheDocument();
    expect(row("META").getByText("40.0%")).toBeInTheDocument();
    expect(row("MA").getByText("35.0%")).toBeInTheDocument();
    expect(row("MSFT").getByText("25.0%")).toBeInTheDocument();
  });

  it("cannot increase a fully invested portfolio until something is reduced", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    // Nothing unallocated: the control says so by being disabled rather
    // than accepting the click and silently clamping it.
    let editor = await openEditor(user, "MA");
    expect(editor.getByRole("button", { name: "+10%" })).toBeDisabled();
    await user.click(editor.getByRole("button", { name: "Avbryt" }));

    await reduce(user, "META");
    editor = await openEditor(user, "MA");
    expect(editor.getByRole("button", { name: "+10%" })).toBeEnabled();
    await user.click(editor.getByRole("button", { name: "+10%" }));
    await user.click(editor.getByRole("button", { name: "Tillämpa i simuleringen" }));
    expect(cellText("MA", "position")).toContain("38.5%");
  });
});

describe("simulation -- the edit unit is explicit", () => {
  it("shows the step on the control, never a bare plus or minus", async () => {
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });

    // Atlas holds no share quantities for any holding, so a bare "−"
    // would read as "one share" -- the single interpretation the data
    // cannot support. The control states its own unit.
    // The row now carries one compact action; the steps live inside the
    // editor, where the position and its value are named.
    expect(row("META").getByRole("button", { name: "Ändra position" })).toBeInTheDocument();
    expect(rowEl("META").textContent).not.toContain("−10%");

    const user = userEvent.setup();
    const editor = await openEditor(user, "META");
    expect(editor.getByRole("button", { name: "−10%" }).textContent).toBe("−10%");
    expect(editor.getByRole("button", { name: "+10%" }).textContent).toBe("+10%");
  });

  it("names the unit, and never a share, in its accessible label", async () => {
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    const user = userEvent.setup();
    await openEditor(user, "META");
    // The dialog names the holding; the unit is money, never shares.
    expect(screen.getByRole("dialog", { name: "META — hypotetisk position" })).toBeInTheDocument();
    const text = screen.getByRole("dialog").textContent ?? "";
    expect(text).not.toMatch(/aktier|share/i);
    // And nothing that reads as a real trade.
    expect(text).not.toMatch(/köp|sälj|order|verkställ/i);
  });

  it("steps against the persisted position, not the latest hypothetical one", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });

    // Compounding 10% against each new value would give 400,000 ->
    // 360,000 -> 324,000 and never reach zero. Anchored to the
    // persisted position it is a flat 40,000 a step.
    await reduce(user, "META");
    expect(cellText("META", "position")).toContain("$360,000");
    await reduce(user, "META");
    expect(cellText("META", "position")).toContain("$320,000");
    await reduce(user, "META");
    expect(cellText("META", "position")).toContain("$280,000");
  });

  it("reaches exactly zero in ten reductions, and stops there", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });

    await reduce(user, "META", 10);
    expect(cellText("META", "position")).toContain("→ $0");
    expect(cellText("META", "position")).toContain("→ 0.0%");
    // And cannot be pushed below it: a further reduction floors at zero
    // rather than creating a short position.
    await reduce(user, "META", 2);
    expect(cellText("META", "position")).toContain("→ $0");
  });
});

describe("simulation -- what may and may not react", () => {
  it("recomputes reduction-supported exposure from the hypothetical weights", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    // Matched against the exposure sentence itself, not the page: a
    // looser match passes even when the aggregate is still reading the
    // persisted weight, which is exactly the mutation this must catch.
    const exposure = () =>
      [...document.querySelectorAll("p,span,div")]
        .map((e) => e.textContent ?? "")
        .find((text) => /av portföljvärdet/.test(text)) ?? "";

    // META alone is reduction-supported, at 40% of the portfolio.
    expect(exposure()).toContain("40.0 %");
    await reduce(user, "META", 5);
    // Halved: the aggregate follows the hypothetical weight. This is
    // the one aggregate safe to recompute -- arithmetic over a weight
    // and an already-published decision-support level, no analysis
    // redone anywhere.
    expect(exposure()).toContain("20.0 %");
    await reduce(user, "META", 5);
    // Removed entirely: its weight leaves the aggregate completely.
    expect(exposure()).toContain("0.0 %");
  });

  it("leaves every analytical verdict exactly as the engine published it", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    const columns = ["atlas", "business", "risk", "valuation", "forward", "fit"] as const;
    const before = Object.fromEntries(columns.map((c) => [c, cellText("META", c)]));

    await reduce(user, "META", 5);

    // Position size changed; what Atlas concluded about the security did
    // not, because none of it is a function of position size. Nothing
    // here is recomputed in the frontend, and nothing may appear to be
    // -- including Portfolio Fit, which this sprint deliberately does
    // not re-derive for a hypothetical portfolio.
    for (const column of columns) {
      expect(cellText("META", column), `${column} must not react to position size`).toBe(before[column]);
    }
    // The position itself did change, so the test is not passing
    // vacuously against a page that ignored the edit.
    expect(cellText("META", "position")).toContain("→");
  });
});

describe("simulation -- one canonical state", () => {
  it("keeps every weight-derived summary consistent with the rows", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    const page = () => document.body.textContent ?? "";

    expect(page()).toContain("META (40.0%)");
    await reduce(user, "META", 5);

    // Largest position, the concentration list and unallocated capital
    // all read the same hypothetical portfolio the rows do. A summary
    // still claiming META at 40% while its row says 20% would be two
    // answers to one question.
    expect(cellText("META", "position")).toContain("→ 20.0%");
    expect(page()).toContain("MA (35.0%)");
    expect(page()).not.toContain("META (40.0%)");
    // The freed capital is visible as unallocated rather than silently
    // vanishing from the portfolio.
    expect(page()).toContain("20.0%");
    // Total value is conserved throughout: value moved, it did not
    // disappear.
    expect(page()).toContain("$1,000,000");
  });
});

describe("position editor", () => {
  function impact(dialog: HTMLElement, label: string): string {
    const row = [...dialog.querySelectorAll("div")].find((d) => (d.textContent ?? "").startsWith(label));
    return row?.textContent ?? "";
  }

  it("opens without touching the simulation", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });

    await openEditor(user, "META");
    // Opening is not an edit: no banner, no changed value.
    expect(screen.queryByText("Hypotetiskt")).not.toBeInTheDocument();
    expect(cellText("META", "position")).not.toContain("→");
  });

  it("discards the draft on Cancel", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });

    const editor = await openEditor(user, "META");
    await user.click(editor.getByRole("button", { name: "−10%" }));
    await user.click(editor.getByRole("button", { name: "−10%" }));
    await user.click(editor.getByRole("button", { name: "Avbryt" }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.queryByText("Hypotetiskt")).not.toBeInTheDocument();
    expect(cellText("META", "position")).not.toContain("→");
  });

  it("closes on Escape without applying", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    const editor = await openEditor(user, "META");
    await user.click(editor.getByRole("button", { name: "−10%" }));
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(cellText("META", "position")).not.toContain("→");
  });

  it("accepts a typed target value", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    await setTarget(user, "META", 300000);
    // 300,000 of a 1,000,000 portfolio.
    expect(cellText("META", "position")).toContain("→ 30.0%");
    expect(cellText("META", "position")).toContain("$300,000");
  });

  it("previews the portfolio impact before anything is applied", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });

    const editor = await openEditor(user, "META");
    await user.click(editor.getByRole("button", { name: "−10%" }));
    const dialog = screen.getByRole("dialog");

    // Position, weight and freed capital.
    expect(impact(dialog, "Positionens värde")).toContain("$360,000");
    expect(impact(dialog, "Portföljandel")).toContain("36.0%");
    expect(impact(dialog, "Oallokerat kapital")).toContain("4.0%");
    // The supported assessment dimensions, and only those.
    expect(impact(dialog, "Koncentration")).toContain("Hög");
    expect(impact(dialog, "Exponering mot värderingsrisk")).toContain("36.0%");
    expect(impact(dialog, "Exponering mot finansiell risk")).toBeTruthy();
    expect(dialog.textContent).not.toMatch(/Förväntad avkastning|Volatilitet|Sektor|AI-beroende/);

    // And none of it has touched the live simulation yet.
    expect(screen.queryByText("Hypotetiskt")).not.toBeInTheDocument();
    expect(cellText("META", "position")).not.toContain("→");
  });

  it("previews against the portfolio as it already stands, not the persisted baseline", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });

    // Remove META first, then open MSFT: its weight preview must be
    // computed against a portfolio that no longer holds META.
    await reduce(user, "META", 10);
    const editor = await openEditor(user, "MSFT");
    await user.click(editor.getByRole("button", { name: "−10%" }));
    const dialog = screen.getByRole("dialog");
    // MSFT 250,000 -> 225,000 of an unchanged 1,000,000 total.
    expect(impact(dialog, "Positionens värde")).toContain("$225,000");
    // Unallocated already holds META's 40%, and gains MSFT's 2.5%.
    expect(impact(dialog, "Oallokerat kapital")).toContain("40.0% → 42.5%");
  });

  it("will not spend capital the simulation does not have", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    // Fully invested: a target above the current position cannot be
    // funded, and the editor says so rather than silently clamping.
    const editor = await openEditor(user, "MA");
    const input = editor.getByRole("spinbutton", { name: /Målvärde/ });
    await user.clear(input);
    await user.type(input, "500000");
    expect(screen.getByRole("dialog").textContent).toMatch(/Begränsas av tillgängligt oallokerat kapital/);
    await user.click(editor.getByRole("button", { name: "Tillämpa i simuleringen" }));
    // The model floors it at what was fundable -- nothing was created.
    expect(cellText("MA", "position")).toContain("35.0%");
  });

  it("steps by a tenth of the persisted position, never compounding the draft", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    const editor = await openEditor(user, "META");
    await user.click(editor.getByRole("button", { name: "−10%" }));
    await user.click(editor.getByRole("button", { name: "−10%" }));
    await user.click(editor.getByRole("button", { name: "−10%" }));
    // 400,000 - 3 x 40,000. Compounding would give 291,600.
    expect(impact(screen.getByRole("dialog"), "Positionens värde")).toContain("$280,000");
  });
});

describe("portfolio assessment", () => {
  /** The assessment row for a factor, by its visible name. */
  function factor(name: string) {
    const cell = [...document.querySelectorAll("td")].find((td) => td.textContent?.trim() === name);
    return (cell!.closest("tr") as HTMLTableRowElement).textContent ?? "";
  }

  it("states the current portfolio's properties before any edit", async () => {
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });

    expect(screen.getByText("Portföljbedömning")).toBeInTheDocument();
    // META is 40% -- past Atlas's own canonical 35% "high" line, the
    // one dimension whose label comes from existing doctrine.
    expect(factor("Koncentration")).toContain("Hög");
    expect(factor("Koncentration")).toContain("META 40.0%");
    // META alone carries high valuation risk, reported numerically.
    expect(factor("Exponering mot värderingsrisk")).toContain("40.0% av portföljen bedömd som hög");
    // MSFT's 25% could not be evaluated, and says so rather than
    // counting as low.
    expect(factor("Exponering mot värderingsrisk")).toContain("25.0% inte bedömd");
    // No "After change" column until something is explored.
    expect(screen.queryByText("Efter ändring")).not.toBeInTheDocument();
  });

  it("shows current, after and effect once a change is explored", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });

    await reduce(user, "META", 2); // 40% -> 32%
    expect(screen.getByText("Efter ändring")).toBeInTheDocument();

    // Valuation-risk exposure falls and says so in words, not by colour
    // or an arrow alone.
    const valuation = factor("Exponering mot värderingsrisk");
    expect(valuation).toContain("40.0% av portföljen bedömd som hög → 32.0%");
    expect(valuation).toContain("Förbättrad");
    // Attribution names the position that moved, with its real weights.
    expect(valuation).toContain("främst META 40.0% → 32.0%");

    // Concentration improves too: the largest position is now 35% MA.
    const concentration = factor("Koncentration");
    expect(concentration).toContain("MA 35.0%");
    expect(concentration).toContain("Förbättrad");
  });

  it("states the exposure as a number, never as an invented band", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });

    // Concentration carries a word because Atlas's own 35/25/75 ladder
    // is existing doctrine. The exposures carry numbers, because Atlas
    // has never set a standard for how much high-rated exposure is too
    // much -- a band here would have invented one.
    expect(factor("Koncentration")).toContain("Hög");
    const before = factor("Exponering mot värderingsrisk");
    expect(before).toContain("40.0%");
    expect(before).not.toMatch(/Förhöjd|Måttlig|Inte bedömd/);

    await reduce(user, "META", 10);
    const after = factor("Exponering mot värderingsrisk");
    // Thin coverage is disclosed beside the numbers rather than
    // blocking them: 25% of the portfolio has no valuation-risk verdict
    // and the row says so, while still reporting what it did measure.
    expect(after).toContain("40.0%");
    expect(after).toContain("0.0%");
    expect(after).toContain("Förbättrad");
    expect(after).toContain("25.0% inte bedömd");
  });

  it("does not let a removed holding keep contributing", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    await reduce(user, "META", 10);
    // The mutation this kills: a position at zero still counted in the
    // exposure it no longer creates.
    expect(factor("Exponering mot värderingsrisk")).toContain("→ 0.0%");
    // And out of concentration: MA becomes the largest position.
    expect(factor("Koncentration")).toContain("MA 35.0%");
  });

  it("treats a small reduction proportionally, not as a dramatic swing", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    await reduce(user, "META", 1); // 40% -> 36%
    const valuation = factor("Exponering mot värderingsrisk");
    expect(valuation).toContain("40.0% av portföljen bedömd som hög → 36.0%");
    // A real 4-point move, so it is reported -- but the band is
    // unchanged, and the row says both.
    expect(valuation).toContain("Förbättrad");
    expect(factor("Koncentration")).toContain("Hög");
  });

  it("returns exactly to the current assessment on reset", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    const before = factor("Exponering mot värderingsrisk");
    await reduce(user, "META", 4);
    await user.click(screen.getByRole("button", { name: "Återställ till nuvarande portfölj" }));
    // No stale "After change" column, no stale comparison.
    expect(screen.queryByText("Efter ändring")).not.toBeInTheDocument();
    expect(factor("Exponering mot värderingsrisk")).toBe(before);
  });

  it("assesses no dimension Atlas has no data for", async () => {
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    const page = document.body.textContent ?? "";
    // No fabricated expected return, volatility, thematic exposure or
    // single overall score -- and the page says why they are absent.
    expect(page).not.toMatch(/Förväntad avkastning|Volatilitet|AI-beroende|Ränte känslighet|Portföljbetyg/);
    expect(page).toContain("bedöms inte");
    // Sector and geography are named as unassessed rather than shown as
    // rows promising a dimension Atlas has no path to.
    expect(page).toMatch(/Sektor- och geografisk spridning/);
  });
});

describe("simulation -- persistence firewall", () => {
  it("makes no mutating request at all, however much is explored", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    const beforeCount = fetchMock.mock.calls.length;

    await reduce(user, "META", 10);
    await reduce(user, "MSFT", 4);
    await setTarget(user, "MA", 360000);
    const editor = await openEditor(user, "META");
    await user.click(editor.getByRole("button", { name: "Återställ nuvarande position" }));
    await user.click(editor.getByRole("button", { name: "Tillämpa i simuleringen" }));
    await user.click(screen.getByRole("button", { name: "Återställ till nuvarande portfölj" }));

    // No POST/PUT/PATCH/DELETE anywhere: not to the portfolio, not to
    // decisions or outcomes, not to anything. That covers the portfolio
    // rows, Decision Memory, the Daily Brief change log, history
    // snapshots and every provider behind them in one assertion --
    // none of them can be written without a request leaving here.
    expect(mutatingCalls()).toEqual([]);
    // And no new request of any kind: the whole simulation is local
    // arithmetic over data already fetched, so it needs no round trip.
    expect(fetchMock.mock.calls.length).toBe(beforeCount);
  });

  it("never re-requests the portfolio, so the persisted state is never re-read or rewritten", async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioPage />, { route: "/portfolio" });
    await screen.findByRole("button", { name: "Öppna METAs vy" });
    const portfolioCalls = () =>
      fetchMock.mock.calls.filter(([input]) => String(input).includes("/api/alpha-portfolio")).length;
    const before = portfolioCalls();
    await reduce(user, "META", 3);
    expect(portfolioCalls()).toBe(before);
  });
});

