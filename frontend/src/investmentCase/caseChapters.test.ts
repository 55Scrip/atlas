import { describe, expect, it } from "vitest";
import SOURCE from "../routes/InvestmentCasePage.tsx?raw";
import { en } from "../i18n/translations/en";
import { sv } from "../i18n/translations/sv";
import {
  CASE_CHAPTER_IDS,
  CASE_CHAPTER_LABEL_KEY,
  CASE_CHAPTER_NAV_IDS,
  caseChapterHref,
  parseCaseChapterHash,
} from "./caseChapters";

/**
 * Product Convergence Sprint 1 (Investment Case Hierarchy) -- the
 * chapter contract.
 *
 * These assert the part of this sprint a later one is most likely to
 * break by accident: that every semantic chapter still exists, still
 * owns its id, and is still rendered by the page. The Portfolio sprint
 * is going to link into these ids; a chapter quietly renamed or dropped
 * would turn those links into silent no-ops.
 */
describe("Investment Case chapter registry", () => {
  it("declares the eight semantic chapters this sprint established", () => {
    expect([...CASE_CHAPTER_IDS]).toEqual([
      "conclusion",
      "company",
      "strategy",
      "forward-view",
      "valuation",
      "risk",
      "portfolio-fit",
      "evidence",
    ]);
  });

  it("gives every chapter a real, translated title in both languages", () => {
    for (const id of CASE_CHAPTER_IDS) {
      const key = CASE_CHAPTER_LABEL_KEY[id];
      expect(en[key], `${id} needs English copy`).toBeTruthy();
      expect(sv[key], `${id} needs Swedish copy`).toBeTruthy();
      // A raw backend enum must never reach visible copy: a chapter
      // title is UI chrome and is written, not echoed.
      expect(en[key]).not.toMatch(/_/);
      expect(sv[key]).not.toMatch(/_/);
    }
  });

  it("offers every chapter but the conclusion in the in-page navigation", () => {
    // The conclusion is the top of the page, so it needs no link down to
    // itself -- but it stays a real destination for an inbound one.
    expect([...CASE_CHAPTER_NAV_IDS]).toEqual(
      CASE_CHAPTER_IDS.filter((id) => id !== "conclusion"),
    );
    expect(CASE_CHAPTER_IDS).toContain("conclusion");
  });

  it("resolves a fragment to a chapter, and anything else to nothing", () => {
    expect(parseCaseChapterHash("#risk")).toBe("risk");
    expect(parseCaseChapterHash("risk")).toBe("risk");
    expect(parseCaseChapterHash("#portfolio-fit")).toBe("portfolio-fit");
    expect(parseCaseChapterHash("#forward-view")).toBe("forward-view");
    // Tolerant of a prefixed link shape and of percent-encoding.
    expect(parseCaseChapterHash("#case-chapter-valuation")).toBe("valuation");
    expect(parseCaseChapterHash("#portfolio%2Dfit")).toBe("portfolio-fit");
    // Degrades safely rather than guessing.
    expect(parseCaseChapterHash("")).toBeNull();
    expect(parseCaseChapterHash("#")).toBeNull();
    expect(parseCaseChapterHash("#investment-case-tabpanel-timeline")).toBeNull();
    expect(parseCaseChapterHash("#Risk")).toBeNull();
    expect(parseCaseChapterHash("#%E0%A4%A")).toBeNull();
  });

  it("links a chapter at its own id, so the anchor and the section agree", () => {
    for (const id of CASE_CHAPTER_IDS) {
      expect(caseChapterHref(id)).toBe(`#${id}`);
      expect(parseCaseChapterHash(caseChapterHref(id))).toBe(id);
    }
  });
});

/** `<CaseChapter id="risk"` on one line, or `<CaseChapter` with its
 * props wrapped across several -- Sprint 1B gave most chapters a
 * `status`/`headline`, so the opening tag is now usually multi-line.
 * Matching on the id alone keeps these assertions about hierarchy
 * rather than about formatting. */
function chapterAt(id: string): number {
  const at = SOURCE.search(new RegExp(`<CaseChapter\\s+(?:[^>]*?\\s)?id="${id}"`));
  expect(at, `chapter ${id} should be rendered`).toBeGreaterThan(-1);
  return at;
}

