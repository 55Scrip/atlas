/**
 * The canonical Recommendation Reasoning wire contract.
 *
 * Mirrors `atlas.analysis_engine.reasoning.serialize_reasoning` field
 * for field. That function is deterministic and total, and every value
 * it writes is a closed-vocabulary token -- so this file is a
 * transcription of an existing contract, never a second model of it.
 * Nothing here is derived, ranked, merged, or renamed: display text is
 * looked up from these tokens at the presentation edge, which is what
 * lets wording change without rewriting stored history.
 *
 * Why it exists: the payload was already produced, persisted and
 * served (`InvestmentDecisionView.reasoning`), but the frontend never
 * declared it -- so the canonical synthesis stopped at the network
 * boundary and each component re-explained its own local state
 * instead. Typing it is the whole fix.
 *
 * Every field is optional-safe on read. `reasoning` may legitimately be
 * absent -- legacy rows written before reasoning was persisted, and
 * outcomes the analysis engine never produced -- and the UI must
 * degrade to showing nothing rather than assuming presence.
 */

export type ReasoningPolarity = "supportive" | "adverse" | "neutral";

export type CanonicalEngine =
  | "growth"
  | "capital_allocation"
  | "valuation"
  | "valuation_support"
  | "financial_risk"
  | "business_quality"
  | "industry_context"
  | "expected_return";

export type InvestmentReasonKind =
  | "growth_strong"
  | "growth_moderate"
  | "growth_weak"
  | "capital_allocation_strong"
  | "capital_allocation_moderate"
  | "capital_allocation_weak"
  | "valuation_undervalued"
  | "valuation_fairly_valued"
  | "valuation_expensive"
  | "valuation_supported"
  | "valuation_not_supported"
  | "financial_risk_elevated"
  | "financial_risk_not_elevated";

export type SignalState = "conclusive" | "inconclusive" | "not_evaluated" | "not_in_direction_contract";

export type KeyUnknownKind =
  | "analysis_input_missing"
  | "not_connected_to_direction"
  | "analysis_complete_unresolved";

export type ChangeTriggerKind =
  | "reduced_risk"
  | "more_attractive_valuation"
  | "improved_growth_evidence"
  | "improved_capital_allocation_evidence"
  | "lower_valuation"
  | "financial_risk_becomes_elevated"
  | "valuation_becomes_expensive"
  | "valuation_support_lost"
  | "growth_deteriorates"
  | "capital_allocation_deteriorates"
  | "no_credible_trigger_identified";

export type ProcessStateReasonKind =
  | "evidence_coverage_partial"
  | "evidence_coverage_full"
  | "contradicting_evidence_present"
  | "no_contradicting_evidence"
  | "open_questions_remain"
  | "no_open_questions"
  | "company_fundamentals_evidence_only";

export type RecommendationConvictionLevel = "high" | "medium" | "low";

export interface InvestmentReasonView {
  kind: InvestmentReasonKind;
  polarity: ReasoningPolarity;
  engine: CanonicalEngine;
  sourceStatus: string | null;
}

/**
 * `influencedDirection` is a *direction-contract membership* marker,
 * not a claim that a direction resulted: the backend sets it `true`
 * for exactly the five engines Direction Selection reads, and `false`
 * for the three it does not (`build_signal_summary`). It is therefore
 * equally true on a withheld outcome -- and must never be rendered as
 * "this drove Atlas's recommendation" when no recommendation exists.
 *
 * The magnitude fields are explanatory projections of an engine's own
 * measurement. `null` means no principled value exists and stays
 * distinct from a computed `0`.
 */
export interface SignalContributionView {
  engine: CanonicalEngine;
  state: SignalState;
  influencedDirection: boolean;
  sourceStatus: string | null;
  revenueCagr: number | null;
  freeCashFlowCagr: number | null;
  currentYield: number | null;
  historicalMedianYield: number | null;
  historicalPercentile: number | null;
  historicalObservationCount: number | null;
  /** Valuation contribution only: whether the valuation history may
   * decide. The yield figures above then describe the prior fiscal
   * years, one each, whatever the eligibility. Absent on rows written
   * before it existed -- those counted market observations, not years. */
  evidenceEligibility?: ValuationEvidenceEligibility | null;
}

/** `ValuationDecisionEligibility` -- see `cash_flow.py`. */
export type ValuationEvidenceEligibility = "eligible" | "limited" | "insufficient" | "not_applicable";

export interface KeyUnknownView {
  kind: KeyUnknownKind;
  engine: CanonicalEngine;
}

/**
 * `DE-004` §3 Recommendation Conviction -- conviction in a *stated
 * direction*. Structurally `null` whenever the recommendation was
 * withheld: the backend refuses to construct it there
 * (`RecommendationWithheldWithReasoning.__post_init__`), so a
 * non-null value here is itself evidence that a direction exists.
 */
export interface RecommendationConvictionReasoningView {
  level: RecommendationConvictionLevel | null;
  analyticalReasons: InvestmentReasonView[];
  evidentialReasons: ProcessStateReasonKind[];
}

/**
 * The collection fields are optional, deliberately. The current
 * serializer writes all of them, but rows persisted before a given
 * field existed simply have no key -- which is exactly why the
 * backend's own `deserialize_reasoning` reads every one of them with
 * `.get(...)`. Mirroring that here keeps a legacy row a legacy row
 * instead of a runtime crash, and forces each read site to say what
 * absence means.
 */
