import { describe, expect, it } from "vitest";
// Vite's `?raw` import -- already typed by `vite/client` in tsconfig, so
// this needs no Node type definitions.
import SOURCE from "../routes/InvestmentCasePage.tsx?raw";
import OUTLOOK_SOURCE from "./AtlasOutlookSection.tsx?raw";

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

/** True when `tag` renders inside an open `<ExpandableDetail>` -- i.e.
 * behind progressive disclosure rather than on the default surface. */
function inDisclosure(tag: string): boolean {
  const at = positionOf(tag);
  const opened = SOURCE.lastIndexOf("<ExpandableDetail", at);
  return opened > -1 && !SOURCE.slice(opened, at).includes("</ExpandableDetail>");
}

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
    // They are un-deleted and still reachable, but must not restate one
    // shared meaning nine times on the primary surface.
    expect(inDisclosure("DecisionReadinessSection")).toBe(true);
    expect(inDisclosure("DecisionReliabilitySection")).toBe(true);
  });

  it("keeps the uncertainty summary behind that same disclosure", () => {
    // Canonical Reasoning Consolidation, Phase K. "Varför Atlas inte är
    // säkrare" summarises the nine sections below it; canonical
    // reasoning's own key unknowns now own primary uncertainty, so this
    // card belongs with the sections it summarises, not above them.
    expect(inDisclosure("AtlasDecisionSummary")).toBe(true);
    expect(positionOf("AtlasInvestmentReasoning")).toBeLessThan(positionOf("AtlasDecisionSummary"));
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

  it("puts Atlas's conclusion above the whole analytical body", () => {
    // Sprint 1B's core correction. `InvestmentCaseCanonicalSections` renders
    // the seven-category bar's supporting analysis -- Outlook, Investment
    // Argument, Atlas Reasoning, Evidence and the audit panels. It sat ~700
    // lines above the conclusion, so Sprint 1's local reorder was correct but
    // not sufficient.
    expect(positionOf("AtlasInvestmentReasoning")).toBeLessThan(
      positionOf("InvestmentCaseCanonicalSections"),
    );
    expect(positionOf("ExecutiveSummaryCard")).toBeLessThan(
      positionOf("InvestmentCaseCanonicalSections"),
    );
  });

  it("keeps the evidence/audit layer out of the default reading surface", () => {
    // Coverage percentages, knowledge-coverage domains, materiality counts,
    // evidence-quality grades and the evidence timeline keep Atlas auditable;
    // they are not how an investor decides.
    for (const panel of [
      "CoveragePanel",
      "KnowledgeCoveragePanel",
      "MaterialityPanel",
      "EvidenceQualityPanel",
      "EvidenceTimelinePanel",
    ]) {
      const at = positionOf(panel);
      const opened = SOURCE.lastIndexOf("<ExpandableDetail", at);
      const closedBetween = SOURCE.slice(opened, at).includes("</ExpandableDetail>");
      expect(opened, `${panel} should sit inside a disclosure`).toBeGreaterThan(-1);
      expect(closedBetween, `${panel} should sit inside a disclosure`).toBe(false);
    }
  });

  it("keeps deep company analysis available but not primary", () => {
    for (const panel of [
      "ManagementIntelligencePanel",
      "RegulatoryIntelligencePanel",
      "CompanyHealthAssessmentSection",
      "InterpretedFinancialEvidenceSection",
      "CompanyOverviewSection",
    ]) {
      const at = positionOf(panel);
      const opened = SOURCE.lastIndexOf("<ExpandableDetail", at);
      expect(SOURCE.slice(opened, at).includes("</ExpandableDetail>")).toBe(false);
    }
  });

  it("keeps Outlook and Evidence on the default surface", () => {
    // Reducing default exposure must not mean hiding the investment case
    // itself. Outlook and Evidence add information the primary narrative
    // does not carry, and stay visible.
    for (const section of ["AtlasOutlookSection", "EvidenceSection"]) {
      expect(inDisclosure(section), `${section} should stay on the default surface`).toBe(false);
    }
  });

  it("invents no Figma-only metric on this page", () => {
    // Expected Return / Upside / Downside / a Conviction score are target
    // product semantics the current engine does not produce with those
    // meanings. Sprint 1B must not introduce them by renaming a
    // confidence-like value.
    expect(SOURCE).not.toMatch(/probability-weighted/i);
    expect(SOURCE).not.toMatch(/intrinsicValue/);
  });

  it("renders canonical reasoning directly under Atlas's conclusion", () => {
    // Recommendation Reasoning Convergence. The one primary investment
    // explanation belongs with the conclusion it explains -- above
    // Portfolio Fit and the Evidence Graph, and above the Decision
    // Layer disclosure, not appended as a tenth analytical module at
    // the bottom of the page.
    expect(positionOf("AtlasInvestmentReasoning")).toBeLessThan(positionOf("PortfolioFitSection"));
    expect(positionOf("AtlasInvestmentReasoning")).toBeLessThan(positionOf("EvidenceGraphSection"));
    expect(positionOf("AtlasInvestmentReasoning")).toBeLessThan(positionOf("DecisionReadinessSection"));
    expect(inDisclosure("AtlasInvestmentReasoning")).toBe(false);
  });

  it("adds no new section inventory for canonical reasoning", () => {
    // The sprint follows Investment Case Compression: reasoning had to
    // become visible without the page becoming long again. One card,
    // rendered once, reusing the already-loaded `investmentDecision`
    // fetch -- no second fetch, and no second render site.
    const occurrences = SOURCE.split("<AtlasInvestmentReasoning").length - 1;
    expect(occurrences).toBe(1);
    expect(SOURCE).not.toContain("fetchRecommendationReasoning");
  });

  it("does not rank or re-derive reasoning in the page", () => {
    // Ordering is the backend's own `_ENGINE_PRECEDENCE`, applied
    // before serialization. The page may not sort, score or threshold
    // canonical drivers.
    const start = SOURCE.indexOf("<AtlasInvestmentReasoning");
    const block = SOURCE.slice(start, start + 400);
    expect(block).not.toMatch(/\.sort\(/);
    expect(block).not.toMatch(/\.filter\(/);
  });

  it("leaves Decision Memory exactly where it was", () => {
    // Recommendation Reasoning Convergence, Phase N. Decision Memory
    // records what the *investor* decided; canonical reasoning states
    // what *Atlas* concluded. The sprint touches neither the section
    // nor its position inside the Decision Layer disclosure.
    expect(positionOf("DecisionMemorySection")).toBeGreaterThan(positionOf("DecisionReadinessSection"));
    expect(SOURCE).toContain("decisionMemoryStatus.kind === \"loaded\"");
  });

  it("keeps the supporting analysis reachable behind disclosure", () => {
    // Phases I/J moved these off the default path. They must still be
    // rendered -- moving is not deleting, and their evidence drill-down
    // is the reason they exist.
    for (const section of ["InvestmentArgumentSection", "AtlasReasoningSection"]) {
      expect(inDisclosure(section), `${section} should be behind disclosure`).toBe(true);
    }
    expect(SOURCE).toContain("investmentCase.canonical.supportingAnalysisLabel");
  });

  it("does not headline re-rating scenario bounds as canonical return metrics", () => {
    // Phase F. `ExpectedReturnRange` and the Bull/Bear `returnPercent`
    // are valuation re-rating bounds with no scenario probabilities.
    // They may not be threaded into the Hero's summary strip, where
    // they sat under the labels "Förväntad avkastning" and "Uppsida /
    // nedsida" beside the recommendation itself.
    const hero = SOURCE.indexOf("<HeroCard");
    const heroProps = SOURCE.slice(hero, SOURCE.indexOf("/>", hero));
    for (const field of [
      "longTermExpectedReturn",
      "longTermExpectedReturnGap",
      "longTermBullReturnPercent",
      "longTermBearReturnPercent",
    ]) {
      expect(heroProps, `${field} must not reach the Hero`).not.toContain(field);
    }
    // The values themselves stay on the page, in the Outlook section.
    expect(positionOf("AtlasOutlookSection")).toBeGreaterThan(-1);
  });

  it("keeps the outlook's workings out of the default surface", () => {
    // Sprint 1C. Each horizon rendered three scenario values, three
    // assumption sentences and up to a dozen unranked driver labels -- about
    // two screens per horizon, twice over. The horizon's conclusion
    // (expected-return range, conviction, momentum) stays visible; the
    // derivation is one click down.
    const outlook = OUTLOOK_SOURCE;
    const disclosure = outlook.indexOf("investmentCase.outlook.scenarioDetailLabel");
    const close = outlook.indexOf("</ExpandableDetail>", disclosure);
    const inside = outlook.slice(disclosure, close);
    expect(inside).toContain("ScenarioField");
    expect(inside).toContain("keyDriversLabel");
    // Momentum is a single line and stays on the default surface.
    expect(outlook.indexOf("momentumLabel")).toBeGreaterThan(close);
  });
});
