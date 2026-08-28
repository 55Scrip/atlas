import type { TranslationKey } from "../i18n";
import type { StatusTone } from "../foundation";
import type {
  AnalysisBusinessStatus,
  AnalysisChangeDirection,
  AnalysisRiskStatus,
  AnalysisValuationStatus,
} from "../changeIntelligence/describeChange";

/**
 * Workspace Migration (Foundation extraction) — the single source of
 * truth for every categorical status this codebase renders across
 * Portfolio and Investment Case: Conviction, Confidence (Evidence
 * Coverage), Analysis Coverage, and Review Priority each previously
 * had their own, separately-declared `*_KEY` translation-key map
 * duplicated verbatim in both `PortfolioPage.tsx` and
 * `InvestmentCasePage.tsx` (the latter's own comment already said as
 * much: "Reused verbatim from PortfolioPage.tsx's own enum-value maps
 * ... must be identical, not just similarly worded"). This module is
 * that one shared declaration; both pages import from here instead of
 * re-declaring it.
 *
 * Risk/Valuation/Business status translation keys are **not**
 * redeclared here — those already live in
 * `../changeIntelligence/describeChange.ts` (extracted for History v1)
 * and are reused verbatim by type-only import. This module adds only
 * what that one doesn't yet have: a `StatusTone` for each value, for
 * `StatusBadge` (`../foundation`) to consume.
 *
 * Every tone assignment below is a direct, literal reading of the
 * enum's own ordinal meaning (more favorable → `positive`, worse →
 * `critical`, the "nothing to conclude yet" members → `neutral`) —
 * never a new judgment about the underlying data. No enum member is
 * reinterpreted differently on Portfolio than on Investment Case.
 */

export type ConvictionLevel = "very_high" | "high" | "moderate" | "low" | "insufficient_evidence";
export type EvidenceCoverageLevel = "not_applicable" | "none" | "partial" | "full";
export type AnalysisCoverageLevel = "no_coverage" | "partial_coverage" | "substantial_coverage";
export type ReviewPriority = "none" | "standard_review" | "evidence_review" | "priority_review";

export const CONVICTION_LEVEL_KEY: Record<ConvictionLevel, TranslationKey> = {
  very_high: "portfolio.cockpit.conviction.very_high",
  high: "portfolio.cockpit.conviction.high",
  moderate: "portfolio.cockpit.conviction.moderate",
  low: "portfolio.cockpit.conviction.low",
  insufficient_evidence: "portfolio.cockpit.conviction.insufficient_evidence",
};

export const CONVICTION_TONE: Record<ConvictionLevel, StatusTone> = {
  very_high: "positive",
  high: "positive",
  moderate: "caution",
  low: "caution",
  insufficient_evidence: "neutral",
};

/** Localization & Language Integrity Sprint: `ConvictionAssessment
 * .reasons` (`atlas/analysis_engine/conviction.py`'s
 * `ConvictionReasonCode`) is a real, bounded, always-populated enum --
 * every Conviction assessment names every applicable reason code, not
 * just the deciding one. Before this map existed, `InvestmentCasePage
 * .tsx` rendered these raw (`humanize()`'s underscores-to-spaces
 * fallback, e.g. "evidence coverage full"), in English only, on every
 * single Case's "More details" tab. */
export type ConvictionReasonCode =
  | "upstream_stage_not_evaluated"
  | "evidence_coverage_insufficient"
  | "evidence_coverage_partial"
  | "evidence_coverage_full"
  | "contradicting_evidence_present"
  | "no_contradicting_evidence"
  | "thesis_stale"
  | "thesis_not_stale"
  | "open_questions_remain"
  | "no_open_questions"
  | "business_or_valuation_not_yet_conclusive"
  | "business_and_valuation_conclusive"
  | "high_financial_or_valuation_risk_present"
  | "no_high_financial_or_valuation_risk";

export const CONVICTION_REASON_KEY: Record<ConvictionReasonCode, TranslationKey> = {
  upstream_stage_not_evaluated: "investmentCase.analysis.conviction.reason.upstreamStageNotEvaluated",
  evidence_coverage_insufficient: "investmentCase.analysis.conviction.reason.evidenceCoverageInsufficient",
  evidence_coverage_partial: "investmentCase.analysis.conviction.reason.evidenceCoveragePartial",
  evidence_coverage_full: "investmentCase.analysis.conviction.reason.evidenceCoverageFull",
  contradicting_evidence_present: "investmentCase.analysis.conviction.reason.contradictingEvidencePresent",
  no_contradicting_evidence: "investmentCase.analysis.conviction.reason.noContradictingEvidence",
  thesis_stale: "investmentCase.analysis.conviction.reason.thesisStale",
  thesis_not_stale: "investmentCase.analysis.conviction.reason.thesisNotStale",
  open_questions_remain: "investmentCase.analysis.conviction.reason.openQuestionsRemain",
  no_open_questions: "investmentCase.analysis.conviction.reason.noOpenQuestions",
  business_or_valuation_not_yet_conclusive:
    "investmentCase.analysis.conviction.reason.businessOrValuationNotYetConclusive",
  business_and_valuation_conclusive: "investmentCase.analysis.conviction.reason.businessAndValuationConclusive",
  high_financial_or_valuation_risk_present:
    "investmentCase.analysis.conviction.reason.highFinancialOrValuationRiskPresent",
  no_high_financial_or_valuation_risk: "investmentCase.analysis.conviction.reason.noHighFinancialOrValuationRisk",
};

export const CONFIDENCE_KEY: Record<EvidenceCoverageLevel, TranslationKey> = {
  not_applicable: "portfolio.intelligence.confidence.not_applicable",
  none: "portfolio.intelligence.confidence.none",
  partial: "portfolio.intelligence.confidence.partial",
  full: "portfolio.intelligence.confidence.full",
};

export const CONFIDENCE_TONE: Record<EvidenceCoverageLevel, StatusTone> = {
  full: "positive",
  partial: "caution",
  none: "neutral",
  not_applicable: "neutral",
};

/** Internal Alpha Fix Sprint 1 (IA-003): a separate signal from
 * Conviction above -- purely "how much does Atlas actually know about
 * this company," never investor evidence. Never merged into
 * Conviction's own key/tone maps. */
