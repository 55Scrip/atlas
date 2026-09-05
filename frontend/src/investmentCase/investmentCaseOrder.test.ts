import { describe, expect, it } from "vitest";
// Vite's `?raw` import -- already typed by `vite/client` in tsconfig, so
// this needs no Node type definitions.
import SOURCE from "../routes/InvestmentCasePage.tsx?raw";

/**
 * Convergence Sprint 1 (Investment Case Compression) -- source-order
 * assertions for the page's own reading hierarchy.
 *
 * `InvestmentCasePage.tsx` is ~6.5k lines and every section fetches
 * independently, so rendering it in jsdom to assert order would need a
 * dozen mocked endpoints and would break for reasons unrelated to
 * hierarchy. What this sprint actually changed is the order sections
 * appear in the render tree, and that is exactly what these assert --
 * a narrow, honest proxy, not a page snapshot.
 */

function positionOf(tag: string): number {
  const index = SOURCE.indexOf(`<${tag}`);
  expect(index, `${tag} should still be rendered by InvestmentCasePage`).toBeGreaterThan(-1);
  return index;
}

describe("Investment Case reading hierarchy", () => {
  it("puts Atlas's conclusion above the detailed Portfolio Fit section", () => {
    // The defect this sprint fixed: AtlasDecisionSummary -- the page's own
    // Level 1 answer -- rendered *below* Portfolio Fit and the Evidence
    // Graph, so the reader met Level 3 evidence before the conclusion.
    expect(positionOf("AtlasDecisionSummary")).toBeLessThan(positionOf("PortfolioFitSection"));
  });

  it("puts Atlas's conclusion above the Evidence Graph", () => {
    expect(positionOf("AtlasDecisionSummary")).toBeLessThan(positionOf("EvidenceGraphSection"));
  });

  it("keeps the hero and executive summary above the conclusion", () => {
    expect(positionOf("HeroCard")).toBeLessThan(positionOf("AtlasDecisionSummary"));
    expect(positionOf("ExecutiveSummaryCard")).toBeLessThan(positionOf("AtlasDecisionSummary"));
  });

  it("keeps the nine Decision Layer sections behind a disclosure", () => {
    // AtlasDecisionSummary exists to state their shared meaning once. They
    // are un-deleted and still reachable, but must not restate that meaning
    // nine times on the primary surface.
    const summaryEnd = positionOf("AtlasDecisionSummary");
    const disclosure = SOURCE.indexOf("<ExpandableDetail", summaryEnd);
    expect(disclosure).toBeGreaterThan(summaryEnd);
    expect(disclosure).toBeLessThan(positionOf("DecisionReadinessSection"));
  });

  it("does not render the manual decision form inline", () => {
    // The legacy BUY/WATCH/PASS + free-text thesis + 0-100 confidence form
    // is preserved (Decision.reason still feeds Decision Memory,
    // Decision.confidence still feeds pattern recognition) but must not
    // interrupt the conclusion. It now sits inside a disclosure.
    const form = positionOf("StartDecisionSection");
    const before = SOURCE.lastIndexOf("<ExpandableDetail", form);
    const between = SOURCE.slice(before, form);
    expect(before).toBeGreaterThan(-1);
    expect(between).not.toContain("</ExpandableDetail>");
  });
});