export interface RecommendationReasoningView {
  schemaVersion: number;
  primaryDrivers?: InvestmentReasonView[];
  counterDrivers?: InvestmentReasonView[];
  signalSummary?: SignalContributionView[];
  keyUnknowns?: KeyUnknownView[];
  whatWouldChange?: ChangeTriggerKind[];
  recommendationConviction?: RecommendationConvictionReasoningView | null;
  /** `null` when Atlas holds no verified forward evidence; absent on rows
   * written before it existed. Context only -- see
   * `ForwardReasoningContextView`. */
  forwardContext?: ForwardReasoningContextView | null;
  /** What the `financial_risk` driver rests on. `null` when no basis was
   * carried; absent on rows written before it existed. Disclosure only --
   * see `RiskDriverBasisView`. */
  riskBasis?: RiskDriverBasisView | null;
}

export type RiskLevel = "not_evaluated" | "insufficient_input" | "not_applicable" | "low" | "moderate" | "high";

export type ElevatingRiskCategory = "financial_risk" | "valuation_risk";

/** Why Financial Risk v2 reached its level -- one token per branch of
 * the backend rule. */
export type FinancialRiskCondition =
  | "debt_burden_low"
  | "debt_burden_moderate"
  | "debt_burden_high"
  | "operating_cash_flow_negative"
  | "operating_cash_flow_zero"
  | "measure_not_applicable"
  | "no_eligible_evidence";

/** One fiscal period's debt burden, in the facts' own unit and never
 * rescaled. `operatingCashFlow` is free cash flow plus capital
 * expenditure; `ratio` is `null` when operating cash flow is not
 * positive (never divided). */
export interface DebtBurdenObservationView {
  period: string;
  unit: string;
  totalDebt: number;
  freeCashFlow: number;
  capitalExpenditure: number;
  operatingCashFlow: number;
  ratio: number | null;
  totalDebtFactId: string;
  freeCashFlowFactId: string;
  capitalExpenditureFactId: string;
  sourceRecordIds: string[];
}

/**
 * Financial Risk v2's own basis. `latest` is what the level rests on;
 * `history` (oldest first, ending with `latest`) is trend context and
 * never moves the level. `bands` are Atlas policy bands, not
 * credit-rating thresholds.
 */
export interface FinancialRiskBasisView {
  level: RiskLevel;
  condition: FinancialRiskCondition;
  measure: "gross_debt_to_operating_cash_flow" | null;
  bands: { lowBelow: number; highFrom: number };
  latest: DebtBurdenObservationView | null;
  history: DebtBurdenObservationView[];
  industry: string | null;
  gaps: string[];
  excluded: { factId: string; reason: "future_period" | "not_a_financial_statement" }[];
}

/**
 * Why the `financial_risk` driver reads as it does. `elevatedCategories`
 * is empty exactly when the driver is not elevated -- and can name only
 * `valuation_risk`, in which case "elevated financial risk" rests on
 * valuation, not on the company's finances. `version` is 2; a payload
 * without it is not interpreted.
 */
export interface RiskDriverBasisView {
  version: number;
  elevatedCategories: ElevatingRiskCategory[];
  financialRisk: FinancialRiskBasisView;
}

export type ForwardGuidanceSubject = "revenue" | "adjusted_ebitda" | "free_cash_flow" | "capital_expenditure";

/** What management's figure did. `reaffirmed` means the numbers did not
 * move -- never "supportive". */
export type GuidanceRevisionKind = "raised" | "lowered" | "reaffirmed";

export type ForwardHorizonKind = "fiscal_year" | "calendar_year" | "unspecified_year";

export type UnestablishedEconomics =
  | "price"
  | "revenue_contribution"
  | "earnings_contribution"
  | "cash_flow_contribution";

export interface ForwardGuidanceContextView {
  signalId: string;
  subject: ForwardGuidanceSubject;
  /** VST's "adjusted free cash flow before growth" is guidance for *a*
   * free-cash-flow measure, never Atlas's own FCF -- render it qualified. */
  measureDefinedByManagement: boolean;
  horizonPeriod: string;
  horizonKind: ForwardHorizonKind;
  revision: GuidanceRevisionKind;
  valueText: string;
  priorValueText: string | null;
  sourcePeriod: string | null;
  revisionCount: number;
}

/** One source *observation*, not one agreement: the same agreement can
 * be restated in several. Quantities are verbatim text only, so there is
 * nothing here to add up. */
export interface ContractedVolumeContextView {
  signalId: string;
  sourcePeriod: string | null;
  counterpartyText: string | null;
  agreementText: string;
  quantityTexts: string[];
  termYears: number | null;
  deliveryStartYears: number[];
  deliveryEndYears: number[];
  notEstablished: UnestablishedEconomics[];
}

/**
 * Verified forward evidence shown alongside the recommendation. It does
 * not decide the direction, carries no polarity, and must never be
 * rendered as a reason for or against. `identityResolved` is always
 * `false`: observations are not deduplicated into agreements.
 */
export interface ForwardReasoningContextView {
  guidance: ForwardGuidanceContextView[];
  contractedVolume: ContractedVolumeContextView[];
  counterpartyTexts: string[];
  unnamedObservationCount: number;
  unestablishedEconomics: UnestablishedEconomics[];
  identityResolved: boolean;
}
