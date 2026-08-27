/**
 * Discover Doctrine, Phases 1-2/12 -- "Atlas should aggressively
 * prioritize... never show every watchlist company with equal visual
 * importance." Replaces `groupCandidatesByTier.ts`'s own "bucket by
 * raw Fit rating, always show all six tiers" grouping, which answered
 * "how well does this fit my portfolio's construction" -- a real but
 * different question from "should I look at this now."
 *
 * Built entirely from three real, already-computed, existing
 * categorical signals -- no new backend concept, no numeric score
 * invented anywhere:
 * - Portfolio Fit (`FitRating`, `atlas.alpha.portfolio_fit` -- excellent
 *   through unavailable, deliberately never a number).
 * - Stance (`StanceLevel`, `atlas.alpha.stance` -- "the one synthesized
 *   answer to what should I do now").
 * - Daily Brief Agenda priority (`PriorityLevel`) -- the same field
 *   `groupCandidatesByTier.ts` already used for within-tier ordering;
 *   only the categorical level is used here, never the raw headline
 *   text that field's own item carries (Phase 5 -- Discover must never
 *   render a raw event announcement as a candidate's own verdict).
 */
import type { FitRating, PortfolioFitAssessmentView } from "../portfolioFit/portfolioFitApi";
import type { StanceLevel } from "../stance/stanceApi";
import { FIT_RATING_TONE, NO_PRIORITY_RANK, PRIORITY_LEVEL_RANK, STANCE_LEVEL_TONE, type PriorityLevel } from "../status/statusTone";

export type OpportunityTier = "highest" | "worthReviewing" | "everythingElse";

export interface RankedCandidate {
  ticker: string;
  caseId: string | null;
  assessment: PortfolioFitAssessmentView | null;
  stance: StanceLevel | null;
  priority: PriorityLevel | null;
}

export interface RankedCandidates {
  highest: RankedCandidate[];
  worthReviewing: RankedCandidate[];
  everythingElse: RankedCandidate[];
}

/** Phase 2 -- "the smallest honest shortlist... Target: 3-5 primary
 * candidates." A hard cap, not a floor: if fewer candidates genuinely
 * qualify, the list is simply shorter -- padding it with weaker
 * candidates just to reach 3 would be exactly the fabricated
 * differentiation this doctrine forbids. */
const MAX_HIGHEST_OPPORTUNITY = 5;

const FIT_RANK: Record<FitRating, number> = { excellent: 0, good: 1, neutral: 2, weak: 3, poor: 4, unavailable: 5 };
const STANCE_RANK: Record<StanceLevel, number> = {
  increase: 0,
  maintain: 1,
  no_recommendation: 2,
  wait: 3,
  review: 4,
  reduce: 5,
  avoid_decision: 6,
};

/**
 * Highest opportunity: a confident, unambiguous case -- Fit is
 * positive-toned (excellent/good) AND Stance does not disagree
 * (nothing caution/critical-toned). A candidate where Fit and Stance
 * genuinely conflict is real, worth a look, but not a confident "top
 * opportunity" claim -- it falls to Worth Reviewing instead, precisely
 * because of the tension, never silently resolved either way.
 *
 * Worth reviewing: some real signal exists -- a positive-toned Fit or
 * Stance on its own, a critical-toned Stance (a red flag worth seeing),
 * or an elevated Daily Brief Agenda priority (something changed).
 *
 * Everything else: no assessment yet, or no signal currently pulling
 * attention there.
 */
function classify(candidate: RankedCandidate): OpportunityTier {
  const assessment = candidate.assessment;
  if (assessment === null) return "everythingElse";
  const fitTone = FIT_RATING_TONE[assessment.overall];
  const stanceTone = candidate.stance ? STANCE_LEVEL_TONE[candidate.stance] : "neutral";
  const elevatedPriority = candidate.priority === "critical" || candidate.priority === "high";

  if (fitTone === "positive" && stanceTone !== "critical" && stanceTone !== "caution") {
    return "highest";
  }
  if (fitTone === "positive" || stanceTone === "positive" || stanceTone === "critical" || elevatedPriority) {
    return "worthReviewing";
  }
  return "everythingElse";
}

function compareRank(a: RankedCandidate, b: RankedCandidate): number {
  const fitRankOf = (c: RankedCandidate) => (c.assessment ? FIT_RANK[c.assessment.overall] : 6);
  const fitDiff = fitRankOf(a) - fitRankOf(b);
  if (fitDiff !== 0) return fitDiff;
  const stanceRankOf = (c: RankedCandidate) => (c.stance ? STANCE_RANK[c.stance] : 7);
  const stanceDiff = stanceRankOf(a) - stanceRankOf(b);
  if (stanceDiff !== 0) return stanceDiff;
  const priorityRankOf = (c: RankedCandidate) => (c.priority ? PRIORITY_LEVEL_RANK[c.priority] : NO_PRIORITY_RANK);
  const priorityDiff = priorityRankOf(b) - priorityRankOf(a);
  if (priorityDiff !== 0) return priorityDiff;
  return a.ticker.localeCompare(b.ticker);
}

/** Phase 12 -- Highest opportunity, then Worth reviewing, then
 * everything else, in that fixed order, always. A candidate that
 * overflows the Highest-opportunity cap is never dropped -- it moves
 * to Worth reviewing, still ranked, still one click away. */
export function rankCandidates(candidates: RankedCandidate[]): RankedCandidates {
  const highest: RankedCandidate[] = [];
  const worthReviewing: RankedCandidate[] = [];
  const everythingElse: RankedCandidate[] = [];
  for (const candidate of candidates) {
    const tier = classify(candidate);
    if (tier === "highest") highest.push(candidate);
    else if (tier === "worthReviewing") worthReviewing.push(candidate);
    else everythingElse.push(candidate);
  }
  highest.sort(compareRank);
  worthReviewing.sort(compareRank);
  everythingElse.sort(compareRank);

  const overflow = highest.splice(MAX_HIGHEST_OPPORTUNITY);
  const combinedWorthReviewing = [...overflow, ...worthReviewing].sort(compareRank);

  return { highest, worthReviewing: combinedWorthReviewing, everythingElse };
}
