import { caseChapterHref, type CaseChapterId } from "../investmentCase/caseChapters";
import type { TranslationKey } from "../i18n";

/**
 * Portfolio Holdings Cockpit v1 -- what each column means, and which
 * Investment Case chapter explains it.
 *
 * The product model this serves: Portfolio is the scanning surface
 * (WHAT Atlas sees), the Investment Case is the explanation (WHY). A
 * cockpit cell therefore never explains itself in place -- it names a
 * conclusion and links to the chapter that owns the reasoning.
 *
 * The mapping lives here, once, rather than as `"#risk"` strings
 * scattered through row rendering, for the same reason
 * `caseChapters.ts` exists: these are semantic destinations other
 * surfaces depend on, and a link that drifts to the wrong chapter is a
 * silent defect no type checker would catch. The ids themselves are
 * imported from the Investment Case's own registry, so a chapter
 * renamed there cannot leave a dangling link here.
 *
 * `atlas` points at `#conclusion` because that is the chapter which
 * explains the evidence-support state it shows.
 */
/**
 * Position Editor v1 / semantic cleanup: `investment` is gone from the
 * Portfolio cockpit.
 *
 * It was `deriveInvestmentRating(decisionSupport.level)` -- the *same
 * field* the Atlas column already states in Atlas's own words, put on a
 * 0-10 scale. So it carried no information the row did not already
 * have, and on an owned position "Investment 3.0 / Weak" reads as a
 * grade on the investment the investor holds. What it actually means is
 * "at today's price this is not attractive enough to increase", which
 * is what "Reduction supported" beside it already says.
 *
 * The construct itself is untouched: the Investment Case's own
 * six-dimension strip still uses it, where it sits beside Company,
 * Portfolio and Evidence and reads as one pillar among several rather
 * than as a verdict on the holding.
 */
export type CockpitColumnKey =
  | "atlas"
  | "business"
  | "risk"
  | "valuation"
  | "forward"
  | "fit";

export const COCKPIT_COLUMN_CHAPTER: Record<CockpitColumnKey, CaseChapterId> = {
  atlas: "conclusion",
  business: "company",
  risk: "risk",
  valuation: "valuation",
  forward: "forward-view",
  fit: "portfolio-fit",
};

/** Column headers. Deliberately one or two words: a header that needs a
 * sentence is a column that needs rethinking.
 *
 * `business` is labelled "Business", not "Company", even though the
 * underlying Atlas concept and its chapter are both called Company --
 * the first column is already the company, and two columns headed
 * "Company" is a readability defect, not a naming decision. The
 * underlying concept is untouched; only this header reads differently.
 */
export const COCKPIT_COLUMN_HEADER_KEY: Record<CockpitColumnKey, TranslationKey> = {
  atlas: "portfolio.cockpitTable.atlasHeader",
  business: "portfolio.cockpitTable.businessHeader",
  risk: "portfolio.cockpitTable.riskHeader",
  valuation: "portfolio.cockpitTable.valuationHeader",
  forward: "portfolio.cockpitTable.forwardHeader",
  fit: "portfolio.cockpitTable.fitHeader",
};

/** Screen-reader text for a linked cell: "Open META risk analysis". The
 * column is named as well as the ticker, because a screen-reader user
 * moving through a row of links hears them in sequence with no visual
 * column header to anchor them. */
export const COCKPIT_COLUMN_LINK_LABEL_KEY: Record<CockpitColumnKey, TranslationKey> = {
  atlas: "portfolio.cockpitTable.link.atlas",
  business: "portfolio.cockpitTable.link.business",
  risk: "portfolio.cockpitTable.link.risk",
  valuation: "portfolio.cockpitTable.link.valuation",
  forward: "portfolio.cockpitTable.link.forward",
  fit: "portfolio.cockpitTable.link.fit",
};

/**
 * Where a cockpit cell links to.
 *
 * Returns `null` when the holding has no Investment Case yet -- the
 * row's own "open the case" path then handles it, rather than this
 * building a route to a case id that does not exist.
 *
 * The fragment is always included, even when that chapter will say
 * "Not assessed": a destination that states its own absence is a
 * better answer than a link that silently does nothing, and the
 * chapters were built to survive exactly this.
 */
export function cockpitCellHref(caseId: string | null, column: CockpitColumnKey): string | null {
  if (!caseId) return null;
  return `/investment-case/${encodeURIComponent(caseId)}${caseChapterHref(COCKPIT_COLUMN_CHAPTER[column])}`;
}
