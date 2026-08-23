/**
 * Investment Case Workspace v2 (Sprint 2, Phase 1): pure, side-effect-
 * free derivations for the Investment Case's new Executive Summary --
 * the same "cross-reference already-fetched data, compute nothing new"
 * discipline `derivePortfolioActions.ts`/`deriveDiscussionPrompts.ts`
 * established for Portfolio Workspace v3. Every function here reads
 * only categorical values `GET /api/cases/{caseId}/analysis` and the
 * existing Alpha portfolio fetch already produce -- no new backend
 * call, no fabricated analysis.
 *
 * These functions decide *what* to show (which status, which grounded
 * sentence, which single priority); the actual English/Swedish text is
 * assembled by the caller via `t()`, the same split
 * `derivePortfolioActions.ts` uses (it returns `PortfolioAction`
 * objects, never translated strings) -- keeps this module pure and
 * independently testable.
 *
 * **No Recommendation.** Nothing here ever selects Build/Hold/Reduce/
 * Exit, a target position size, a target execution price, or a
 * portfolio-impact simulation -- that model does not exist in this
 * codebase yet (see `PortfolioPage.tsx`'s own `HoldingsTable` doc
 * comment for the identical, already-established rationale) and is
 * explicit, planned future work. `deriveCurrentPriority` below can only
 * ever select a *question to look at* (evidence, thesis, position,
 * outcome), never a directional instruction.
 */

export type ConvictionLevel = "very_high" | "high" | "moderate" | "low" | "insufficient_evidence";
export type ValuationStatus = "not_evaluated" | "insufficient_input" | "undervalued" | "fairly_valued" | "expensive";
export type RiskCategory = "business_risk" | "financial_risk" | "valuation_risk" | "thesis_risk";
export type RiskStatus = "not_evaluated" | "insufficient_input" | "low" | "moderate" | "high";
export type EvidenceCoverageLevel = "not_applicable" | "none" | "partial" | "full";
export type OutstandingWorkKind = "outcome-missing" | "trade-missing" | "reconciliation-needed";

export type CaseStatusLevel = "healthy" | "needs_review" | "high_priority";

export interface RiskFindingLite {
  category: RiskCategory;
  status: RiskStatus;
}

const RISK_SEVERITY_RANK: Record<RiskStatus, number> = {
  high: 3,
  moderate: 2,
  low: 1,
  insufficient_input: 0,
  not_evaluated: 0,
};

const RISK_CATEGORY_ORDER: RiskCategory[] = ["business_risk", "financial_risk", "valuation_risk", "thesis_risk"];

/**
 * The single highest-severity risk finding, mirroring the exact
 * selection rule `atlas/alpha/portfolio_cockpit/models.py`'s own
 * `RiskProjection` already documents server-side (HIGH > MODERATE > LOW
 * > INSUFFICIENT_INPUT/NOT_EVALUATED, ties broken by category's own
 * declared enum order -- deterministic, never arbitrary). Reapplied
 * client-side here because the Investment Case `/analysis` endpoint
 * returns the full four-category vector, not a pre-reduced projection
 * the way Portfolio Cockpit's does.
 */
export function findMostSevereRisk(findings: RiskFindingLite[]): RiskFindingLite | null {
  return findings.reduce<RiskFindingLite | null>((best, candidate) => {
    if (best === null) return candidate;
    const rankDiff = RISK_SEVERITY_RANK[candidate.status] - RISK_SEVERITY_RANK[best.status];
    if (rankDiff > 0) return candidate;
    if (rankDiff < 0) return best;
    return RISK_CATEGORY_ORDER.indexOf(candidate.category) < RISK_CATEGORY_ORDER.indexOf(best.category)
      ? candidate
      : best;
  }, null);
}

export type ValuationSupportStatus = "supported" | "not_supported" | "insufficient_input";
export type ValuationSupportGapKind =
  | "missing_capital_deployment_valuation_support"
  | "no_durable_growth_basis"
  | "insufficient_historical_valuation_data"
  | "scenario_envelope_inconclusive"
  | "conflicting_valuation_proofs"
  | "no_sufficient_valuation_proof";

export type LimitingFactor =
  | { kind: "valuationGap"; gap: ValuationSupportGapKind }
  | { kind: "risk"; category: RiskCategory };

/**
 * Beta Recommendation Experience implementation sprint (`UX-022` §3/§6):
 * the real, Core-derived "what limits this conclusion" content -- the
 * Figma's own "Limiting Factors" card and hero "Limited by:" line, per
 * `UX-022`'s exact data-source rule: only `RiskFinding`s tagged to the
 * four real categories, plus `ValuationSupport.gap`, nothing else (no
 * concentration threshold, no earnings-calendar timing claim, no
 * fabricated taxonomy). Returns at most 2, matching the Figma card's own
 * "1-2 items" visual structure -- may return 0, in which case the
 * section is omitted entirely, never filled with placeholder text.
 *
 * Ordering: the Valuation Support gap, when present, is shown first --
 * it is Recommendation's own most direct real "why not stronger" signal
 * (`DE-015`) -- then the remaining slot(s) are filled with the
 * highest-severity real Risk findings (reusing `RISK_SEVERITY_RANK`/
 * `RISK_CATEGORY_ORDER` above, the same deterministic ordering
 * `findMostSevereRisk` already uses), filtered to `moderate`/`high`
 * only -- `low`/`insufficient_input`/`not_evaluated` risk is not worth a
 * limiting-factor line, mirroring `isNoteworthyRisk` in `HeroCard.tsx`.
 */
