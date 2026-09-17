import { describe, expect, it } from "vitest";
import SOURCE from "../routes/PortfolioPage.tsx?raw";
import { en } from "../i18n/translations/en";
import { sv } from "../i18n/translations/sv";
import { CASE_CHAPTER_IDS } from "../investmentCase/caseChapters";
import {
  COCKPIT_COLUMN_CHAPTER,
  COCKPIT_COLUMN_HEADER_KEY,
  COCKPIT_COLUMN_LINK_LABEL_KEY,
  cockpitCellHref,
  type CockpitColumnKey,
} from "./cockpitColumns";

/**
 * Portfolio Holdings Cockpit v1 -- the contract between the Portfolio
 * scanning surface and the Investment Case chapters that explain it.
 *
 * These assert the two things a later sprint is most likely to break by
 * accident: that a cell links to the chapter that actually explains it,
 * and that a cell never states a conclusion Atlas did not reach.
 */
const ALL: CockpitColumnKey[] = ["atlas", "business", "investment", "risk", "valuation", "forward", "fit"];

describe("cockpit column -> Investment Case chapter", () => {
  it("sends every dimension to the chapter that explains it", () => {
    expect(COCKPIT_COLUMN_CHAPTER).toEqual({
      atlas: "conclusion",
      business: "company",
      investment: "conclusion",
      risk: "risk",
      valuation: "valuation",
      forward: "forward-view",
      fit: "portfolio-fit",
    });
  });

  it("only ever targets a chapter the Investment Case actually declares", () => {
    // The ids come from the Case's own registry, so a chapter renamed
    // there cannot leave a dangling link here.
    for (const column of ALL) {
      expect(CASE_CHAPTER_IDS).toContain(COCKPIT_COLUMN_CHAPTER[column]);
    }
  });

  it("does not cross-wire the two easiest columns to confuse", () => {
    // The mutation this kills: risk linking to valuation, or fit to
    // risk. Both would look right and explain the wrong thing.
    expect(COCKPIT_COLUMN_CHAPTER.risk).not.toBe(COCKPIT_COLUMN_CHAPTER.valuation);
    expect(COCKPIT_COLUMN_CHAPTER.fit).not.toBe(COCKPIT_COLUMN_CHAPTER.risk);
    expect(COCKPIT_COLUMN_CHAPTER.business).not.toBe(COCKPIT_COLUMN_CHAPTER.investment);
  });

  it("builds a case-scoped URL carrying the chapter fragment", () => {
    expect(cockpitCellHref("abc-123", "risk")).toBe("/investment-case/abc-123#risk");
    expect(cockpitCellHref("abc-123", "valuation")).toBe("/investment-case/abc-123#valuation");
    expect(cockpitCellHref("abc-123", "business")).toBe("/investment-case/abc-123#company");
    expect(cockpitCellHref("abc-123", "fit")).toBe("/investment-case/abc-123#portfolio-fit");
    expect(cockpitCellHref("abc-123", "forward")).toBe("/investment-case/abc-123#forward-view");
    expect(cockpitCellHref("abc-123", "atlas")).toBe("/investment-case/abc-123#conclusion");
  });

  it("links nowhere when the holding has no case yet", () => {
    // The row's own "create then open" path handles this; building a
    // URL around a case id that does not exist would 404 on click.
    for (const column of ALL) {
      expect(cockpitCellHref(null, column)).toBeNull();
    }
  });

  it("carries a screen-reader label naming both ticker and dimension", () => {
    // A screen-reader user moves through a row of links in sequence,
    // with no visual column header to anchor them.
    for (const column of ALL) {
      for (const dict of [en, sv]) {
        const copy = dict[COCKPIT_COLUMN_LINK_LABEL_KEY[column]];
        expect(copy, `${column} needs a link label`).toBeTruthy();
        expect(copy).toContain("{{ticker}}");
      }
    }
  });

  it("gives every column a short header in both languages", () => {
    for (const column of ALL) {
      for (const dict of [en, sv]) {
        const header = dict[COCKPIT_COLUMN_HEADER_KEY[column]];
        expect(header, `${column} needs a header`).toBeTruthy();
        expect(header).not.toMatch(/_/);
        expect(header.split(" ").length).toBeLessThanOrEqual(2);
      }
    }
  });

  it("does not head two columns with the same word", () => {
    // The first column is already the company; a second column headed
    // "Company" is a readability defect. The underlying Atlas concept
    // and its chapter are unchanged -- only this header reads
    // differently.
    for (const dict of [en, sv]) {
      const headers = [
        dict["portfolio.cockpitTable.companyHeader"],
        ...ALL.map((c) => dict[COCKPIT_COLUMN_HEADER_KEY[c]]),
      ];
      expect(new Set(headers).size).toBe(headers.length);
    }
  });
});

