import type { TranslationKey } from "../i18n";

/**
 * Shared, pure presentation logic over Investment Case Change
 * Intelligence's `ChangeFinding`s -- extracted from
 * `InvestmentCasePage.tsx`'s own "What Changed" section (Investment
 * Case Monitoring & Change Intelligence v1) so History v1 can render
 * the exact same change vocabulary (labels, verbs, symbols, thesis
 * impact language) without a second, drifting copy of this mapping
 * table. Every type/const/function here mirrors
 * `atlas/analysis_engine/investment_case_change.py`'s own closed enums
 * 1:1 -- nothing here invents a new category, status, or interpretation;
 * this module only chooses which already-established translation key
 * a given enum value maps to.
 */

export type AnalysisRiskCategory = "business_risk" | "financial_risk" | "valuation_risk" | "thesis_risk";
export type AnalysisRiskStatus = "not_evaluated" | "insufficient_input" | "low" | "moderate" | "high";
export type AnalysisBusinessCategory =
  | "business_model"
  | "competitive_position"
  | "management"
  | "capital_allocation"
  | "growth"
  | "durability";
export type AnalysisBusinessStatus = "not_evaluated" | "insufficient_input" | "weak" | "moderate" | "strong";
export type AnalysisHighlightKind =
  | "growth"
  | "capital_allocation"
  | "valuation"
  | "business_risk"
  | "financial_risk"
  | "valuation_risk";
export type AnalysisChangeCategory =
  | "growth_changed"
  | "capital_allocation_changed"
  | "business_quality_changed"
  | "business_risk_changed"
  | "financial_risk_changed"
  | "valuation_risk_changed"
  | "valuation_changed"
  | "strength_added"
  | "strength_removed"
  | "risk_added"
  | "risk_removed"
  | "open_question_added"
  | "open_question_resolved"
  | "analytical_coverage_changed";
export type AnalysisChangeDirection = "positive" | "negative" | "neutral";
export type AnalysisThesisImpact = "strengthened" | "weakened" | "mixed" | "unchanged";
export type AnalysisValuationStatus = "not_evaluated" | "insufficient_input" | "undervalued" | "fairly_valued" | "expensive";
export type AnalysisOpenQuestionOrigin =
  | "growth_inconclusive"
  | "growth_mixed"
  | "capital_allocation_inconclusive"
  | "capital_allocation_weak"
  | "valuation_inconclusive"
  | "valuation_expensive_versus_growth"
  | "scenario_valuation_unavailable";

export interface ChangeFindingView {
  id: string;
  category: AnalysisChangeCategory;
  direction: AnalysisChangeDirection;
  previousState: string;
  currentState: string;
  details: Record<string, string>;
  evidenceReferences: string[];
  sourceFindingId: string | null;
}

export type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

export const RISK_STATUS_KEY: Record<AnalysisRiskStatus, TranslationKey> = {
  not_evaluated: "portfolio.cockpit.risk.status.not_evaluated",
  insufficient_input: "portfolio.cockpit.risk.status.insufficient_input",
  low: "portfolio.cockpit.risk.status.low",
  moderate: "portfolio.cockpit.risk.status.moderate",
  high: "portfolio.cockpit.risk.status.high",
};

export const RISK_CATEGORY_KEY: Record<AnalysisRiskCategory, TranslationKey> = {
  business_risk: "portfolio.cockpit.risk.category.business_risk",
  financial_risk: "portfolio.cockpit.risk.category.financial_risk",
  valuation_risk: "portfolio.cockpit.risk.category.valuation_risk",
  thesis_risk: "portfolio.cockpit.risk.category.thesis_risk",
};

export const BUSINESS_STATUS_KEY: Record<AnalysisBusinessStatus, TranslationKey> = {
  not_evaluated: "portfolio.cockpit.business.not_evaluated",
  insufficient_input: "portfolio.cockpit.business.insufficient_input",
  weak: "portfolio.cockpit.business.weak",
  moderate: "portfolio.cockpit.business.moderate",
  strong: "portfolio.cockpit.business.strong",
};

export const BUSINESS_CATEGORY_KEY: Record<AnalysisBusinessCategory, TranslationKey> = {
  business_model: "investmentCase.analysis.business.category.business_model",
  competitive_position: "investmentCase.analysis.business.category.competitive_position",
  management: "investmentCase.analysis.business.category.management",
  capital_allocation: "investmentCase.analysis.business.category.capital_allocation",
  growth: "investmentCase.analysis.business.category.growth",
  durability: "investmentCase.analysis.business.category.durability",
};

export const HIGHLIGHT_KIND_KEY: Record<AnalysisHighlightKind, TranslationKey> = {
  growth: "investmentCase.analysis.business.category.growth",
  capital_allocation: "investmentCase.analysis.business.category.capital_allocation",
  valuation: "investmentCase.atlasView.highlight.valuation",
  business_risk: "portfolio.cockpit.risk.category.business_risk",
  financial_risk: "portfolio.cockpit.risk.category.financial_risk",
  valuation_risk: "portfolio.cockpit.risk.category.valuation_risk",
};

export const CHANGE_DIRECTION_SYMBOL: Record<AnalysisChangeDirection, string> = {
  positive: "↑",
  negative: "↓",
  neutral: "•",
};

export const THESIS_IMPACT_KEY: Record<AnalysisThesisImpact, TranslationKey> = {
  strengthened: "investmentCase.whatChanged.thesisImpact.strengthened",
  weakened: "investmentCase.whatChanged.thesisImpact.weakened",
  mixed: "investmentCase.whatChanged.thesisImpact.mixed",
  unchanged: "investmentCase.whatChanged.thesisImpact.unchanged",
};