export const ANALYSIS_COVERAGE_LEVEL_KEY: Record<AnalysisCoverageLevel, TranslationKey> = {
  no_coverage: "portfolio.cockpit.analysisCoverage.no_coverage",
  partial_coverage: "portfolio.cockpit.analysisCoverage.partial_coverage",
  substantial_coverage: "portfolio.cockpit.analysisCoverage.substantial_coverage",
};

export const ANALYSIS_COVERAGE_TONE: Record<AnalysisCoverageLevel, StatusTone> = {
  substantial_coverage: "positive",
  partial_coverage: "caution",
  no_coverage: "neutral",
};

export const REVIEW_PRIORITY_KEY: Record<ReviewPriority, TranslationKey> = {
  none: "portfolio.cockpit.review.none",
  standard_review: "portfolio.cockpit.review.standard_review",
  evidence_review: "portfolio.cockpit.review.evidence_review",
  priority_review: "portfolio.cockpit.review.priority_review",
};

export const REVIEW_PRIORITY_TONE: Record<ReviewPriority, StatusTone> = {
  priority_review: "critical",
  evidence_review: "caution",
  standard_review: "neutral",
  none: "neutral",
};

/** Workspace Migration Phase 1 (Decision Support presentation layer) --
 * mirrors the backend's `atlas.alpha.decision_support.DecisionSupportLevel`
 * exactly (7 members). The API sends `level`/`badgeLabel`/`statement`
 * together, but this codebase's own i18n convention (every other
 * categorical field here) is: the frontend owns the localized text via
 * its own `LEVEL_KEY` map, keyed by the enum `level` alone -- so
 * `badgeLabel`/`statement` from the API are read only as an
 * English-only fallback shape check, never rendered directly. */
export type DecisionSupportLevel =
  | "entry_supported"
  | "increase_supported"
  | "thesis_intact"
  | "reduction_supported"
  | "exit_supported"
  | "no_action_supported"
  | "insufficient_evidence";

export const DECISION_SUPPORT_BADGE_KEY: Record<DecisionSupportLevel, TranslationKey> = {
  entry_supported: "decisionSupport.badge.entry_supported",
  increase_supported: "decisionSupport.badge.increase_supported",
  thesis_intact: "decisionSupport.badge.thesis_intact",
  reduction_supported: "decisionSupport.badge.reduction_supported",
  exit_supported: "decisionSupport.badge.exit_supported",
  no_action_supported: "decisionSupport.badge.no_action_supported",
  insufficient_evidence: "decisionSupport.badge.insufficient_evidence",
};

export const DECISION_SUPPORT_STATEMENT_KEY: Record<DecisionSupportLevel, TranslationKey> = {
  entry_supported: "decisionSupport.statement.entry_supported",
  increase_supported: "decisionSupport.statement.increase_supported",
  thesis_intact: "decisionSupport.statement.thesis_intact",
  reduction_supported: "decisionSupport.statement.reduction_supported",
  exit_supported: "decisionSupport.statement.exit_supported",
  no_action_supported: "decisionSupport.statement.no_action_supported",
  insufficient_evidence: "decisionSupport.statement.insufficient_evidence",
};

export const DECISION_SUPPORT_TONE: Record<DecisionSupportLevel, StatusTone> = {
  entry_supported: "positive",
  increase_supported: "positive",
  thesis_intact: "positive",
  reduction_supported: "caution",
  exit_supported: "critical",
  no_action_supported: "neutral",
  insufficient_evidence: "neutral",
};

/** Calibration Phase 2 (Investment Case Coherence Implementation),
 * Phase 6 -- mirrors the backend's `atlas.analysis_engine.recommendation
 * .ChangeTriggerKind` exactly (6 members). `noCredibleTriggerIdentified`
 * is a real, disclosed answer ("nothing here would credibly move this
 * call"), never rendered as if it were missing data. */
export type ChangeTriggerKind =
  | "reduced_risk"
  | "more_attractive_valuation"
  | "improved_growth_evidence"
  | "improved_capital_allocation_evidence"
  | "lower_valuation"
  | "no_credible_trigger_identified";

export const CHANGE_TRIGGER_KEY: Record<ChangeTriggerKind, TranslationKey> = {
  reduced_risk: "investmentCase.whatWouldChange.reducedRisk",
  more_attractive_valuation: "investmentCase.whatWouldChange.moreAttractiveValuation",
  improved_growth_evidence: "investmentCase.whatWouldChange.improvedGrowthEvidence",
  improved_capital_allocation_evidence: "investmentCase.whatWouldChange.improvedCapitalAllocationEvidence",
  lower_valuation: "investmentCase.whatWouldChange.lowerValuation",
  no_credible_trigger_identified: "investmentCase.whatWouldChange.noCredibleTriggerIdentified",
};

/** Recommendation / Decision Intelligence Sprint 1 -- mirrors the
 * backend's `atlas.analysis_engine.recommendation_outlook_context
 * .OutlookRecommendationRelationship` exactly (4 members). Disclosure
 * only: this fact is never read to alter `DecisionSupportLevel`/the
 * Recommendation copy above -- see that backend module's own docstring
 * for the DE-012/DE-014 boundary this respects. A render-facing caller
 * must present this as independent, correlated context next to the
 * Recommendation, never as its cause. */
export type OutlookRecommendationRelationship = "corroborates" | "diverges" | "mixed" | "unavailable";

export const OUTLOOK_ALIGNMENT_KEY: Record<OutlookRecommendationRelationship, TranslationKey> = {
  corroborates: "investmentCase.outlookAlignment.corroborates",
  diverges: "investmentCase.outlookAlignment.diverges",
  mixed: "investmentCase.outlookAlignment.mixed",
  unavailable: "investmentCase.outlookAlignment.unavailable",
};

/** Reuses `AnalysisRiskStatus`/`AnalysisValuationStatus`/
 * `AnalysisBusinessStatus` verbatim from `changeIntelligence
 * /describeChange.ts` -- their translation keys already live there;
 * only a tone is added here. */
export const RISK_STATUS_TONE: Record<AnalysisRiskStatus, StatusTone> = {
  high: "critical",
  moderate: "caution",
  low: "positive",
  insufficient_input: "neutral",
  not_evaluated: "neutral",
};

