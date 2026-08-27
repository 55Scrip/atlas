import type { AnalysisCoverageLevel, StanceLevel } from "../status/statusTone";
import type { FitRating } from "../portfolioFit/portfolioFitApi";

/**
 * Product Sprint 8 (Portfolio Excellence, Deliverable 6 -- Holding
 * Ordering). A pure, deterministic sort over holdings already fetched
 * elsewhere -- no numeric ranking is invented; every sort key is either
 * a real qualitative signal already computed server-side (Portfolio
 * Fit's own `FitRating`) or a plain real number the portfolio already
 * carries (`weightPercent`), with ticker as the final, always-available
 * tie-break so the order is never ambiguous.
 *
 * `"weight"` is the default (Alpha Integration Fix, One Product Pass):
 * the largest positions float to the top first, matching Portfolio's
 * own doctrine question, "what do I own." The former `"attention"` key
 * ranked holdings by the shared Daily Brief Agenda's own priority --
 * removed because it put Portfolio's default ordering in the same job
 * as Daily Brief's own "what changed" ranking (Alpha Product
 * Integration Review, Phase 8).
 */
export type HoldingSortKey = "weight" | "fit" | "coverage" | "stance" | "alphabetical";

/** Weakest first -- matches this sprint's own "identify weak holdings"
 * framing; `unavailable` sorts last, since it is neither strong nor
 * weak, just unassessed. */
const FIT_RANK: Record<FitRating, number> = { poor: 0, weak: 1, neutral: 2, good: 3, excellent: 4, unavailable: 5 };
const NO_FIT_RANK = 6;

/** Atlas Intelligence Sprint 1 (Data Coverage & Confidence Engine,
 * Deliverable 6): lowest coverage first -- "I should investigate these
 * companies before trusting Atlas too much" is this sort's own stated
 * purpose. Reuses the existing, already-displayed `AnalysisCoverageLevel`
 * (Portfolio's own "TÄCKNING" column), never the new, finer-grained
 * per-dimension model -- that level of detail belongs on the Investment
 * Case page's own Coverage panel, not a table row. */
const COVERAGE_RANK: Record<AnalysisCoverageLevel, number> = {
  no_coverage: 0,
  partial_coverage: 1,
  substantial_coverage: 2,
};

/** Atlas Intelligence Sprint 2 (Recommendation Quality &
 * Actionability, Deliverable 6): the levels this Sprint's own gating
 * doctrine treats as genuinely needing the investor's attention first
 * (`avoid_decision`, a real red flag; `review`) rank ahead of the
 * merely-uncertain ones (`reduce`, `wait`, `no_recommendation`), which
 * in turn rank ahead of the levels needing no action at all
 * (`maintain`, `increase`). Never a numeric score -- a fixed,
 * deterministic ordering over a closed vocabulary, the same discipline
 * `FIT_RANK`/`COVERAGE_RANK` above already establish. */
const STANCE_RANK: Record<StanceLevel, number> = {
  avoid_decision: 0,
  review: 1,
  reduce: 2,
  wait: 3,
  no_recommendation: 4,
  maintain: 5,
  increase: 6,
};

export interface SortableHolding {
  ticker: string;
  weightPercent: number;
}

export function sortHoldings<T extends SortableHolding>(
  holdings: T[],
  sortKey: HoldingSortKey,
  fitRatingByTicker: Map<string, FitRating>,
  coverageByTicker: Map<string, AnalysisCoverageLevel> = new Map(),
  stanceByTicker: Map<string, StanceLevel> = new Map(),
): T[] {
  const sorted = [...holdings];

  sorted.sort((a, b) => {
    switch (sortKey) {
      case "fit": {
        const rankA = fitRatingByTicker.has(a.ticker) ? FIT_RANK[fitRatingByTicker.get(a.ticker)!] : NO_FIT_RANK;
        const rankB = fitRatingByTicker.has(b.ticker) ? FIT_RANK[fitRatingByTicker.get(b.ticker)!] : NO_FIT_RANK;
        return rankA - rankB || a.ticker.localeCompare(b.ticker);
      }
      case "coverage": {
        const rankA = coverageByTicker.has(a.ticker) ? COVERAGE_RANK[coverageByTicker.get(a.ticker)!] : COVERAGE_RANK.no_coverage;
        const rankB = coverageByTicker.has(b.ticker) ? COVERAGE_RANK[coverageByTicker.get(b.ticker)!] : COVERAGE_RANK.no_coverage;
        return rankA - rankB || a.ticker.localeCompare(b.ticker);
      }
      case "stance": {
        const rankA = stanceByTicker.has(a.ticker) ? STANCE_RANK[stanceByTicker.get(a.ticker)!] : STANCE_RANK.no_recommendation;
        const rankB = stanceByTicker.has(b.ticker) ? STANCE_RANK[stanceByTicker.get(b.ticker)!] : STANCE_RANK.no_recommendation;
        return rankA - rankB || a.ticker.localeCompare(b.ticker);
      }
      case "alphabetical":
        return a.ticker.localeCompare(b.ticker);
      case "weight":
      default:
        return b.weightPercent - a.weightPercent || a.ticker.localeCompare(b.ticker);
    }
  });

  return sorted;
}