export const VALUATION_STATUS_KEY: Record<AnalysisValuationStatus, TranslationKey> = {
  not_evaluated: "portfolio.cockpit.valuation.not_evaluated",
  insufficient_input: "portfolio.cockpit.valuation.insufficient_input",
  undervalued: "portfolio.cockpit.valuation.undervalued",
  fairly_valued: "portfolio.cockpit.valuation.fairly_valued",
  expensive: "portfolio.cockpit.valuation.expensive",
};

export const OPEN_QUESTION_ORIGIN_KEY: Record<AnalysisOpenQuestionOrigin, TranslationKey> = {
  growth_inconclusive: "investmentCase.atlasView.openQuestions.growth_inconclusive",
  growth_mixed: "investmentCase.atlasView.openQuestions.growth_mixed",
  capital_allocation_inconclusive: "investmentCase.atlasView.openQuestions.capital_allocation_inconclusive",
  capital_allocation_weak: "investmentCase.atlasView.openQuestions.capital_allocation_weak",
  valuation_inconclusive: "investmentCase.atlasView.openQuestions.valuation_inconclusive",
  valuation_expensive_versus_growth: "investmentCase.atlasView.openQuestions.valuation_expensive_versus_growth",
  scenario_valuation_unavailable: "investmentCase.atlasView.openQuestions.scenario_valuation_unavailable",
};

/** Canonical enum values not worth a dedicated translation entry each
 * are shown as their own raw value with underscores turned into spaces
 * -- still specific and honest, never a vague catch-all phrase. */
export function humanize(rawValue: string): string {
  return rawValue.replace(/_/g, " ");
}

/** Which dimension a change is about, in already-established page
 * vocabulary -- reuses BUSINESS_CATEGORY_KEY/RISK_CATEGORY_KEY/the
 * existing FCF-yield label, never a second, parallel label set. */
export function dimensionLabel(dimension: string | undefined, t: Translate): string {
  if (!dimension) return "";
  if (dimension in BUSINESS_CATEGORY_KEY) {
    return t(BUSINESS_CATEGORY_KEY[dimension as AnalysisBusinessCategory]);
  }
  if (dimension in RISK_CATEGORY_KEY) {
    return t(RISK_CATEGORY_KEY[dimension as AnalysisRiskCategory]);
  }
  if (dimension === "fcf_yield_relative") {
    return t("investmentCase.analysis.valuation.method.fcf_yield_relative");
  }
  return humanize(dimension);
}

export function describeChange(change: ChangeFindingView, t: Translate): string {
  const dimension = change.details.dimension;

  if (change.category === "analytical_coverage_changed") {
    const label = dimensionLabel(dimension, t);
    if (change.currentState === "insufficient_input" || change.currentState === "not_evaluated") {
      return t("investmentCase.whatChanged.change.coverageLost", { dimension: label });
    }
    return t("investmentCase.whatChanged.change.coverageGained", { dimension: label });
  }

  if (
    change.category === "growth_changed" ||
    change.category === "capital_allocation_changed" ||
    change.category === "business_quality_changed"
  ) {
    const label = dimensionLabel(dimension, t);
    const verbKey =
      change.direction === "positive" ? "investmentCase.whatChanged.verb.improved" : "investmentCase.whatChanged.verb.weakened";
    const previous = t(BUSINESS_STATUS_KEY[change.previousState as AnalysisBusinessStatus]);
    const current = t(BUSINESS_STATUS_KEY[change.currentState as AnalysisBusinessStatus]);
    return t("investmentCase.whatChanged.change.dimensionChanged", {
      dimension: label,
      verb: t(verbKey),
      previous,
      current,
    });
  }

  if (
    change.category === "business_risk_changed" ||
    change.category === "financial_risk_changed" ||
    change.category === "valuation_risk_changed"
  ) {
    const label = dimensionLabel(dimension, t);
    const verbKey =
      change.direction === "positive" ? "investmentCase.whatChanged.verb.decreased" : "investmentCase.whatChanged.verb.increased";
    const previous = t(RISK_STATUS_KEY[change.previousState as AnalysisRiskStatus]);
    const current = t(RISK_STATUS_KEY[change.currentState as AnalysisRiskStatus]);
    return t("investmentCase.whatChanged.change.dimensionChanged", {
      dimension: label,
      verb: t(verbKey),
      previous,
      current,
    });
  }

  if (change.category === "valuation_changed") {
    const verbKey =
      change.direction === "positive"
        ? "investmentCase.whatChanged.verb.moreAttractive"
        : "investmentCase.whatChanged.verb.lessAttractive";
    return t("investmentCase.whatChanged.change.valuationChanged", { verb: t(verbKey) });
  }

  if (change.category === "strength_added" || change.category === "risk_added") {
    const label = t(HIGHLIGHT_KIND_KEY[change.currentState as AnalysisHighlightKind]);
    const key =
      change.category === "strength_added"
        ? "investmentCase.whatChanged.change.strengthAdded"
        : "investmentCase.whatChanged.change.riskAdded";
    return t(key, { label });
  }

  if (change.category === "strength_removed" || change.category === "risk_removed") {
    const label = t(HIGHLIGHT_KIND_KEY[change.previousState as AnalysisHighlightKind]);
    const key =
      change.category === "strength_removed"
        ? "investmentCase.whatChanged.change.strengthRemoved"
        : "investmentCase.whatChanged.change.riskRemoved";
    return t(key, { label });
  }

  if (change.category === "open_question_added") {
    return t("investmentCase.whatChanged.change.openQuestionAdded");
  }
  if (change.category === "open_question_resolved") {
    return t("investmentCase.whatChanged.change.openQuestionResolved");
  }
  return "";
}
