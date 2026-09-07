import type { TranslationKey } from "../i18n";
import type {
  CanonicalEngine,
  ChangeTriggerKind,
  InvestmentReasonKind,
  InvestmentReasonView,
  KeyUnknownView,
} from "./reasoningContract";

/**
 * Closed backend vocabularies -> investor language. The same role
 * `describeInvestmentDecision.ts` plays for actions and qualifiers,
 * and the same rule: this module only looks tokens up. It derives
 * nothing, ranks nothing, and merges nothing -- ordering is the
 * backend's own `_ENGINE_PRECEDENCE`, and it arrives already applied.
 */

export const REASON_KIND_KEY: Record<InvestmentReasonKind, TranslationKey> = {
  growth_strong: "investmentReasoning.reason.growthStrong",
  growth_moderate: "investmentReasoning.reason.growthModerate",
  growth_weak: "investmentReasoning.reason.growthWeak",
  capital_allocation_strong: "investmentReasoning.reason.capitalAllocationStrong",
  capital_allocation_moderate: "investmentReasoning.reason.capitalAllocationModerate",
  capital_allocation_weak: "investmentReasoning.reason.capitalAllocationWeak",
  valuation_undervalued: "investmentReasoning.reason.valuationUndervalued",
  valuation_fairly_valued: "investmentReasoning.reason.valuationFairlyValued",
  valuation_expensive: "investmentReasoning.reason.valuationExpensive",
  valuation_supported: "investmentReasoning.reason.valuationSupported",
  valuation_not_supported: "investmentReasoning.reason.valuationNotSupported",
  financial_risk_elevated: "investmentReasoning.reason.financialRiskElevated",
  financial_risk_not_elevated: "investmentReasoning.reason.financialRiskNotElevated",
};

export const ENGINE_KEY: Record<CanonicalEngine, TranslationKey> = {
  growth: "investmentReasoning.engine.growth",
  capital_allocation: "investmentReasoning.engine.capitalAllocation",
  valuation: "investmentReasoning.engine.valuation",
  valuation_support: "investmentReasoning.engine.valuationSupport",
  financial_risk: "investmentReasoning.engine.financialRisk",
  business_quality: "investmentReasoning.engine.businessQuality",
  industry_context: "investmentReasoning.engine.industryContext",
  expected_return: "investmentReasoning.engine.expectedReturn",
};

export const CHANGE_TRIGGER_KEY: Record<ChangeTriggerKind, TranslationKey> = {
  reduced_risk: "investmentReasoning.trigger.reducedRisk",
  more_attractive_valuation: "investmentReasoning.trigger.moreAttractiveValuation",
  improved_growth_evidence: "investmentReasoning.trigger.improvedGrowthEvidence",
  improved_capital_allocation_evidence: "investmentReasoning.trigger.improvedCapitalAllocationEvidence",
  lower_valuation: "investmentReasoning.trigger.lowerValuation",
  financial_risk_becomes_elevated: "investmentReasoning.trigger.financialRiskBecomesElevated",
  valuation_becomes_expensive: "investmentReasoning.trigger.valuationBecomesExpensive",
  valuation_support_lost: "investmentReasoning.trigger.valuationSupportLost",
  growth_deteriorates: "investmentReasoning.trigger.growthDeteriorates",
  capital_allocation_deteriorates: "investmentReasoning.trigger.capitalAllocationDeteriorates",
  no_credible_trigger_identified: "investmentReasoning.trigger.noCredibleTrigger",
};

export function reasonKindLabel(
  reason: InvestmentReasonView,
  t: (key: TranslationKey) => string,
): string {
  return t(REASON_KIND_KEY[reason.kind]);
}

/**
 * A key unknown is a *kind* plus the engine it belongs to -- rendered
 * together, because "input missing" means something quite different
 * for Valuation Support than for Growth. `not_connected_to_direction`
 * is deliberately not surfaced: it describes Atlas's own engine
 * wiring, not an unknown about the company.
 */
export function keyUnknownLabel(
  unknown: KeyUnknownView,
  t: (key: TranslationKey, params?: Record<string, string | number>) => string,
): string | null {
  if (unknown.kind === "not_connected_to_direction") return null;
  const engine = t(ENGINE_KEY[unknown.engine]);
  return unknown.kind === "analysis_input_missing"
    ? t("investmentReasoning.unknown.inputMissing", { engine })
    : t("investmentReasoning.unknown.unresolved", { engine });
}
