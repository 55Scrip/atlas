/**
 * Discover Doctrine, Phases 1-2/12 -- "Atlas should aggressively
 * prioritize... never show every watchlist company with equal visual
 * importance." Replaces `groupCandidatesByTier.ts`'s own "bucket by
 * raw Fit rating, always show all six tiers" grouping, which answered
 * "how well does this fit my portfolio's construction" -- a real but
 * different question from "should I look at this now."
 *
 * Built entirely from four real, already-computed, existing categorical
 * signals -- no new backend concept, no numeric score invented
 * anywhere, and no arithmetic across signals:
 * - Decision Support (`DecisionSupportLevel`,
 *   `atlas.alpha.decision_support` -- Atlas's own canonical conclusion,
 *   projected from the recommendation gate, never recomputed). Added by
 *   Convergence Sprint 4D and read first; see `EntrySupportBand`.
 * - Portfolio Fit (`FitRating`, `atlas.alpha.portfolio_fit` -- excellent
 *   through unavailable, deliberately never a number).
 * - Stance (`StanceLevel`, `atlas.alpha.stance` -- "the one synthesized
 *   answer to what should I do now").
 * - Daily Brief Agenda priority (`PriorityLevel`) -- the same field
 *   `groupCandidatesByTier.ts` already used for within-tier ordering;
 *   only the categorical level is used here, never the raw headline
 *   text that field's own item carries (Phase 5 -- Discover must never
 *   render a raw event announcement as a candidate's own verdict).
 *
 * The order above is the precedence, and it encodes one product rule:
 * Portfolio Fit may inform and warn, but it may not rewrite what Atlas
 * concluded about the company. A strong case that suits this portfolio
 * badly stays a strong case, shown with its poor fit visible.
 */
import type { FitRating } from "../portfolioFit/portfolioFitApi";
import type { StanceLevel } from "../stance/stanceApi";
import {
  NO_PRIORITY_RANK,
  PRIORITY_LEVEL_RANK,
  STANCE_LEVEL_TONE,
  type DecisionSupportLevel,
  type PriorityLevel,
} from "../status/statusTone";

export type OpportunityTier = "highest" | "worthReviewing" | "everythingElse";

/**
 * Convergence Sprint 4D. What Atlas's own canonical recommendation says
 * about *initiating a position* -- the one question Discovery exists to
 * answer, since every candidate is by construction a company the
 * investor does not hold.
 *
 * This is a three-band reading of `DecisionSupportLevel`, not an
 * ordinal over its seven members. The seven are not a scale: they are
 * seven distinct conclusions, and only some of them say anything at all
 * about a *new* entry.
 *
 * - `"supported"` -- Atlas's evidence supports deploying capital here.
 * - `"open"` -- no entry conclusion was reached. `INSUFFICIENT_EVIDENCE`
 *   is a withheld conclusion, never a negative one, and it belongs
 *   above a negative one for Discovery's purpose: an open question is
 *   worth an investor's own look, a settled "no" mostly is not.
 *   `THESIS_INTACT` sits here too, deliberately: "the current thesis
 *   remains intact" is a statement about an *existing* position, and
 *   reading it as "a good time to buy" would be inventing a claim the
 *   recommendation engine never made.
 * - `"against"` -- Atlas evaluated and concluded against deploying
 *   capital. `NO_ACTION_SUPPORTED` is a real, evaluated "no" (its own
 *   sentence: "current evidence does not support initiating a position
 *   in this security"), which is exactly why it must not sit alongside
 *   a withheld one.
 *
 * `atlas/analysis_engine/direction_selector.py`'s "Not held" matrix can
 * only reach BUY, NO_ACTION or withheld, so on real Discovery data only
 * three of these seven ever occur (measured: 4 / 6 / 12 of 22). The
 * other four are mapped anyway, by meaning rather than by reachability,
 * so a future sprint that widens the matrix needs no edit here.
 */
export type EntrySupportBand = "supported" | "open" | "against";

