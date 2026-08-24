import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "../testUtils";
import { DashboardPage } from "./DashboardPage";
import { __resetAlphaPortfolioCacheForTests } from "../portfolio/alphaPortfolioData";

/** Status/Explanation Language stabilization: Needs Attention, Recent
 * Activity, and Continue Working all require decisions + outcomes +
 * trade-log + the shared portfolio cache to be loaded before they can
 * derive anything real -- these tests simulate one of those four
 * permanently failing, and confirm the three sections report an
 * honest error instead of showing "Loading…" forever. */

function portfolioBody(overrides: Record<string, unknown> = {}) {
  return {
    exists: true,
    numberOfHoldings: 1,
    cashWeightPercent: null,
    holdings: [{ ticker: "AAPL", caseId: "case-aapl" }],
    ...overrides,
  };
}

function mockFetch(opts: {
  decisions?: "ok" | "error";
  outcomes?: "ok" | "error";
  tradeLog?: "ok" | "error";
  portfolio?: "ok" | "error";
} = {}) {
  const { decisions = "ok", outcomes = "ok", tradeLog = "ok", portfolio = "ok" } = opts;
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/decisions")) {
        return decisions === "ok"
          ? Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response)
          : Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve(null) } as Response);
      }
      if (url.includes("/api/outcomes")) {
        return outcomes === "ok"
          ? Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response)
          : Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve(null) } as Response);
      }
      if (url.includes("/api/alpha-portfolio/trade-log")) {
        return tradeLog === "ok"
          ? Promise.resolve({ ok: true, json: () => Promise.resolve([]) } as Response)
          : Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve(null) } as Response);
      }
      if (url.includes("/api/alpha-portfolio")) {
        return portfolio === "ok"
          ? Promise.resolve({ ok: true, json: () => Promise.resolve(portfolioBody()) } as Response)
          : Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve(null) } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch: ${url}`));
    }),
  );
}

beforeEach(() => {
  __resetAlphaPortfolioCacheForTests();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("DashboardPage", () => {
  it("shows Loading… in all three sections before any fetch has resolved", () => {
    mockFetch();
    renderWithProviders(<DashboardPage />);
    // "Loading…" appears once per section that's still pending, plus
    // possibly the shared Portfolio Status card -- at least the three
    // sections under audit must show it immediately.
    expect(screen.getAllByText("Läser in…").length).toBeGreaterThanOrEqual(3);
  });

  it("renders real content in all three sections once every fetch succeeds -- baseline, unaffected by this fix", async () => {
    mockFetch();
    renderWithProviders(<DashboardPage />);
    await waitFor(() => expect(screen.getByText("Inget återstår just nu.")).toBeInTheDocument());
    expect(screen.getByText("Ingen aktivitet registrerad ännu.")).toBeInTheDocument();
    expect(screen.getByText("Ingen nyligen aktivitet i något case ännu.")).toBeInTheDocument();
  });

  it("a permanent decisions-fetch failure surfaces an honest error in all three sections, never stuck on Loading…", async () => {
    mockFetch({ decisions: "error" });
    renderWithProviders(<DashboardPage />);

    await waitFor(() =>
      expect(screen.getAllByText("Något gick fel vid inläsningen, så det här kan inte visas just nu.").length).toBe(3),
    );
    expect(screen.queryByText("Inget återstår just nu.")).not.toBeInTheDocument();
    expect(screen.queryByText("Ingen aktivitet registrerad ännu.")).not.toBeInTheDocument();
    expect(screen.queryByText("Ingen nyligen aktivitet i något case ännu.")).not.toBeInTheDocument();
  });

  it("a permanent portfolio-fetch failure (the shared cache, not a local Dashboard fetch) also surfaces the same honest error", async () => {
    mockFetch({ portfolio: "error" });
    renderWithProviders(<DashboardPage />);

    await waitFor(() =>
      expect(screen.getAllByText("Något gick fel vid inläsningen, så det här kan inte visas just nu.").length).toBe(3),
    );
  });

  it("a permanent trade-log failure alone is also enough to trip anyError for all three sections", async () => {
    mockFetch({ tradeLog: "error" });
    renderWithProviders(<DashboardPage />);

    await waitFor(() =>
      expect(screen.getAllByText("Något gick fel vid inläsningen, så det här kan inte visas just nu.").length).toBe(3),
    );
  });
});
