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
}