describe("cockpit row honesty", () => {
  it("reads each cell from its own canonical source", () => {
    // The mutations these kill: Business reading the Investment score,
    // Investment reading the business vector, action inferred from fit,
    // risk reading valuation.
    const row = SOURCE.slice(SOURCE.indexOf("function HoldingsTableRow"));
    expect(row).toContain("deriveCompanyRating(analysis.businessCategories");
    expect(row).toContain("deriveInvestmentRating(analysis.decisionSupport.level)");
    expect(row).toContain("analysis?.riskProjection");
    expect(row).toContain("analysis?.valuation.status");
    // The action is the engine's own evidence-support state and is
    // never derived from fit, risk, valuation or a score.
    const atlasCell = row.slice(row.indexOf('column="atlas"'), row.indexOf('column="business"'));
    expect(atlasCell).toContain("DECISION_SUPPORT_BADGE_KEY[analysis.decisionSupport.level]");
    expect(atlasCell).not.toContain("fitRating");
    expect(atlasCell).not.toContain("riskProjection");
  });

  it("never turns an absent forward context into a forecast", () => {
    const row = SOURCE.slice(SOURCE.indexOf("function HoldingsTableRow"));
    const forwardCell = row.slice(row.indexOf('column="forward"'), row.indexOf('column="fit"'));
    // Counts only -- no direction, no polarity, no sensitivity.
    expect(forwardCell).toContain("guidanceCount");
    expect(forwardCell).not.toMatch(/sensitivity|outlook|expectedReturn|forecast/i);
    expect(en["portfolio.cockpitTable.forward.verified"]).toBe("Verified");
    expect(en["portfolio.cockpitTable.forward.countOther"]).not.toMatch(/up|down|better|worse/i);
  });

  it("renders unknown as unknown, never as a bad score", () => {
    const row = SOURCE.slice(SOURCE.indexOf("function HoldingsTableRow"));
    // A rating with no real input renders the quiet state, not 0.0.
    expect(row).toContain("rating.score === null) return <NotAssessedCell");
    expect(row).not.toMatch(/score\s*\?\?\s*0/);
    expect(en["portfolio.cockpitTable.none"]).toBe("—");
    expect(en["portfolio.cockpitTable.notAssessed"]).toBe("Not assessed");
  });

  it("keeps the row itself a link to the conclusion", () => {
    const row = SOURCE.slice(SOURCE.indexOf("function HoldingsTableRow"));
    expect(row).toContain("openInvestmentCase(holding.ticker, holding.caseId)");
    // A cell click must not also fire the row's own navigation.
    expect(row).toContain("event.stopPropagation()");
  });

  it("adds no per-holding fetch to draw a row", () => {
    // The hard stop this sprint declared: 25 holdings must not mean 25
    // Investment Case requests. Everything a row shows comes from the
    // cockpit report and the portfolio-fit report already fetched once.
    const table = SOURCE.slice(SOURCE.indexOf("function HoldingsTable"));
    expect(table).not.toContain("fetch(");
    expect(table).not.toContain("useEffect");
  });
});
