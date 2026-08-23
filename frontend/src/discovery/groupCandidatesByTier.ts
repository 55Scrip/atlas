import type { FitRating, PortfolioFitAssessmentView } from "../portfolioFit/portfolioFitApi";
import { NO_PRIORITY_RANK, PRIORITY_LEVEL_RANK, type PriorityLevel } from "../status/statusTone";

/**
 * Deliverable 3 -- "if two candidates are effectively equivalent, show
 * a tie. Do not manufacture differentiation." Candidates within the
 * same `FitRating` are grouped under one tier heading, not numbered
 * 1/2/3 -- a flat ordered list would visually imply a ranking this
 * engine never computed (every candidate within a tier is, by design,
 * equally qualitatively rated).
 *
 * Product Sprint 9 (Discovery Excellence, Deliverable 9): within a tier,
 * candidates the shared Daily Brief Agenda already flagged (a real,
 * existing `PriorityLevel` -- never a new score) are listed first,
 * ranked by that same priority; every other candidate in the tier
 * follows, alphabetically. Two candidates with the same Fit rating and
 * the same Agenda priority (including "neither flagged") remain a tie,
 * broken only by ticker for stable rendering -- never a claim of
 * further differentiation. `priorityByTicker` defaults to empty, which
 * reduces to the original alphabetical-only behavior.
 */
const TIER_ORDER: FitRating[] = ["excellent", "good", "neutral", "weak", "poor", "unavailable"];

export interface CandidateTier {
  rating: FitRating;
  candidates: PortfolioFitAssessmentView[];
}

export function groupCandidatesByTier(
  candidates: PortfolioFitAssessmentView[],
  priorityByTicker: Map<string, PriorityLevel> = new Map(),
): CandidateTier[] {
  return TIER_ORDER.map((rating) => ({
    rating,
    candidates: candidates
      .filter((c) => c.overall === rating)
      .sort((a, b) => {
        const rankA = priorityByTicker.has(a.ticker) ? PRIORITY_LEVEL_RANK[priorityByTicker.get(a.ticker)!] : NO_PRIORITY_RANK;
        const rankB = priorityByTicker.has(b.ticker) ? PRIORITY_LEVEL_RANK[priorityByTicker.get(b.ticker)!] : NO_PRIORITY_RANK;
        if (rankA !== rankB) return rankB - rankA;
        return a.ticker.localeCompare(b.ticker);
      }),
  })).filter((tier) => tier.candidates.length > 0);
}
