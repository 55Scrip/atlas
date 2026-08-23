import { describe, expect, it } from "vitest";
import { resolveCompanionContext } from "./useCompanionContext";

describe("resolveCompanionContext", () => {
  it("resolves the five original bare-workspace routes with no entity", () => {
    expect(resolveCompanionContext("/portfolio")).toEqual({ workspace: "portfolio", caseId: null, ticker: null });
    expect(resolveCompanionContext("/daily-brief")).toEqual({ workspace: "dailyBrief", caseId: null, ticker: null });
    expect(resolveCompanionContext("/discovery")).toEqual({ workspace: "discovery", caseId: null, ticker: null });
    expect(resolveCompanionContext("/history")).toEqual({ workspace: "history", caseId: null, ticker: null });
    expect(resolveCompanionContext("/dashboard")).toEqual({ workspace: "dashboard", caseId: null, ticker: null });
  });

  it("resolves an Investment Case route to a real caseId, never a ticker", () => {
    expect(resolveCompanionContext("/investment-case/case-123")).toEqual({
      workspace: "investmentCase",
      caseId: "case-123",
      ticker: null,
    });
  });

  it("resolves the bare Investment Case route (no id) with no entity", () => {
    expect(resolveCompanionContext("/investment-case")).toEqual({ workspace: "investmentCase", caseId: null, ticker: null });
  });

  it("resolves a Portfolio Holding route to the portfolio workspace with a ticker, not a caseId", () => {
    expect(resolveCompanionContext("/portfolio/holding/AAPL")).toEqual({
      workspace: "portfolio",
      caseId: null,
      ticker: "AAPL",
    });
  });

  it("resolves a Company route to the company workspace with a ticker", () => {
    expect(resolveCompanionContext("/company/MSFT")).toEqual({ workspace: "company", caseId: null, ticker: "MSFT" });
  });

  it("resolves a bare Watchlist route with no entity", () => {
    expect(resolveCompanionContext("/watchlist")).toEqual({ workspace: "watchlist", caseId: null, ticker: null });
  });

  it("resolves an unsupported route (Settings/Platform Status/Developer/utility pages) to no workspace", () => {
    expect(resolveCompanionContext("/platform-status")).toEqual({ workspace: null, caseId: null, ticker: null });
    expect(resolveCompanionContext("/welcome")).toEqual({ workspace: null, caseId: null, ticker: null });
    expect(resolveCompanionContext("/portfolio/import")).toEqual({ workspace: null, caseId: null, ticker: null });
    expect(resolveCompanionContext("/something-unknown")).toEqual({ workspace: null, caseId: null, ticker: null });
  });

  it("resolves Decision Workspace / Draft Commit routes to no workspace (deliberately deferred, see navigation audit)", () => {
    expect(resolveCompanionContext("/decisions/d1/workspace")).toEqual({ workspace: null, caseId: null, ticker: null });
    expect(resolveCompanionContext("/decision-drafts/draft-1/commit")).toEqual({ workspace: null, caseId: null, ticker: null });
  });

  it("does not treat a trailing-segment variant of a bare route as a match", () => {
    expect(resolveCompanionContext("/portfolio/holding")).toEqual({ workspace: null, caseId: null, ticker: null });
    expect(resolveCompanionContext("/company")).toEqual({ workspace: null, caseId: null, ticker: null });
  });

  // Product Sprint 5 (Discovery Engine v2).
  it("resolves a Discovery candidate route to the company workspace with a ticker, reusing the existing workspace type", () => {
    expect(resolveCompanionContext("/discovery/candidate/NVDA")).toEqual({
      workspace: "company",
      caseId: null,
      ticker: "NVDA",
    });
  });

  it("resolves the Compare route to the bare discovery workspace, never a fabricated single-candidate entity", () => {
    expect(resolveCompanionContext("/discovery/compare")).toEqual({ workspace: "discovery", caseId: null, ticker: null });
  });

  it("still resolves the bare Discovery route unchanged", () => {
    expect(resolveCompanionContext("/discovery")).toEqual({ workspace: "discovery", caseId: null, ticker: null });
  });
});
