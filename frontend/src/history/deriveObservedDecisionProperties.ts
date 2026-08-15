/**
 * Sprint 14 (Observed Decision Properties -- First Frontend Integration):
 * a pure membership projection over the response of the existing
 * read-only `GET /observed-decision-properties` endpoint
 * (`atlas/alpha/observed_decision_properties`, Sprint 13). This module
 * performs no pattern recognition and no analytical computation of its
 * own -- it only indexes the API's own properties by the Decision ids
 * each one already names in `supportingDecisionIds`, so a Decision
 * Review card can look up "which observed properties, if any, include
 * this exact Decision" in O(1). The API is the sole source of truth for
 * which properties exist, their factual descriptions, scope, and every
 * semantic-limitation field (`outcomeAware`, `sampleSizeWarning`) --
 * this module neither recomputes nor reinterprets any of them.
 */

export type ObservedPropertyScope = "single_company" | "portfolio_wide";

export interface ObservedDecisionPropertyView {
  propertyType: string;
  factualDescription: string;
  scope: ObservedPropertyScope;
  observedCount: number;
  totalEligibleDecisions: number;
  proportion: number;
  supportingDecisionIds: string[];
  firstObservedAt: string;
  lastObservedAt: string;
  outcomeAware: boolean;
  sampleSizeWarning: boolean;
}

export interface ObservedDecisionPropertiesResponse {
  properties: ObservedDecisionPropertyView[];
  limitations: string[];
}

/** Decision id -> the properties (in the API's own response order) that
 * name that Decision in `supportingDecisionIds`. Preserves the API's
 * own order rather than re-sorting -- Sprint 13 already verified the
 * endpoint's determinism (same input -> same output), so re-deriving an
 * order here would be a second, redundant ordering decision the
 * frontend has no analytical basis to make. */
export function buildObservedPropertiesByDecisionId(
  properties: ObservedDecisionPropertyView[],
): Map<string, ObservedDecisionPropertyView[]> {
  const byDecisionId = new Map<string, ObservedDecisionPropertyView[]>();
  for (const property of properties) {
    for (const decisionId of property.supportingDecisionIds) {
      const existing = byDecisionId.get(decisionId);
      if (existing) existing.push(property);
      else byDecisionId.set(decisionId, [property]);
    }
  }
  return byDecisionId;
}
