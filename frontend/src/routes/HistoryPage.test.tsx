import { describe, expect, it, vi, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../testUtils";
import { HistoryPage } from "./HistoryPage";
import { __resetAlphaPortfolioCacheForTests } from "../portfolio/alphaPortfolioData";

const EMPTY_ANALYTICAL = { generatedAt: "2026-01-01T00:00:00Z", entries: [] };
const EMPTY_OBSERVED_PROPERTIES = { properties: [] };

function analyticalEntry(overrides: Record<string, unknown> = {}) {
  return {
    caseId: "case-aapl",
    ticker: "AAPL",
    snapshotId: "snap-1",
    capturedAt: "2026-01-01T00:00:00Z",
    isBaseline: true,
    thesisImpact: "unchanged",
    summary: "Baseline established.",
    changeCount: 0,
    changes: [],
    atlasThesisNarrative: null,
    atlasThesisPosture: null,
    strengths: [],
    risks: [],
    openQuestions: [],
    businessCategoryStates: [],
    riskCategoryStates: [],
    valuationStatus: "not_evaluated",
    currentYield: null,
    ...overrides,
  };
}

function decisionSnapshot(overrides: Record<string, unknown> = {}) {
  return {
    caseId: "case-aapl",
    action: "hold",
    readinessStatus: "ready",
    blockerCodes: [],
    convictionStrength: "moderate",
    convictionStability: "stable",
    decisionPathStepCount: 1,
    decisionPathFinalState: "investable",
    primaryAlternativeKind: null,
    alternativeCount: 0,
    contentHash: "hash-1",
    recordedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function decisionMemoryChange(overrides: Record<string, unknown> = {}) {
  return {
    caseId: "case-aapl",
    isBaseline: false,
    previousAction: "wait",
    currentAction: "hold",
    recommendationChanged: true,
    convictionDirection: null,
    readinessDirection: null,
    decisionPathDirection: null,
    blockersResolved: [],
    blockersAdded: [],
    alternativeChanged: false,
    detectedAt: "2026-01-02T00:00:00Z",
    ...overrides,
  };
}

function decisionMemoryView(overrides: Record<string, unknown> = {}) {
  const current = decisionSnapshot({ recordedAt: "2026-01-02T00:00:00Z", contentHash: "hash-2" });
  const change = decisionMemoryChange();
  return {
    caseId: "case-aapl",
    currentSnapshot: current,
    previousSnapshot: decisionSnapshot(),
    latestChange: change,
    history: {
      caseId: "case-aapl",
      entries: [
        { snapshot: decisionSnapshot(), change: decisionMemoryChange({ isBaseline: true, previousAction: null, recommendationChanged: false, currentAction: "wait", detectedAt: "2026-01-01T00:00:00Z" }) },
        { snapshot: current, change },
      ],
    },
    ...overrides,
  };
}

function mockFetch(
  overrides: {
    decisions?: unknown[];
    outcomes?: unknown[];
    trades?: unknown[];
    holdings?: unknown[];
    analytical?: unknown;
    decisionMemoryByCaseId?: Record<string, { status: number; body?: unknown }>;
  } = {},
) {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/decisions")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.decisions ?? []) } as Response);
      }
      if (url.includes("/api/outcomes")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.outcomes ?? []) } as Response);
      }
      if (url.includes("/api/alpha-portfolio/trade-log")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.trades ?? []) } as Response);
      }
      if (url.includes("/api/alpha-portfolio")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ holdings: overrides.holdings ?? [] }) } as Response);
      }
      if (url.includes("/api/history/analysis")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(overrides.analytical ?? EMPTY_ANALYTICAL) } as Response);
      }
      if (url.includes("/api/observed-decision-properties")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(EMPTY_OBSERVED_PROPERTIES) } as Response);
      }
      const decisionMemoryMatch = url.match(/\/api\/decision-memory\/([^/]+)$/);
      if (decisionMemoryMatch?.[1]) {
        const caseId = decodeURIComponent(decisionMemoryMatch[1]);
        const entry = overrides.decisionMemoryByCaseId?.[caseId];
        if (!entry) return Promise.resolve({ ok: false, status: 404 } as Response);
        return Promise.resolve({ ok: entry.status < 400, status: entry.status, json: () => Promise.resolve(entry.body) } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
}

describe("HistoryPage Decision Memory timeline (Product Intelligence Sprint 4 -- History & Decision Memory Activation)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    __resetAlphaPortfolioCacheForTests();
  });

  it("surfaces a real Decision Memory change -- previously computed and never shown in History", async () => {
    mockFetch({
      analytical: { generatedAt: "2026-01-01T00:00:00Z", entries: [analyticalEntry()] },
      decisionMemoryByCaseId: { "case-aapl": { status: 200, body: decisionMemoryView() } },
    });
    renderWithProviders(<HistoryPage />, { route: "/history" });
    await waitFor(() =>
      expect(screen.getByText("Rekommendationen ändrades från Vänta till Behåll.", { exact: false })).toBeInTheDocument(),
    );
  });

  it("shows the baseline entry as a real, honest first-recorded fact, not a fabricated change", async () => {
    mockFetch({
      analytical: { generatedAt: "2026-01-01T00:00:00Z", entries: [analyticalEntry()] },
      decisionMemoryByCaseId: { "case-aapl": { status: 200, body: decisionMemoryView() } },
    });
    renderWithProviders(<HistoryPage />, { route: "/history" });
    const matches = await screen.findAllByText("Det här är det första registrerade beslutet för det här caset.", { exact: false });
    expect(matches.length).toBeGreaterThan(0);
  });

  it("discloses companies with no recorded decision yet, separately from a real change", async () => {
    mockFetch({
      analytical: { generatedAt: "2026-01-01T00:00:00Z", entries: [analyticalEntry({ caseId: "case-msft", ticker: "MSFT" })] },
      decisionMemoryByCaseId: {},
    });
    renderWithProviders(<HistoryPage />, { route: "/history" });
    await waitFor(() => expect(screen.getByText("1 bolag saknar ännu ett registrerat beslut.")).toBeInTheDocument());
  });

  it("expands to show the full set of decision facts, reusing the same rendering Investment Case already uses", async () => {
    mockFetch({
      analytical: { generatedAt: "2026-01-01T00:00:00Z", entries: [analyticalEntry()] },
      decisionMemoryByCaseId: {
        "case-aapl": {
          status: 200,
          body: decisionMemoryView({
            history: {
              caseId: "case-aapl",
              entries: [
                {
                  snapshot: decisionSnapshot({ recordedAt: "2026-01-02T00:00:00Z", contentHash: "hash-2" }),
                  change: decisionMemoryChange({ blockersResolved: ["insufficient_evidence"] }),
                },
              ],
            },
          }),
        },
      },
    });
    const user = userEvent.setup();
    renderWithProviders(<HistoryPage />, { route: "/history" });
    // The decision-memory row (recorded 2026-01-02) sorts ahead of the
    // analytical row (captured 2026-01-01) under the page's own default
    // "newest first" order -- both row kinds render a "Visa detaljer"
    // toggle, so the first match is deterministically this row's own.
    await waitFor(() => expect(screen.getAllByText("Visa detaljer").length).toBe(2));
    const [firstToggle] = screen.getAllByText("Visa detaljer");
    await user.click(firstToggle!);
    expect(await screen.findByText(/Löst:/)).toBeInTheDocument();
  });

  it("filters the timeline to only Decision Record Changes when that scope is selected", async () => {
    mockFetch({
      analytical: { generatedAt: "2026-01-01T00:00:00Z", entries: [analyticalEntry()] },
      decisionMemoryByCaseId: { "case-aapl": { status: 200, body: decisionMemoryView() } },
    });
    const user = userEvent.setup();
    renderWithProviders(<HistoryPage />, { route: "/history" });
    await waitFor(() => expect(screen.getByText("Rekommendationen ändrades från Vänta till Behåll.", { exact: false })).toBeInTheDocument());
    await user.click(screen.getByText("Förändringar i beslutsunderlag"));
    expect(screen.queryByText("Baslinje etablerad")).not.toBeInTheDocument();
    expect(screen.getByText("Rekommendationen ändrades från Vänta till Behåll.", { exact: false })).toBeInTheDocument();
  });
});