export function deriveLimitingFactors(input: {
  riskFindings: RiskFindingLite[];
  valuationSupportStatus: ValuationSupportStatus;
  valuationSupportGap: ValuationSupportGapKind | null;
}): LimitingFactor[] {
  const factors: LimitingFactor[] = [];

  if (input.valuationSupportStatus !== "supported" && input.valuationSupportGap !== null) {
    factors.push({ kind: "valuationGap", gap: input.valuationSupportGap });
  }

  const noteworthyRisks = input.riskFindings
    .filter((f) => f.status === "high" || f.status === "moderate")
    .slice()
    .sort((a, b) => {
      const rankDiff = RISK_SEVERITY_RANK[b.status] - RISK_SEVERITY_RANK[a.status];
      if (rankDiff !== 0) return rankDiff;
      return RISK_CATEGORY_ORDER.indexOf(a.category) - RISK_CATEGORY_ORDER.indexOf(b.category);
    });

  for (const risk of noteworthyRisks) {
    if (factors.length >= 2) break;
    factors.push({ kind: "risk", category: risk.category });
  }

  return factors.slice(0, 2);
}

export interface CaseStatusInput {
  hasOutstandingWork: boolean;
  isThesisStale: boolean;
  openQuestionCount: number;
  evidenceGap: boolean;
}

/**
 * One clear status word, mirroring the exact severity ordering Portfolio
 * Workspace v3 already established for `AttentionCategory`: a case-level
 * workflow gap (a Decision with no Outcome, an Outcome with no trade
 * recorded, a holding awaiting reconciliation) outranks a stale thesis,
 * an open question, or an evidence gap, which in turn outranks nothing
 * outstanding at all. Three plain words, never a numeric score.
 */
export function deriveCaseStatus(input: CaseStatusInput): CaseStatusLevel {
  if (input.hasOutstandingWork) return "high_priority";
  if (input.isThesisStale || input.openQuestionCount > 0 || input.evidenceGap) return "needs_review";
  return "healthy";
}

export type CurrentPriorityKind = "outcomeMissing" | "reconciliationNeeded" | "thesisStale" | "openQuestion" | "none";

/**
 * Exactly one item -- "the single highest-priority action," per the
 * sprint's own instruction -- selected from already-existing facts only.
 * Deliberately never Build/Hold/Reduce/Exit/target-size/target-price
 * (see this module's own file-header rationale): every possible return
 * value here names a question to go look at, not an instruction to
 * act on the position. Priority order matches `deriveCaseStatus`'s own
 * severity ordering (workflow gaps first, then thesis/evidence
 * questions), with a fixed, documented tie-break among the three
 * equally-severe workflow-gap kinds (outcome-missing and trade-missing
 * both read as "complete the missing outcome"; reconciliation is a
 * distinct, portfolio-facing action).
 */
export function deriveCurrentPriority(input: {
  outstandingWorkKinds: OutstandingWorkKind[];
  isThesisStale: boolean;
  openQuestionCount: number;
}): CurrentPriorityKind {
  if (
    input.outstandingWorkKinds.includes("outcome-missing") ||
    input.outstandingWorkKinds.includes("trade-missing")
  ) {
    return "outcomeMissing";
  }
  if (input.outstandingWorkKinds.includes("reconciliation-needed")) return "reconciliationNeeded";
  if (input.isThesisStale) return "thesisStale";
  if (input.openQuestionCount > 0) return "openQuestion";
  return "none";
}

export type OutstandingIssueKind = "missingEvidence" | "thesisStale" | "outcomeMissing" | "tradeMissing" | "reconciliationNeeded";

/**
 * The full bullet list (unlike `deriveCurrentPriority`, every real issue
 * is shown, not just the top one) -- each entry a direct read of an
 * already-computed flag, same source data as `deriveCaseStatus` and the
 * page's own existing "Outstanding work" section further down.
 */
export function deriveOutstandingIssues(input: {
  outstandingWorkKinds: OutstandingWorkKind[];
  isThesisStale: boolean;
  evidenceGap: boolean;
}): OutstandingIssueKind[] {
  const issues: OutstandingIssueKind[] = [];
  if (input.evidenceGap) issues.push("missingEvidence");
  if (input.isThesisStale) issues.push("thesisStale");
  if (input.outstandingWorkKinds.includes("outcome-missing")) issues.push("outcomeMissing");
  if (input.outstandingWorkKinds.includes("trade-missing")) issues.push("tradeMissing");
  if (input.outstandingWorkKinds.includes("reconciliation-needed")) issues.push("reconciliationNeeded");
  return issues;
}