const ENTRY_SUPPORT_BAND: Record<DecisionSupportLevel, EntrySupportBand> = {
  entry_supported: "supported",
  increase_supported: "supported",
  thesis_intact: "open",
  insufficient_evidence: "open",
  no_action_supported: "against",
  reduction_supported: "against",
  exit_supported: "against",
};

const BAND_RANK: Record<EntrySupportBand, number> = { supported: 0, open: 1, against: 2 };

/** A candidate carrying no level at all has reached no entry
 * conclusion, which is exactly what `"open"` means -- read from the
 * absence, not defaulted past it. */
export function entrySupportBand(level: DecisionSupportLevel | null): EntrySupportBand {
  return level === null ? "open" : ENTRY_SUPPORT_BAND[level];
}

export interface RankedCandidate {
  ticker: string;
  caseId: string | null;
  /** Sprint 4B: the Fit *rating*, not the whole assessment -- ranking
   * only ever read `.overall`, and a candidate now arrives from the
   * Discovery candidate endpoint, which carries the rating alone.
   * `null` means Portfolio Fit genuinely could not evaluate it and is
   * ranked last, never quietly treated as neutral. */
  fit: FitRating | null;
  stance: StanceLevel | null;
  priority: PriorityLevel | null;
  /** Sprint 4D: Atlas's own canonical conclusion about this company,
   * and the first thing ranking reads. See `EntrySupportBand`. */
  decisionSupport: DecisionSupportLevel | null;
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
 * Sprint 4D. The tier is Atlas's own conclusion about entering, and
 * nothing else decides it.
 *
 * It used to be decided by Portfolio Fit: "highest" meant a
 * positive-toned Fit with no caution- or critical-toned Stance. That
 * put a company the investor's portfolio happens to accommodate above
 * one Atlas actually concluded was worth buying, and -- because Stance
 * reads Portfolio Fit itself (`atlas/alpha/stance/service.py`: "a
 * Stance needs to know whether an otherwise-favorable direction still
 * fits the portfolio") -- it weighted the same portfolio-relative fact
 * twice. Measured against live data, no candidate reached "highest" at
 * all, because Stance is `review` for 20 of 22 as a pure
 * moderate-confidence gate.
 *
 * Fit did not stop being a signal; it stopped being the *case*. It
 * still orders candidates inside a band, and the surface still shows
 * it. What it no longer does is rewrite what Atlas concluded.
 *
 * The one thing kept from the old rule is its instinct about genuine
 * conflict: an entry Atlas supports while its Stance is critical-toned
 * (`avoid_decision` -- contradicting evidence, or conviction that could
 * not be established at all) is a real tension, and it drops to Worth
 * reviewing rather than being presented as a confident pick. Ordinary
 * caution no longer does that -- caution here is usually just moderate
 * confidence, which is not a disagreement with the recommendation.
 */
function classify(candidate: RankedCandidate): OpportunityTier {
  const band = entrySupportBand(candidate.decisionSupport);
  if (band === "supported") {
    const stanceTone = candidate.stance ? STANCE_LEVEL_TONE[candidate.stance] : "neutral";
    return stanceTone === "critical" ? "worthReviewing" : "highest";
  }
  return band === "open" ? "worthReviewing" : "everythingElse";
}

/** Lexicographic, in this order, with no weights and no arithmetic
 * across keys -- so "A is above B" is always attributable to exactly
 * one of them:
 *
 * 1. what Atlas concludes about entering (Sprint 4D);
 * 2. how the company fits this portfolio -- context inside a band,
 *    never across bands;
 * 3. Stance, unchanged;
 * 4. Daily Brief Agenda priority, unchanged;
 * 5. ticker, so equal candidates still order deterministically.
 *
 * Keys 2-5 and their null handling are exactly what they were before
 * this sprint; 4D only inserts key 1 ahead of them. */
function compareRank(a: RankedCandidate, b: RankedCandidate): number {
  const bandDiff = BAND_RANK[entrySupportBand(a.decisionSupport)] - BAND_RANK[entrySupportBand(b.decisionSupport)];
  if (bandDiff !== 0) return bandDiff;
  const fitRankOf = (c: RankedCandidate) => (c.fit ? FIT_RANK[c.fit] : 6);
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