export const VALUATION_STATUS_TONE: Record<AnalysisValuationStatus, StatusTone> = {
  undervalued: "positive",
  fairly_valued: "neutral",
  expensive: "critical",
  insufficient_input: "neutral",
  not_evaluated: "neutral",
};

export const BUSINESS_STATUS_TONE: Record<AnalysisBusinessStatus, StatusTone> = {
  strong: "positive",
  moderate: "caution",
  weak: "critical",
  insufficient_input: "neutral",
  not_evaluated: "neutral",
};

/** Alpha Freeze correction sprint (resolving Principal Engineer Review 2.0
 * finding M-2) -- the first frontend exposure of `DE-015`'s
 * `ValuationSupport.status`. Mirrors the backend's own
 * `atlas.analysis_engine.valuation.support.ValuationSupportStatus`
 * exactly (three members). Presentation-layer labels only, per `UX-021`
 * Part 8 / `UX-022` -- the literal word "supported" is never rendered
 * directly, since `DE-015` §6 is explicit that `SUPPORTED` is a narrow,
 * downside-only claim, never a general valuation-attractiveness one. The
 * Core enum itself is unchanged; only this presentation mapping is new. */
export type ValuationSupportStatus = "supported" | "not_supported" | "insufficient_input";

export const VALUATION_SUPPORT_LABEL_KEY: Record<ValuationSupportStatus, TranslationKey> = {
  supported: "investmentCase.valuationSupport.present",
  not_supported: "investmentCase.valuationSupport.absent",
  insufficient_input: "investmentCase.valuationSupport.unresolved",
};

export const VALUATION_SUPPORT_TONE: Record<ValuationSupportStatus, StatusTone> = {
  supported: "positive",
  not_supported: "caution",
  insufficient_input: "neutral",
};

/** Beta Recommendation Experience implementation sprint (`UX-022` §9):
 * mirrors `atlas.analysis_engine.valuation.support.ValuationSupportGapKind`
 * exactly (six members). Present only when `ValuationSupportStatus` is not
 * `supported`. Copy is this frontend's own short, presentation-layer
 * paraphrase of the real backend `.reasoning` for each kind (never that
 * verbose internal string verbatim, per `ValuationSupportView`'s own "never
 * `.reasoning` verbatim" rule) -- calibrated to `UX-022` Part 9's own
 * worked example for `insufficient_historical_valuation_data`. */
export type ValuationSupportGapKind =
  | "missing_capital_deployment_valuation_support"
  | "no_durable_growth_basis"
  | "insufficient_historical_valuation_data"
  | "scenario_envelope_inconclusive"
  | "conflicting_valuation_proofs"
  | "no_sufficient_valuation_proof";

export const VALUATION_SUPPORT_GAP_COPY_KEY: Record<ValuationSupportGapKind, TranslationKey> = {
  missing_capital_deployment_valuation_support: "investmentCase.valuationSupport.gap.missingCapitalDeploymentValuationSupport",
  no_durable_growth_basis: "investmentCase.valuationSupport.gap.noDurableGrowthBasis",
  insufficient_historical_valuation_data: "investmentCase.valuationSupport.gap.insufficientHistoricalValuationData",
  scenario_envelope_inconclusive: "investmentCase.valuationSupport.gap.scenarioEnvelopeInconclusive",
  conflicting_valuation_proofs: "investmentCase.valuationSupport.gap.conflictingValuationProofs",
  no_sufficient_valuation_proof: "investmentCase.valuationSupport.gap.noSufficientValuationProof",
};

/** Beta Recommendation Experience implementation sprint (`UX-022` §4):
 * mirrors `atlas.decision_engine.contracts.MissingEvaluationCategory`
 * exactly (four members). Rendered as the real, per-case reason list
 * alongside (never in place of) the existing fixed Withheld headline --
 * see `RecommendationStateView.missing_evaluations`'s own docstring. */
export type MissingEvaluationCategory = "business_evaluation" | "valuation" | "portfolio_intelligence" | "reasoning";

export const MISSING_EVALUATION_COPY_KEY: Record<MissingEvaluationCategory, TranslationKey> = {
  business_evaluation: "investmentCase.withheld.missing.businessEvaluation",
  valuation: "investmentCase.withheld.missing.valuation",
  portfolio_intelligence: "investmentCase.withheld.missing.portfolioIntelligence",
  reasoning: "investmentCase.withheld.missing.reasoning",
};

/** Product Sprint 4 (Portfolio Fit Engine) -- mirrors the backend's
 * `atlas.alpha.portfolio_fit.models.FitRating` exactly (six members,
 * including `unavailable`). `StatusTone` only has four values, so
 * `excellent`/`good` deliberately share `positive` -- the qualitative
 * label text (not the tone) is what carries their distinction, the
 * same "label carries the fine-grained meaning, tone carries the
 * coarse one" reading this module's own docstring already establishes
 * for `CONVICTION_TONE`'s `very_high`/`high` pair. */
export type FitRating = "excellent" | "good" | "neutral" | "weak" | "poor" | "unavailable";

export const FIT_RATING_KEY: Record<FitRating, TranslationKey> = {
  excellent: "portfolioFit.rating.excellent",
  good: "portfolioFit.rating.good",
  neutral: "portfolioFit.rating.neutral",
  weak: "portfolioFit.rating.weak",
  poor: "portfolioFit.rating.poor",
  unavailable: "portfolioFit.rating.unavailable",
};

export const FIT_RATING_TONE: Record<FitRating, StatusTone> = {
  excellent: "positive",
  good: "positive",
  neutral: "neutral",
  weak: "caution",
  poor: "critical",
  unavailable: "neutral",
};

/** Mirrors `atlas.alpha.portfolio_fit.models.FitDimensionKind` exactly
 * (six members). */
export type FitDimensionKind = "business" | "valuation" | "risk" | "allocation" | "expected_contribution" | "cash_impact";

