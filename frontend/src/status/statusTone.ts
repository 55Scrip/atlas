import type { TranslationKey } from "../i18n";
import type { StatusTone } from "../foundation";
import type {
  AnalysisBusinessStatus,
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
