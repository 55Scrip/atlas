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
}

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

export type RiskLevel = "not_evaluated" | "insufficient_input" | "low" | "moderate" | "high";

export type ElevatingRiskCategory = "financial_risk" | "valuation_risk";

export type FinancialRiskSignal = "capital_allocation" | "cash_generation" | "debt_trend";

export type FinancialRiskCondition =
  | "capital_allocation_weak"
  | "capital_allocation_moderate"
  | "capital_allocation_strong"
  | "capital_allocation_unavailable"
  | "latest_free_cash_flow_negative"
  | "latest_free_cash_flow_not_negative"
  | "no_free_cash_flow"
  | "total_debt_increased_every_period"
  | "total_debt_decreased_every_period"
  | "total_debt_no_consistent_direction"
  | "total_debt_fewer_than_two_periods";

export type FinancialRiskRule =
  | "any_signal_high"
  | "no_core_signal_assessed"
  | "core_signals_both_low"
  | "core_signal_not_low";

/** One reported figure exactly as the fact states it -- `period` is the
 * period-end date, `value` is in `unit` and never rescaled. */
export interface FinancialRiskObservationView {
  metric: "free_cash_flow" | "total_debt";
  period: string;
  value: number;
  unit: string;
  factId: string;
  sourceRecordId: string;
}

export interface FinancialRiskSignalBasisView {
  signal: FinancialRiskSignal;
  level: RiskLevel;
  condition: FinancialRiskCondition;
  sourceFindingId: string | null;
  observations: FinancialRiskObservationView[];
}

/** The Financial Risk evaluator's own basis. `determining` names the
 * signals the matched rule rests on -- for `high`, every high signal and
 * nothing else. A signal outside it is never a cause. */
export interface FinancialRiskBasisView {
  level: RiskLevel;
  rule: FinancialRiskRule;
  determining: FinancialRiskSignal[];
  signals: FinancialRiskSignalBasisView[];
}

/**
 * Why the `financial_risk` driver reads as it does. `elevatedCategories`
 * is empty exactly when the driver is not elevated -- and can name only
 * `valuation_risk`, in which case the "elevated financial risk" driver
 * rests on valuation, not on the company's finances.
 */
export interface RiskDriverBasisView {
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