export const FIT_DIMENSION_KEY: Record<FitDimensionKind, TranslationKey> = {
  business: "portfolioFit.dimension.business",
  valuation: "portfolioFit.dimension.valuation",
  risk: "portfolioFit.dimension.risk",
  allocation: "portfolioFit.dimension.allocation",
  expected_contribution: "portfolioFit.dimension.expectedContribution",
  cash_impact: "portfolioFit.dimension.cashImpact",
};

/** Mirrors `atlas.alpha.portfolio_fit.models.FitTrend` exactly (five
 * members) -- sourced from the existing `ChangeIntelligence.thesis_impact`
 * (Deliverable 7's own "improved/worsened" requirement), never a second,
 * Portfolio-Fit-specific history. */
export type FitTrend = "improving" | "declining" | "mixed" | "unchanged" | "unavailable";

export const FIT_TREND_KEY: Record<FitTrend, TranslationKey> = {
  improving: "portfolioFit.trend.improving",
  declining: "portfolioFit.trend.declining",
  mixed: "portfolioFit.trend.mixed",
  unchanged: "portfolioFit.trend.unchanged",
  unavailable: "portfolioFit.trend.unavailable",
};

/** Product Sprint 6 (Daily Brief Agenda / Priority Engine) -- mirrors
 * the backend's `atlas.alpha.daily_brief_agenda.models.PriorityLevel`
 * exactly (four members). Never a number: the label text alone carries
 * the four-way distinction, matching every other categorical field in
 * this module. */
export type PriorityLevel = "critical" | "high" | "normal" | "low";

export const PRIORITY_LEVEL_KEY: Record<PriorityLevel, TranslationKey> = {
  critical: "dailyBriefAgenda.priority.critical",
  high: "dailyBriefAgenda.priority.high",
  normal: "dailyBriefAgenda.priority.normal",
  low: "dailyBriefAgenda.priority.low",
};

export const PRIORITY_LEVEL_TONE: Record<PriorityLevel, StatusTone> = {
  critical: "critical",
  high: "caution",
  normal: "neutral",
  low: "positive",
};

/** Internal Alpha Stabilization: this exact object literal was
 * independently declared three times (`portfolio/sortHoldings.ts`,
 * `discovery/groupCandidatesByTier.ts`, `routes/DiscoveryPage.tsx`) for
 * the same real purpose -- ranking already-flagged tickers by their
 * shared Daily Brief Agenda priority, highest first. Not a bug today
 * (all three agreed), but three independently-maintainable copies of
 * one ranking rule is exactly the kind of drift risk this stabilization
 * sprint targets. One shared source now; a ticker with no Agenda item
 * at all should compare below every real priority, hence the separate,
 * equally shared `NO_PRIORITY_RANK` sentinel rather than each caller
 * inventing its own placeholder value. */
export const PRIORITY_LEVEL_RANK: Record<PriorityLevel, number> = { critical: 3, high: 2, normal: 1, low: 0 };
export const NO_PRIORITY_RANK = -1;

/** Mirrors `atlas.alpha.daily_brief_agenda.models.AgendaItemKind`
 * exactly (eight members) -- each one doubles as the item's own
 * "recommended next step" label. */
export type AgendaItemKind =
  | "review_investment_case"
  | "review_portfolio_position"
  | "review_watchlist_candidate"
  | "compare_candidate"
  | "revisit_assumption"
  | "evaluate_case_condition"
  | "portfolio_risk"
  | "portfolio_opportunity";

export const AGENDA_ITEM_KIND_KEY: Record<AgendaItemKind, TranslationKey> = {
  review_investment_case: "dailyBriefAgenda.kind.reviewInvestmentCase",
  review_portfolio_position: "dailyBriefAgenda.kind.reviewPortfolioPosition",
  review_watchlist_candidate: "dailyBriefAgenda.kind.reviewWatchlistCandidate",
  compare_candidate: "dailyBriefAgenda.kind.compareCandidate",
  revisit_assumption: "dailyBriefAgenda.kind.revisitAssumption",
  evaluate_case_condition: "dailyBriefAgenda.kind.evaluateCaseCondition",
  portfolio_risk: "dailyBriefAgenda.kind.portfolioRisk",
  portfolio_opportunity: "dailyBriefAgenda.kind.portfolioOpportunity",
};

/** Mirrors `atlas.alpha.daily_brief_agenda.models.AgendaGroup` exactly
 * (four members) -- presentation-only, a small tag per item, never
 * used to reorder (priority always wins). */
export type AgendaGroup = "portfolio" | "watchlist" | "discovery" | "system";

export const AGENDA_GROUP_KEY: Record<AgendaGroup, TranslationKey> = {
  portfolio: "dailyBriefAgenda.group.portfolio",
  watchlist: "dailyBriefAgenda.group.watchlist",
  discovery: "dailyBriefAgenda.group.discovery",
  system: "dailyBriefAgenda.group.system",
};

/** Fix Sprint 4 (Daily Brief Signal Quality) -- mirrors
 * `atlas.alpha.daily_brief_agenda.models.SignalNature` exactly (two
 * members). Deliberately both `"neutral"` in tone: this distinguishes
 * *when* something is true, never *whether* it is good or bad news --
 * `PRIORITY_LEVEL_TONE` above already owns that judgment, and a change
 * event is not inherently more alarming than a persistent one (a
 * newly-blocked decision and a still-high concentration are each
 * exactly as serious as their own `priority` already says). */
export type SignalNature = "change_event" | "persistent_condition";

export const SIGNAL_NATURE_KEY: Record<SignalNature, TranslationKey> = {
  change_event: "dailyBriefAgenda.nature.changeEvent",
  persistent_condition: "dailyBriefAgenda.nature.persistentCondition",
};

export const SIGNAL_NATURE_TONE: Record<SignalNature, StatusTone> = {
  change_event: "neutral",
  persistent_condition: "neutral",
};

/** Localization fix (Portfolio live-verification follow-up) -- mirrors
 * `atlas.alpha.portfolio_status.models.AttentionCategory` exactly (six
 * members). Before this, a workflow-sourced item's `headline` was a
 * raw, backend-composed English sentence built directly from this
 * enum's own `.value` (`.replace('_', ' ').lower()`) -- the one gap in
 * an otherwise fully localized UI. `agendaItemHeadline`
 * (`../dailyBriefAgenda/describeAgendaHeadline.ts`) uses this map to
 * compose a translated version instead. */
