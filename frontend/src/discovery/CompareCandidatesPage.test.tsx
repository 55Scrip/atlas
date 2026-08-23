import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "../testUtils";
import { CompareCandidatesPage } from "./CompareCandidatesPage";

function dimension(kind: string, rating: string) {
  return { kind, rating, reasoning: [`${kind} reasoning`], unavailableReason: null };
}

function assessment(ticker: string, overall: string) {
  return {
    caseId: `case-${ticker}`,
    ticker,
    isExistingHolding: false,
    currentWeightPercent: null,
    overall,
    overallReasoning: [`${ticker} overall reasoning`],
    dimensions: [dimension("business", "good"), dimension("risk", "weak")],
    trend: "unavailable",
    dataGaps: [],
    generatedAt: "2026-01-01T00:00:00Z",
  };
}

// `/api/portfolio-fit/holdings` is already sorted best-first by the
// backend (`PortfolioFitService.assess_all_holdings`) -- the fixture
// preserves that order so "weakest" (last) resolves to AAPL.
const HOLDINGS_RESPONSE = [assessment("MSFT", "good"), assessment("AAPL", "weak")];
const STATUS_RESPONSE = { summary: { largestPositionTicker: "MSFT" } };

function mockFetch(compareResult: unknown = null, compareStatus = 200, stanceCompareResult: unknown = null) {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/portfolio-fit/holdings")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(HOLDINGS_RESPONSE) } as Response);
      }
      if (url.includes("/api/alpha-portfolio/status")) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(STATUS_RESPONSE) } as Response);
      }
      if (url.includes("/api/portfolio-fit/compare")) {
        return Promise.resolve({
          ok: compareStatus !== 404,
          status: compareStatus,
          json: () => Promise.resolve(compareResult),
        } as Response);
      }
      if (url.includes("/api/stance/compare")) {
        return Promise.resolve({
          ok: stanceCompareResult !== null,
          status: stanceCompareResult !== null ? 200 : 404,
          json: () => Promise.resolve(stanceCompareResult),
        } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
}

function stance(level: string) {
  return {
    level,
    reasoning: [{ code: "thesis_unchanged" }],
    supportingSignals: [],
    limitingSignals: [],
    confidence: "high",
    missingInformation: [],
  };
}

describe("CompareCandidatesPage", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the honest empty state when no candidate is selected", () => {
    mockFetch();
    renderWithProviders(<CompareCandidatesPage />, { route: "/discovery/compare" });
    expect(
      screen.getByText('Ingen kandidat vald. Öppna en kandidat från Discovery och välj "Jämför" för att börja.'),
    ).toBeInTheDocument();
  });

  it("offers weakest-holding and largest-concentration quick picks once one candidate is chosen", async () => {
    mockFetch();
    renderWithProviders(<CompareCandidatesPage />, { route: "/discovery/compare?a=NVDA" });
    await waitFor(() => expect(screen.getByText("Ditt innehav med svagast passform (AAPL)")).toBeInTheDocument());
    expect(screen.getByText("Din största position (MSFT)")).toBeInTheDocument();
  });

  it("never offers a 'similar holding' quick pick, disclosing why instead", async () => {
    mockFetch();
    renderWithProviders(<CompareCandidatesPage />, { route: "/discovery/compare?a=NVDA" });
    await waitFor(() =>
      expect(
        screen.getByText(
          'Atlas jämför inte mot ett "liknande" innehav: det finns ingen sektor- eller branschdata för att avgöra likhet på ett ärligt sätt.',
        ),
      ).toBeInTheDocument(),
    );
  });

  it("renders both columns and the qualitative conclusion once both tickers resolve", async () => {
    mockFetch({
      assessmentA: assessment("NVDA", "good"),
      assessmentB: assessment("AAPL", "weak"),
      preferredTicker: "NVDA",
      reasoning: ["NVDA rates Good overall, AAPL rates Weak."],
    });
    renderWithProviders(<CompareCandidatesPage />, { route: "/discovery/compare?a=NVDA&b=AAPL" });

    await waitFor(() => expect(screen.getByText("NVDA passar bättre")).toBeInTheDocument());
    expect(screen.getByText("NVDA rates Good overall, AAPL rates Weak.")).toBeInTheDocument();
  });

  it("shows a tie conclusion when preferredTicker is null, never forcing a winner", async () => {
    mockFetch({
      assessmentA: assessment("NVDA", "good"),
      assessmentB: assessment("AAPL", "good"),
      preferredTicker: null,
      reasoning: ["Both companies rate Good overall."],
    });
    renderWithProviders(<CompareCandidatesPage />, { route: "/discovery/compare?a=NVDA&b=AAPL" });

    await waitFor(() => expect(screen.getByText("Ingen passar tydligt bättre")).toBeInTheDocument());
  });

  it("shows the insufficient-data message when the backend has no assessment for one ticker", async () => {
    mockFetch(null, 404);
    renderWithProviders(<CompareCandidatesPage />, { route: "/discovery/compare?a=NVDA&b=ZZZZ" });

    await waitFor(() =>
      expect(
        screen.getByText("Atlas har inte tillräckligt med information för att jämföra dessa bolag på ett tillförlitligt sätt än."),
      ).toBeInTheDocument(),
    );
  });

  it("shows a distinct real-error message when the fetch actually fails, never the same copy as insufficient-data (Deliverable 13)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/portfolio-fit/compare")) return Promise.reject(new Error("network down"));
        if (url.includes("/api/portfolio-fit/holdings")) return Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response);
        if (url.includes("/api/alpha-portfolio/status")) return Promise.resolve({ ok: true, json: () => Promise.resolve({ summary: null }) } as Response);
        return Promise.reject(new Error(`Unexpected fetch: ${url}`));
      }),
    );
    renderWithProviders(<CompareCandidatesPage />, { route: "/discovery/compare?a=NVDA&b=ZZZZ" });
    await waitFor(() => expect(screen.getByText("Atlas kunde inte läsa in den här jämförelsen. Försök att uppdatera sidan.")).toBeInTheDocument());
    expect(screen.queryByText("Atlas har inte tillräckligt med information för att jämföra dessa bolag på ett tillförlitligt sätt än.")).not.toBeInTheDocument();
  });

  describe("Stance comparison (Atlas Intelligence Sprint 2, Deliverable 9)", () => {
    it("shows Atlas's View section with both Stance badges once both tickers resolve", async () => {
      mockFetch(
        { assessmentA: assessment("NVDA", "good"), assessmentB: assessment("AAPL", "weak"), preferredTicker: "NVDA", reasoning: ["x"] },
        200,
        {
          tickerA: "NVDA",
          stanceA: stance("increase"),
          tickerB: "AAPL",
          stanceB: stance("reduce"),
          preferredTicker: "NVDA",
          reasoning: [{ code: "preferred_has_a_more_favorable_stance", ticker: "NVDA" }],
        },
      );
      renderWithProviders(<CompareCandidatesPage />, { route: "/discovery/compare?a=NVDA&b=AAPL" });
      await waitFor(() => expect(screen.getByText("Atlas syn")).toBeInTheDocument());
      expect(screen.getByText("Synen har stärkts")).toBeInTheDocument();
      expect(screen.getByText("Synen har försvagats")).toBeInTheDocument();
      expect(screen.getByText("NVDA har för närvarande den mer fördelaktiga synen.")).toBeInTheDocument();
    });

    it("disambiguates when Stance cannot compare but Portfolio Fit still names a preferred ticker (live-verification finding)", async () => {
      mockFetch(
        { assessmentA: assessment("NVDA", "good"), assessmentB: assessment("AAPL", "weak"), preferredTicker: "NVDA", reasoning: ["x"] },
        200,
        {
          tickerA: "NVDA",
          stanceA: stance("avoid_decision"),
          tickerB: "AAPL",
          stanceB: stance("avoid_decision"),
          preferredTicker: null,
          reasoning: [{ code: "one_or_both_too_uncertain_to_compare", ticker: null }],
        },
      );
      renderWithProviders(<CompareCandidatesPage />, { route: "/discovery/compare?a=NVDA&b=AAPL" });
      await waitFor(() => expect(screen.getByText("NVDA passar bättre")).toBeInTheDocument());
      expect(
        screen.getByText(
          "Detta avser endast hur respektive bolags dimensioner för närvarande värderas mot din portfölj, inte Atlas övergripande rekommendation ovan.",
        ),
      ).toBeInTheDocument();
    });

    it("never shows the disambiguation note when Stance and Fit agree", async () => {
      mockFetch(
        { assessmentA: assessment("NVDA", "good"), assessmentB: assessment("AAPL", "weak"), preferredTicker: "NVDA", reasoning: ["x"] },
        200,
        {
          tickerA: "NVDA",
          stanceA: stance("increase"),
          tickerB: "AAPL",
          stanceB: stance("reduce"),
          preferredTicker: "NVDA",
          reasoning: [{ code: "preferred_has_a_more_favorable_stance", ticker: "NVDA" }],
        },
      );
      renderWithProviders(<CompareCandidatesPage />, { route: "/discovery/compare?a=NVDA&b=AAPL" });
      await waitFor(() => expect(screen.getByText("NVDA passar bättre")).toBeInTheDocument());
      expect(
        screen.queryByText(
          "Detta avser endast hur respektive bolags dimensioner för närvarande värderas mot din portfölj, inte Atlas övergripande rekommendation ovan.",
        ),
      ).not.toBeInTheDocument();
    });

    it("never forces a winner when Atlas cannot honestly choose", async () => {
      mockFetch(
        { assessmentA: assessment("NVDA", "good"), assessmentB: assessment("AAPL", "good"), preferredTicker: null, reasoning: ["x"] },
        200,
        {
          tickerA: "NVDA",
          stanceA: stance("wait"),
          tickerB: "AAPL",
          stanceB: stance("wait"),
          preferredTicker: null,
          reasoning: [{ code: "one_or_both_too_uncertain_to_compare", ticker: null }],
        },
      );
      renderWithProviders(<CompareCandidatesPage />, { route: "/discovery/compare?a=NVDA&b=AAPL" });
      await waitFor(() =>
        expect(
          screen.getByText(
            "Atlas kan för närvarande inte rekommendera det ena bolaget framför det andra eftersom minst ett av dem har begränsad analystäckning.",
          ),
        ).toBeInTheDocument(),
      );
    });
  });

  it("states plainly what is being compared once both tickers are chosen (Deliverable 10)", async () => {
    mockFetch({
      assessmentA: assessment("NVDA", "good"),
      assessmentB: assessment("AAPL", "weak"),
      preferredTicker: "NVDA",
      reasoning: ["NVDA rates Good overall, AAPL rates Weak."],
    });
    renderWithProviders(<CompareCandidatesPage />, { route: "/discovery/compare?a=NVDA&b=AAPL" });
    await waitFor(() => expect(screen.getByText("Jämför NVDA mot AAPL.")).toBeInTheDocument());
  });
});
