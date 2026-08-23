import type { RegulatoryFilingView } from "./managementIntelligenceApi";

/**
 * Product Utilization Sprint 1 (Investment Case Experience Activation).
 * Phase 7's own "no ambiguous empty cards" requirement, for the six
 * Filing-Content-Intelligence-family capabilities: an empty
 * `filingsConsidered` list is not one honest state, it is (at least)
 * two, and this codebase already has the data to tell them apart
 * without any new backend field or explainability system (Phase 5's
 * own "reuse existing data").
 *
 * - `has_evidence`: the capability actually has real, disclosed
 *   evidence to show.
 * - `content_not_yet_acquired`: Atlas already knows a relevant filing
 *   exists (it is right there in `regulatoryFilings`, ingested,
 *   real), but no production path has read that filing's own content
 *   yet -- see Integration Sprint 1's own Final Report for exactly
 *   why. A genuinely different, more informative message than "no
 *   data": the user should expect this to fill in once filing-content
 *   acquisition is built, not read it as "Atlas checked and found
 *   nothing."
 * - `no_relevant_filing_known`: Atlas has not even discovered a
 *   filing of the relevant type for this company -- an earlier-stage,
 *   more fundamental gap.
 *
 * Mirrors the exact `_GOVERNANCE_RELEVANT_FORM_TYPES`-style sets
 * `atlas.alpha.knowledge_coverage.engine` already declares for these
 * same domains -- the identical, already-established reasoning,
 * reused here rather than invented fresh.
 */
export type FilingContentStatus = "has_evidence" | "content_not_yet_acquired" | "no_relevant_filing_known";

export function filingContentStatus(
  regulatoryFilings: RegulatoryFilingView[],
  relevantFormTypes: readonly string[],
  filingsConsidered: readonly string[],
): FilingContentStatus {
  if (filingsConsidered.length > 0) return "has_evidence";
  const hasRelevantFiling = regulatoryFilings.some((f) => relevantFormTypes.includes(f.formType));
  return hasRelevantFiling ? "content_not_yet_acquired" : "no_relevant_filing_known";
}

export const GOVERNANCE_RELEVANT_FORM_TYPES = ["10-K", "DEF 14A"] as const;
export const RISK_FACTOR_RELEVANT_FORM_TYPES = ["10-K", "10-Q"] as const;
export const LEGAL_PROCEEDINGS_RELEVANT_FORM_TYPES = ["10-K", "10-Q"] as const;
export const OWNERSHIP_RELEVANT_FORM_TYPES = ["DEF 14A"] as const;
export const EXECUTIVE_COMPENSATION_RELEVANT_FORM_TYPES = ["DEF 14A"] as const;