export type AttentionCategory =
  | "MISSING_CASE"
  | "DECISION_WITHOUT_OUTCOME"
  | "OUTCOME_WITHOUT_EXECUTION"
  | "AWAITING_RECONCILIATION"
  | "VERY_OLD_CASE"
  | "OBSERVATION_WITHOUT_DECISION";

export const ATTENTION_CATEGORY_KEY: Record<AttentionCategory, TranslationKey> = {
  MISSING_CASE: "dailyBriefAgenda.attentionCategory.missingCase",
  DECISION_WITHOUT_OUTCOME: "dailyBriefAgenda.attentionCategory.decisionWithoutOutcome",
  OUTCOME_WITHOUT_EXECUTION: "dailyBriefAgenda.attentionCategory.outcomeWithoutExecution",
  AWAITING_RECONCILIATION: "dailyBriefAgenda.attentionCategory.awaitingReconciliation",
  VERY_OLD_CASE: "dailyBriefAgenda.attentionCategory.veryOldCase",
  OBSERVATION_WITHOUT_DECISION: "dailyBriefAgenda.attentionCategory.observationWithoutDecision",
};

/** Atlas Intelligence Sprint 1 (Data Coverage & Confidence Engine) --
 * mirrors `atlas.alpha.coverage.models.DimensionCoverageLevel` exactly
 * (five members). `unavailable`/`insufficient_evidence` both read
 * `neutral`, matching `ANALYSIS_COVERAGE_TONE`'s own convention: a real
 * evidence gap is disclosed honestly, never presented as alarming in
 * itself (that would overstate what a missing fact actually means).
 * `not_applicable` is likewise `neutral` -- it names a capability this
 * build of Atlas does not evaluate for any company, not a per-company
 * problem, so it must never share `unavailable`'s implication that more
 * data could close the gap. */
export type DimensionCoverageLevel = "available" | "partially_available" | "unavailable" | "insufficient_evidence" | "not_applicable";

export const DIMENSION_COVERAGE_LEVEL_KEY: Record<DimensionCoverageLevel, TranslationKey> = {
  available: "coverage.dimension.available",
  partially_available: "coverage.dimension.partiallyAvailable",
  unavailable: "coverage.dimension.unavailable",
  insufficient_evidence: "coverage.dimension.insufficientEvidence",
  not_applicable: "coverage.dimension.notApplicable",
};

export const DIMENSION_COVERAGE_TONE: Record<DimensionCoverageLevel, StatusTone> = {
  available: "positive",
  partially_available: "caution",
  unavailable: "neutral",
  insufficient_evidence: "neutral",
  not_applicable: "neutral",
};

/** Mirrors `atlas.alpha.coverage.models.ConfidenceLevel` exactly (four
 * members) -- how much an investor should trust Atlas's own
 * understanding of a case, derived purely from dimension coverage
 * counts, contradiction presence, and thesis staleness. A deliberately
 * separate concept from `ConvictionLevel`/`EvidenceCoverageLevel`
 * above -- see `atlas.alpha.coverage.engine`'s own module docstring. */
export type ConfidenceLevel = "high" | "moderate" | "limited" | "very_limited";

export const COVERAGE_CONFIDENCE_KEY: Record<ConfidenceLevel, TranslationKey> = {
  high: "coverage.confidence.high",
  moderate: "coverage.confidence.moderate",
  limited: "coverage.confidence.limited",
  very_limited: "coverage.confidence.veryLimited",
};

export const COVERAGE_CONFIDENCE_TONE: Record<ConfidenceLevel, StatusTone> = {
  high: "positive",
  moderate: "caution",
  limited: "caution",
  very_limited: "neutral",
};

/** Atlas Intelligence Sprint 2 (Recommendation Quality &
 * Actionability) -- mirrors `atlas.alpha.stance.models.StanceLevel`
 * exactly (seven members). Explicitly **not** a trade-sizing
 * instruction: `increase`/`reduce` name the *direction* of Atlas's
 * current view, never rendered alongside a share count or trade verb
 * anywhere in this codebase -- see `STANCE_LEVEL_KEY`'s own labels
 * ("View strengthened," never "Buy more"). `avoid_decision` is `critical`
 * tone -- the one level this engine reserves for a genuine red flag
 * (contradicting evidence, or Conviction itself unreachable), never
 * merely "not enough data yet" (that is `wait`, `neutral`). */
export type StanceLevel = "increase" | "maintain" | "reduce" | "review" | "wait" | "avoid_decision" | "no_recommendation";

export const STANCE_LEVEL_KEY: Record<StanceLevel, TranslationKey> = {
  increase: "stance.level.increase",
  maintain: "stance.level.maintain",
  reduce: "stance.level.reduce",
  review: "stance.level.review",
  wait: "stance.level.wait",
  avoid_decision: "stance.level.avoidDecision",
  no_recommendation: "stance.level.noRecommendation",
};

export const STANCE_LEVEL_TONE: Record<StanceLevel, StatusTone> = {
  increase: "positive",
  maintain: "neutral",
  reduce: "caution",
  review: "caution",
  wait: "neutral",
  avoid_decision: "critical",
  no_recommendation: "neutral",
};

/** Mirrors `atlas.alpha.stance.models.StanceReasonCode` exactly
 * (seventeen members). The presentation layer owns every sentence --
 * this engine only names real, already-computed facts, the same
 * `ConfidenceReasonCode`/`ConvictionReasonCode` precedent. */
export type StanceReasonCode =
  | "no_company_data"
  | "contradicting_evidence_present"
  | "conviction_insufficient"
  | "confidence_very_limited"
  | "confidence_limited"
  | "confidence_moderate"
  | "thesis_strengthened"
  | "thesis_weakened"
  | "thesis_mixed"
  | "thesis_unchanged"
  | "decision_support_favorable"
  | "decision_support_unfavorable"
  | "decision_support_neutral"
  | "portfolio_fit_weak"
  | "portfolio_fit_favorable"
  | "high_risk_present"
  | "no_high_risk";

