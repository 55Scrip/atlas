/**
 * Investment Case Decision Layer Bundle (Opportunity Cost Cross-Case
 * Computation Review, follow-up implementation sprint).
 *
 * Replaces the five separate requests the page previously fired for
 * opportunity-cost (base + change), decision-memory, decision-
 * explanation, and portfolio-decision with a single request -- all
 * four backend services share the same request-scoped memoization, so
 * the expensive cross-case scan behind `opportunity_cost` now runs
 * once per page load instead of five times. The five original
 * endpoints remain unchanged and available for any other caller.
 *
 * Field types are re-exported from each section's own, already-real
 * wire types -- nothing is redeclared here.
 */
import type { OpportunityCostChangeView, OpportunityCostView } from "../opportunityCost/opportunityCostApi";
import type { DecisionMemoryView } from "../decisionMemory/decisionMemoryApi";
import type { DecisionExplanationView } from "../decisionExplanation/decisionExplanationApi";
import type { PortfolioDecisionView } from "../portfolioDecision/portfolioDecisionApi";

export interface InvestmentCaseDecisionLayerBundleView {
  opportunityCost: OpportunityCostView | null;
  opportunityCostChange: OpportunityCostChangeView | null;
  decisionMemory: DecisionMemoryView | null;
  decisionExplanation: DecisionExplanationView | null;
  portfolioDecision: PortfolioDecisionView | null;
}

export function fetchInvestmentCaseDecisionLayerBundle(
  caseId: string,
  signal?: AbortSignal,
): Promise<InvestmentCaseDecisionLayerBundleView> {
  return fetch(`/api/cases/${encodeURIComponent(caseId)}/decision-layer-bundle`, { signal: signal ?? null }).then(
    (response) => {
      if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
      return response.json() as Promise<InvestmentCaseDecisionLayerBundleView>;
    },
  );
}