describe("Investment Case chapter rendering", () => {
  it("renders every chapter exactly once on the page", () => {
    for (const id of CASE_CHAPTER_IDS) {
      const occurrences = SOURCE.match(new RegExp(`<CaseChapter\\s+(?:[^>]*?\\s)?id="${id}"`, "g")) ?? [];
      expect(occurrences.length, `${id} should render exactly once`).toBe(1);
    }
  });

  it("puts each analytical section under the chapter that owns it", () => {
    // Chapter boundaries are what a later Portfolio deep link depends
    // on. A section drifting into a neighbouring chapter would make the
    // link land on the wrong explanation.
    const sectionIn = (tag: string, id: string) => {
      const at = SOURCE.indexOf(`<${tag}`, chapterAt(id));
      expect(at, `${tag} should be rendered`).toBeGreaterThan(-1);
      const nextChapter = SOURCE.search(new RegExp(`<CaseChapter\\s`, "g"));
      void nextChapter;
      const following = SOURCE.indexOf("<CaseChapter", chapterAt(id) + 1);
      return following === -1 || at < following;
    };
    expect(sectionIn("CompanyHealthAssessmentSection", "company")).toBe(true);
    expect(sectionIn("StrategySection", "strategy")).toBe(true);
    expect(sectionIn("ForwardViewSection", "forward-view")).toBe(true);
    expect(sectionIn("ValuationDetailSection", "valuation")).toBe(true);
    expect(sectionIn("RiskSection", "risk")).toBe(true);
    expect(sectionIn("PortfolioFitSection", "portfolio-fit")).toBe(true);
    expect(sectionIn("EvidenceSection", "evidence")).toBe(true);
  });

  it("states each chapter's own conclusion beside its title", () => {
    // Product Convergence Sprint 1B. A deep link from Portfolio lands on
    // a chapter and must answer that chapter's question immediately --
    // "Risk — High", "Valuation — Expensive" -- without the reader
    // opening anything. Every chapter that has an engine status to show
    // shows it; Conclusion is the Hero itself and needs none.
    for (const id of ["company", "strategy", "forward-view", "valuation", "risk", "portfolio-fit", "evidence"]) {
      const open = SOURCE.slice(chapterAt(id), SOURCE.indexOf(">", chapterAt(id) + 40));
      expect(open, `${id} should carry a status`).toContain("status=");
    }
  });

  it("Position Editor v1: badges the Portfolio Fit chapter from the portfolio-relative dimension", () => {
    // The chapter used to badge `fitAssessment.overall`, which votes
    // across business, valuation and risk as well -- so a chapter
    // headed "Portfolio Fit" could read "Weak Fit" purely because the
    // stock was expensive, restating the Valuation chapter two
    // chapters further down. The badge must come from allocation, the
    // one dimension that asks a portfolio question.
    const open = SOURCE.slice(chapterAt("portfolio-fit"), SOURCE.indexOf(">", chapterAt("portfolio-fit") + 40));
    expect(open).toContain("fitAllocation");
    // And `fitAllocation` must itself be the allocation dimension --
    // pinning only the usage would let the definition drift back to the
    // overall rating under an honest-looking name.
    const definition = SOURCE.slice(SOURCE.indexOf("const fitAllocation ="), SOURCE.indexOf(";", SOURCE.indexOf("const fitAllocation =")));
    expect(definition).toContain('kind === "allocation"');
    expect(open).not.toContain("fitAssessment.overall");
    expect(open).not.toContain("describeFitVerdict");
  });

  it("keeps each chapter's analysis behind a disclosure", () => {
    // Sprint 1B's core correction: Sprint 1 made the chapters real but
    // left their analysis expanded, so the page grew from 3,908px to
    // 5,457px on META. The conclusion is on the surface; the analysis is
    // one click down.
    for (const [id, tag] of [
      ["company", "CompanyHealthAssessmentSection"],
      ["valuation", "ValuationDetailSection"],
      ["risk", "RiskSection"],
      ["portfolio-fit", "PortfolioFitSection"],
    ] as [string, string][]) {
      const at = SOURCE.indexOf(`<${tag}`, chapterAt(id));
      expect(at, `${tag} should be rendered`).toBeGreaterThan(-1);
      const opened = SOURCE.lastIndexOf("<ExpandableDetail", at);
      expect(opened, `${tag} should sit inside a disclosure`).toBeGreaterThan(chapterAt(id));
      expect(SOURCE.slice(opened, at)).not.toContain("</ExpandableDetail>");
    }
  });

  it("completes deep-link arrival only once the chapters exist", () => {
    // The browser's own fragment handling has already run and failed by
    // the time the case finishes loading, so the page must gate the
    // arrival on the same condition the chapters render under.
    expect(SOURCE).toContain("useCaseChapterDeepLink(");
    const at = SOURCE.indexOf("useCaseChapterDeepLink(");
    const call = SOURCE.slice(at, SOURCE.indexOf(");", at));
    expect(call).toContain('status.kind === "loaded"');
    expect(call).toContain('investmentCaseAnalysis.kind === "loaded"');
  });

  it("no longer hides Risk, Valuation or Portfolio Fit behind a tab", () => {
    // The reason neither could be deep-linked before this sprint: their
    // only render site was inside `activeTab === "moreDetails"`.
    const tabPanel = SOURCE.indexOf('activeTab === "moreDetails"');
    expect(tabPanel).toBeGreaterThan(-1);
    const panel = SOURCE.slice(tabPanel, SOURCE.indexOf("investment-case-tabpanel-moreDetails", tabPanel) + 4000);
    for (const tag of ["<RiskSection", "<ValuationDetailSection", "<PortfolioContextDetail", "<EvidenceDetailSection"]) {
      expect(panel, `${tag} should no longer live in the tab`).not.toContain(tag);
    }
  });

  it("states each dimension's conclusion before its machinery", () => {
    // Valuation: the conclusion and the support state read first;
    // sensitivity -- conditional re-rating arithmetic whose range can be
    // very wide -- reads last and never opens the chapter.
    const chapter = chapterAt("valuation");
    const conclusion = SOURCE.indexOf("<ValuationDetailSection", chapter);
    const support = SOURCE.indexOf("<ValuationSupportCard", chapter);
    const sensitivity = SOURCE.indexOf("<AtlasOutlookSection", chapter);
    expect(conclusion).toBeLessThan(support);
    expect(support).toBeLessThan(sensitivity);
    // Sprint 1B: sensitivity is two disclosures deep -- inside the
    // chapter's analysis, then inside its own.
    const opened = SOURCE.lastIndexOf("<ExpandableDetail", sensitivity);
    expect(SOURCE.slice(opened, sensitivity)).not.toContain("</ExpandableDetail>");
  });

  it("keeps valuation sensitivity labelled as sensitivity, not forecast", () => {
    // Unchanged from the engine: `OUTLOOK_ROLE` is `"sensitivity"` and
    // the caption says so. This sprint reordered it; it may not reframe
    // it, and no chapter may call it a forecast.
    expect(en["investmentCase.outlook.heading"]).toBe("Valuation sensitivity");
    expect(en["investmentCase.outlook.caption"]).toContain("Not a forecast");
    expect(sv["investmentCase.outlook.caption"]).toContain("Inte en prognos");
    expect(en["investmentCase.forwardView.caption"]).toContain("Not a forecast");
    expect(sv["investmentCase.forwardView.caption"]).toContain("Inte en prognos");
  });

  it("does not let Portfolio Fit reach the recommendation", () => {
    // Doctrine: fit informs the decision, never overrides case strength.
    // The chapter reads an independently-fetched assessment and nothing
    // else; nothing in it may be threaded into the Hero.
    const chapter = chapterAt("portfolio-fit");
    const body = SOURCE.slice(chapter, SOURCE.indexOf("</CaseChapter>", chapter));
    expect(body).toContain("portfolioFitStatus.kind");
    expect(body).not.toContain("recommendation");
    expect(body).not.toContain("conviction");
    expect(en["investmentCase.portfolioFit.doctrine"]).toContain("never overrides");
  });

  it("does not claim comprehensive risk coverage", () => {
    // Atlas evaluates four risk categories. The chapter says so rather
    // than letting the word "Risk" imply macro, geopolitical or causal
    // coverage that no engine computes.
    // Sprint 1B shortened the line that carries this, but did not move
    // it behind a disclosure: it is the one thing stopping the word
    // "Risk" from implying coverage no engine computes, so it stays on
    // the chapter's surface.
    expect(en["investmentCase.risk.scopeNoteShort"]).toMatch(/not assessed/);
    expect(sv["investmentCase.risk.scopeNoteShort"]).toMatch(/bedöms inte/);
    expect(SOURCE).toContain("investmentCase.risk.scopeNoteShort");
  });

  it("keeps an unsupported or empty chapter down to a headline", () => {
    // The empty/low-signal chapter rule: a stable deep-link destination
    // does not need a large card. Strategy holds no panel at all beyond
    // its one line, and Forward View renders its evidence component only
    // when there is evidence.
    const strategy = SOURCE.slice(chapterAt("strategy"), SOURCE.indexOf("</CaseChapter>", chapterAt("strategy")));
    expect(strategy).toContain("<StrategySection");
    expect(strategy).not.toContain("<ExpandableDetail");

    const forward = SOURCE.slice(chapterAt("forward-view"), SOURCE.indexOf("</CaseChapter>", chapterAt("forward-view")));
    expect(forward).toContain("forwardSummary.hasEvidence &&");
  });
});