export const STANCE_REASON_KEY: Record<StanceReasonCode, TranslationKey> = {
  no_company_data: "stance.reason.noCompanyData",
  contradicting_evidence_present: "stance.reason.contradictingEvidencePresent",
  conviction_insufficient: "stance.reason.convictionInsufficient",
  confidence_very_limited: "stance.reason.confidenceVeryLimited",
  confidence_limited: "stance.reason.confidenceLimited",
  confidence_moderate: "stance.reason.confidenceModerate",
  thesis_strengthened: "stance.reason.thesisStrengthened",
  thesis_weakened: "stance.reason.thesisWeakened",
  thesis_mixed: "stance.reason.thesisMixed",
  thesis_unchanged: "stance.reason.thesisUnchanged",
  decision_support_favorable: "stance.reason.decisionSupportFavorable",
  decision_support_unfavorable: "stance.reason.decisionSupportUnfavorable",
  decision_support_neutral: "stance.reason.decisionSupportNeutral",
  portfolio_fit_weak: "stance.reason.portfolioFitWeak",
  portfolio_fit_favorable: "stance.reason.portfolioFitFavorable",
  high_risk_present: "stance.reason.highRiskPresent",
  no_high_risk: "stance.reason.noHighRisk",
};

/** Mirrors `atlas.alpha.stance.models.StanceComparisonReasonCode`
 * exactly (three members). */
export type StanceComparisonReasonCode =
  | "preferred_has_a_more_favorable_stance"
  | "both_stances_tied"
  | "one_or_both_too_uncertain_to_compare";

export const STANCE_COMPARISON_REASON_KEY: Record<StanceComparisonReasonCode, TranslationKey> = {
  preferred_has_a_more_favorable_stance: "stance.compare.preferredHasMoreFavorableStance",
  both_stances_tied: "stance.compare.bothStancesTied",
  one_or_both_too_uncertain_to_compare: "stance.compare.oneOrBothTooUncertain",
};

/** Atlas Intelligence Sprint 4 (Evidence Quality & Conflict Resolution)
 * -- mirrors `atlas.alpha.evidence_quality.models.EvidenceQualityLevel`
 * exactly (nine members). `conflicting`/`unsupported` are the two real
 * red flags this engine reserves `critical` tone for -- a genuine,
 * detected problem with the evidence itself, never merely "not much
 * evidence yet" (that is `incomplete`/`not_applicable`, `neutral`).
 * `superseded` is a reserved, never-constructed state (see the
 * backend model's own docstring) -- included here only so this map
 * stays exhaustive against the real enum, not because the UI expects
 * to render it in practice. */
export type EvidenceQualityLevel =
  | "fresh"
  | "recent"
  | "old"
  | "stale"
  | "superseded"
  | "conflicting"
  | "incomplete"
  | "unsupported"
  | "not_applicable";

export const EVIDENCE_QUALITY_LEVEL_KEY: Record<EvidenceQualityLevel, TranslationKey> = {
  fresh: "evidenceQuality.level.fresh",
  recent: "evidenceQuality.level.recent",
  old: "evidenceQuality.level.old",
  stale: "evidenceQuality.level.stale",
  superseded: "evidenceQuality.level.superseded",
  conflicting: "evidenceQuality.level.conflicting",
  incomplete: "evidenceQuality.level.incomplete",
  unsupported: "evidenceQuality.level.unsupported",
  not_applicable: "evidenceQuality.level.notApplicable",
};

export const EVIDENCE_QUALITY_LEVEL_TONE: Record<EvidenceQualityLevel, StatusTone> = {
  fresh: "positive",
  recent: "positive",
  old: "caution",
  stale: "caution",
  superseded: "neutral",
  conflicting: "critical",
  incomplete: "caution",
  unsupported: "critical",
  not_applicable: "neutral",
};

/** Mirrors `atlas.alpha.evidence_quality.models.EvidenceFreshness`
 * exactly (five members) -- the narrower, per-fact freshness bucket
 * `EvidenceQualityLevel` above's own `fresh`/`recent`/`old`/`stale`
 * members are rolled up from. */
export type EvidenceFreshness = "fresh" | "recent" | "old" | "stale" | "not_applicable";

export const EVIDENCE_FRESHNESS_KEY: Record<EvidenceFreshness, TranslationKey> = {
  fresh: "evidenceQuality.level.fresh",
  recent: "evidenceQuality.level.recent",
  old: "evidenceQuality.level.old",
  stale: "evidenceQuality.level.stale",
  not_applicable: "evidenceQuality.level.notApplicable",
};

/** Mirrors `atlas.alpha.evidence_quality.models.EvidenceWarningCode`
 * exactly (six members). The presentation layer owns every sentence,
 * the same `StanceReasonCode`/`ConfidenceReasonCode` convention. */
export type EvidenceWarningCode =
  | "conflicting_source_values"
  | "evidence_stale"
  | "single_source_dependency"
  | "conclusion_without_support"
  | "partial_coverage"
  | "no_evidence";

export const EVIDENCE_WARNING_KEY: Record<EvidenceWarningCode, TranslationKey> = {
  conflicting_source_values: "evidenceQuality.warning.conflictingSourceValues",
  evidence_stale: "evidenceQuality.warning.evidenceStale",
  single_source_dependency: "evidenceQuality.warning.singleSourceDependency",
  conclusion_without_support: "evidenceQuality.warning.conclusionWithoutSupport",
  partial_coverage: "evidenceQuality.warning.partialCoverage",
  no_evidence: "evidenceQuality.warning.noEvidence",
};

/** Mirrors `atlas.alpha.evidence_quality.models.EvidenceDominance`
 * exactly (three members). */
export type EvidenceDominance = "single_source" | "corroborated" | "not_applicable";

export const EVIDENCE_DOMINANCE_KEY: Record<EvidenceDominance, TranslationKey> = {
  single_source: "evidenceQuality.dominance.singleSource",
  corroborated: "evidenceQuality.dominance.corroborated",
  not_applicable: "evidenceQuality.dominance.notApplicable",
};

/** Mirrors `atlas.alpha.evidence_quality.models.EvidenceConflictStatus`
 * exactly (three members). */
export type EvidenceConflictStatus = "consistent" | "conflicting" | "not_applicable";

