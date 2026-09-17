import type { TranslationKey } from "../i18n";

/**
 * Product Convergence Sprint 1 (Investment Case Hierarchy) -- the
 * Investment Case's stable semantic chapters.
 *
 * The product model this sprint establishes:
 *
 *   Portfolio / Daily Brief / Watchlist / Discovery = WHAT Atlas sees
 *   Investment Case                                 = WHY Atlas sees it
 *   Evidence / deep analysis                        = what it rests on
 *
 * These eight ids are the Investment Case's public surface. They are
 * deliberately declared once, here, rather than spelled out at each
 * render site, because a later sprint has to be able to link
 * *into* them from Portfolio ("High risk" -> `#risk`, "Expensive" ->
 * `#valuation`, "Weak fit" -> `#portfolio-fit`) without another page
 * rewrite. A chapter id is a product promise, not a DOM detail: it
 * never encodes ordering, and a chapter that has nothing to show still
 * exists and still receives its link (it says so honestly instead of
 * disappearing, which is what would break an inbound link).
 *
 * The DOM id is the chapter id verbatim, so `/investment-case/<id>#risk`
 * is also a plain browser anchor once the case has loaded -- no
 * indirection to keep in sync between the router, the nav and the
 * section.
 */
export const CASE_CHAPTER_IDS = [
  "conclusion",
  "company",
  "strategy",
  "forward-view",
  "valuation",
  "risk",
  "portfolio-fit",
  "evidence",
] as const;

export type CaseChapterId = (typeof CASE_CHAPTER_IDS)[number];

/** Chapter titles. Structured keys, never backend prose -- a chapter
 * heading is UI chrome and is fully translated like the rest of it. */
export const CASE_CHAPTER_LABEL_KEY: Record<CaseChapterId, TranslationKey> = {
  conclusion: "investmentCase.chapter.conclusion",
  company: "investmentCase.chapter.company",
  strategy: "investmentCase.chapter.strategy",
  "forward-view": "investmentCase.chapter.forwardView",
  valuation: "investmentCase.chapter.valuation",
  risk: "investmentCase.chapter.risk",
  "portfolio-fit": "investmentCase.chapter.portfolioFit",
  evidence: "investmentCase.chapter.evidence",
};

/** The chapters the in-page navigation offers. Conclusion is excluded
 * deliberately: it is the top of the page and the thing the reader is
 * already looking at when the navigation appears. It remains a real,
 * linkable destination for inbound deep links. */
export const CASE_CHAPTER_NAV_IDS: readonly CaseChapterId[] = CASE_CHAPTER_IDS.filter(
  (id) => id !== "conclusion",
);

/** `#risk` -> `"risk"`. Anything else -- an unknown fragment, a bare
 * `#`, a fragment belonging to some other anchor on the page -- is
 * `null`, and the caller then does nothing at all rather than guessing
 * at a chapter. Tolerant of the `case-chapter-` prefix an earlier
 * link shape might carry, and of percent-encoding. */
export function parseCaseChapterHash(hash: string): CaseChapterId | null {
  if (!hash) return null;
  let raw = hash.startsWith("#") ? hash.slice(1) : hash;
  try {
    raw = decodeURIComponent(raw);
  } catch {
    // A malformed escape sequence is simply not a chapter.
    return null;
  }
  const candidate = raw.startsWith("case-chapter-") ? raw.slice("case-chapter-".length) : raw;
  return (CASE_CHAPTER_IDS as readonly string[]).includes(candidate) ? (candidate as CaseChapterId) : null;
}

/** The in-page link target for a chapter. */
export function caseChapterHref(id: CaseChapterId): string {
  return `#${id}`;
}