export const EVIDENCE_CONFLICT_STATUS_KEY: Record<EvidenceConflictStatus, TranslationKey> = {
  consistent: "evidenceQuality.conflictStatus.consistent",
  conflicting: "evidenceQuality.conflictStatus.conflicting",
  not_applicable: "evidenceQuality.conflictStatus.notApplicable",
};

/** Atlas Intelligence Sprint 5 (Evidence Timeline & Historical
 * Understanding) -- mirrors `atlas.alpha.evidence_timeline.models
 * .EvidenceTransitionCategory` exactly (six members). Direction
 * (better/worse/neutral) is `AnalysisChangeDirection`, a separate
 * field, the same economy `investment_case_change.ChangeCategory`'s
 * own docstring documents -- reused verbatim from
 * `changeIntelligence/describeChange.ts`, never a second "positive/
 * negative/neutral" enum. */
export type EvidenceTransitionCategory =
  | "coverage_changed"
  | "confidence_changed"
  | "stance_changed"
  | "freshness_changed"
  | "conflict_status_changed"
  | "evidence_quality_changed";

export const EVIDENCE_TRANSITION_CATEGORY_KEY: Record<EvidenceTransitionCategory, TranslationKey> = {
  coverage_changed: "evidenceTimeline.category.coverageChanged",
  confidence_changed: "evidenceTimeline.category.confidenceChanged",
  stance_changed: "evidenceTimeline.category.stanceChanged",
  freshness_changed: "evidenceTimeline.category.freshnessChanged",
  conflict_status_changed: "evidenceTimeline.category.conflictStatusChanged",
  evidence_quality_changed: "evidenceTimeline.category.evidenceQualityChanged",
};

export const EVIDENCE_TRANSITION_DIRECTION_TONE: Record<AnalysisChangeDirection, StatusTone> = {
  positive: "positive",
  negative: "critical",
  neutral: "neutral",
};

/** One sentence per (category, direction) pair -- the presentation
 * layer owns every sentence, the same closed-reason-code convention
 * every prior Sprint's own reason/warning maps already establish.
 * `AnalysisChangeDirection` (not re-declared here) is imported by
 * `describeEvidenceTimeline.ts`, which builds the actual `Record`
 * keyed by both fields -- see that module for the full sentence set. */

/** Atlas Intelligence -- Materiality & Priority Engine -- mirrors
 * `atlas.alpha.materiality.models.MaterialityLevel` exactly (six
 * members). `critical`/`high` share `critical`/`caution` tone with
 * every other Sprint's own real-red-flag convention; `background`/
 * `unknown` read `neutral` -- true, never alarming. */
export type MaterialityLevel = "critical" | "high" | "medium" | "low" | "background" | "unknown";

export const MATERIALITY_LEVEL_KEY: Record<MaterialityLevel, TranslationKey> = {
  critical: "materiality.level.critical",
  high: "materiality.level.high",
  medium: "materiality.level.medium",
  low: "materiality.level.low",
  background: "materiality.level.background",
  unknown: "materiality.level.unknown",
};

export const MATERIALITY_LEVEL_TONE: Record<MaterialityLevel, StatusTone> = {
  critical: "critical",
  high: "caution",
  medium: "neutral",
  low: "neutral",
  background: "neutral",
  unknown: "neutral",
};

/**
 * Atlas Intelligence Sprint 7 (Monitoring & Change Detection,
 * Deliverable 18/23). Mirrors `atlas.alpha.monitoring.models
 * .MonitoringStatus` exactly (five-member closed vocabulary).
 */
export type MonitoringStatus = "up_to_date" | "changed_review_suggested" | "changed_high_importance" | "waiting_for_better_evidence" | "unavailable";

export const MONITORING_STATUS_KEY: Record<MonitoringStatus, TranslationKey> = {
  up_to_date: "monitoring.status.upToDate",
  changed_review_suggested: "monitoring.status.changedReviewSuggested",
  changed_high_importance: "monitoring.status.changedHighImportance",
  waiting_for_better_evidence: "monitoring.status.waitingForBetterEvidence",
  unavailable: "monitoring.status.unavailable",
};

export const MONITORING_STATUS_TONE: Record<MonitoringStatus, StatusTone> = {
  up_to_date: "positive",
  changed_review_suggested: "neutral",
  changed_high_importance: "caution",
  waiting_for_better_evidence: "neutral",
  unavailable: "neutral",
};

/**
 * Atlas Intelligence Sprint 9 (Data Ingestion & Automatic Refresh,
 * Deliverable 6/7/13). Mirrors `atlas.alpha.ingestion.engine
 * .DataFreshnessStatus` exactly. Deliberately operations-only language
 * (Deliverable 13) -- never "confidence"/"stance"/"conviction".
 */
export type DataFreshnessStatus = "waiting_for_new_data" | "waiting_for_analysis" | "monitoring_failed" | "no_data_source" | "unknown";

export const DATA_FRESHNESS_STATUS_KEY: Record<DataFreshnessStatus, TranslationKey> = {
  waiting_for_new_data: "dataFreshness.status.waitingForNewData",
  waiting_for_analysis: "dataFreshness.status.waitingForAnalysis",
  monitoring_failed: "dataFreshness.status.monitoringFailed",
  no_data_source: "dataFreshness.status.noDataSource",
  unknown: "dataFreshness.status.unknown",
};

export const DATA_FRESHNESS_STATUS_TONE: Record<DataFreshnessStatus, StatusTone> = {
  waiting_for_new_data: "positive",
  waiting_for_analysis: "neutral",
  monitoring_failed: "caution",
  no_data_source: "neutral",
  unknown: "neutral",
};

/** Automatic Investment Case Builder Foundation -- mirrors
 * `atlas.alpha.knowledge_coverage.models.KnowledgeDomainGroup` exactly
 * (eight members). Purely organizational, never itself a coverage
 * signal -- no tone map. */
export type KnowledgeDomainGroup =
  | "company_overview"
  | "financials"
  | "governance_ownership"
  | "valuation"
  | "events_filings"
  | "macro_external_exposure"
  | "risk_opportunity"
  | "case_memory";

export const KNOWLEDGE_DOMAIN_GROUP_KEY: Record<KnowledgeDomainGroup, TranslationKey> = {
  company_overview: "knowledgeDomainGroup.companyOverview",
  financials: "knowledgeDomainGroup.financials",
  governance_ownership: "knowledgeDomainGroup.governanceOwnership",
  valuation: "knowledgeDomainGroup.valuation",
  events_filings: "knowledgeDomainGroup.eventsFilings",
  macro_external_exposure: "knowledgeDomainGroup.macroExternalExposure",
  risk_opportunity: "knowledgeDomainGroup.riskOpportunity",
  case_memory: "knowledgeDomainGroup.caseMemory",
};

/** Automatic Investment Case Builder Foundation -- mirrors
 * `atlas.alpha.knowledge_coverage.models.KnowledgeDomain` exactly
 * (36 members). Only 3 have a real extractor wired in this build of
 * Atlas (`company_profile`/`financial_history`/`valuation`); every
 * other member is a real, named, currently `not_applicable` domain --
 * "framework, not complete dataset." */
export type KnowledgeDomain =
  | "company_profile"
  | "business_model"
  | "revenue_segments"
  | "geographic_exposure"
  | "industry"
  | "competitors"
  | "competitive_advantages"
  | "financial_history"
  | "growth"
  | "profitability"
  | "cash_flow"
  | "balance_sheet"
  | "capital_allocation"
  | "shareholder_returns"
  | "management"
  | "ownership"
  | "insider_activity"
  | "institutional_ownership"
  | "valuation"
  | "historical_valuation"
  | "analyst_expectations"
  | "earnings"
  | "earnings_call_analysis"
  | "regulatory_filings"
  | "important_news"
  | "macro_exposure"
  | "geopolitical_exposure"
  | "commodity_exposure"
  | "currency_exposure"
  | "ai_exposure"
  | "risk_factors"
  | "opportunities"
  | "monitoring_status"
  | "historical_observations"
  | "existing_evidence"
  | "knowledge_references"
  /** Product Utilization Sprint 1 (Investment Case Experience
   * Activation), Phase 6: `governance`/`legal_proceedings`/
   * `executive_compensation` (Capability Expansion Sprints 15/18/20)
   * were real backend `KnowledgeDomain` members this union type never
   * grew to match -- a genuine, already-live gap (a real Case with a
   * relevant filing would send one of these three, and `KNOWLEDGE_
   * DOMAIN_KEY` had no entry for it), not new backend knowledge. */
  | "governance"
  | "legal_proceedings"
  | "executive_compensation";

export const KNOWLEDGE_DOMAIN_KEY: Record<KnowledgeDomain, TranslationKey> = {
  company_profile: "knowledgeDomain.companyProfile",
  business_model: "knowledgeDomain.businessModel",
  revenue_segments: "knowledgeDomain.revenueSegments",
  geographic_exposure: "knowledgeDomain.geographicExposure",
  industry: "knowledgeDomain.industry",
  competitors: "knowledgeDomain.competitors",
  competitive_advantages: "knowledgeDomain.competitiveAdvantages",
  financial_history: "knowledgeDomain.financialHistory",
  growth: "knowledgeDomain.growth",
  profitability: "knowledgeDomain.profitability",
  cash_flow: "knowledgeDomain.cashFlow",
  balance_sheet: "knowledgeDomain.balanceSheet",
  capital_allocation: "knowledgeDomain.capitalAllocation",
  shareholder_returns: "knowledgeDomain.shareholderReturns",
  management: "knowledgeDomain.management",
  ownership: "knowledgeDomain.ownership",
  insider_activity: "knowledgeDomain.insiderActivity",
  institutional_ownership: "knowledgeDomain.institutionalOwnership",
  valuation: "knowledgeDomain.valuation",
  historical_valuation: "knowledgeDomain.historicalValuation",
  analyst_expectations: "knowledgeDomain.analystExpectations",
  earnings: "knowledgeDomain.earnings",
  earnings_call_analysis: "knowledgeDomain.earningsCallAnalysis",
  regulatory_filings: "knowledgeDomain.regulatoryFilings",
  important_news: "knowledgeDomain.importantNews",
  macro_exposure: "knowledgeDomain.macroExposure",
  geopolitical_exposure: "knowledgeDomain.geopoliticalExposure",
  commodity_exposure: "knowledgeDomain.commodityExposure",
  currency_exposure: "knowledgeDomain.currencyExposure",
  ai_exposure: "knowledgeDomain.aiExposure",
  risk_factors: "knowledgeDomain.riskFactors",
  opportunities: "knowledgeDomain.opportunities",
  monitoring_status: "knowledgeDomain.monitoringStatus",
  historical_observations: "knowledgeDomain.historicalObservations",
  existing_evidence: "knowledgeDomain.existingEvidence",
  knowledge_references: "knowledgeDomain.knowledgeReferences",
  governance: "knowledgeDomain.governance",
  legal_proceedings: "knowledgeDomain.legalProceedings",
  executive_compensation: "knowledgeDomain.executiveCompensation",
};

/** Automatic Investment Case Builder Foundation -- mirrors
 * `atlas.alpha.knowledge_coverage.models.MissingKnowledgeReason`
 * exactly (six members). Presence-only, closed, never free text -- the
 * presentation layer (`describeKnowledgeCoverage.ts`) owns every
 * sentence, the same `EvidenceWarningCode` convention. Renders as
 * plain text under a domain row, never a badge -- no tone map. */
export type MissingKnowledgeReason =
  | "domain_not_yet_wired"
  | "no_source_document_ingested"
  | "insufficient_history"
  | "descriptive_fields_incomplete"
  | "underlying_inputs_missing"
  | "evidence_stale";

export const MISSING_KNOWLEDGE_REASON_KEY: Record<MissingKnowledgeReason, TranslationKey> = {
  domain_not_yet_wired: "missingKnowledgeReason.domainNotYetWired",
  no_source_document_ingested: "missingKnowledgeReason.noSourceDocumentIngested",
  insufficient_history: "missingKnowledgeReason.insufficientHistory",
  descriptive_fields_incomplete: "missingKnowledgeReason.descriptiveFieldsIncomplete",
  underlying_inputs_missing: "missingKnowledgeReason.underlyingInputsMissing",
  evidence_stale: "missingKnowledgeReason.evidenceStale",
};
