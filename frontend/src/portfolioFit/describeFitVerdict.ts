import type { TranslationKey } from "../i18n";

type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

/** Sprint 11 Phase 3 -- the closed translation of the Portfolio Fit
 * Engine's own `FitVerdictReasonCode` (Implementation Sprint B1.2's
 * `overallReasoningCode`/`overallReasoningCount`), shared by every
 * consumer of a `PortfolioFitAssessmentView` (Investment Case's own
 * Portfolio Fit section, Portfolio's Today's Risk/Opportunity card,
 * and Daily Brief Agenda's `portfolio_fit_verdict` reason fact) so the
 * same fact never reads differently depending on where it's shown. */
export const PORTFOLIO_FIT_VERDICT_KEY: Record<string, TranslationKey> = {
  no_dimension_evaluated: "portfolioFit.verdictReason.noDimensionEvaluated",
  no_company_level_analysis: "portfolioFit.verdictReason.noCompanyLevelAnalysis",
  risk_gate: "portfolioFit.verdictReason.riskGate",
  multiple_poor: "portfolioFit.verdictReason.multiplePoorOther",
  more_weak_poor_than_good_excellent: "portfolioFit.verdictReason.moreWeakPoorThanGoodExcellent",
  mostly_excellent: "portfolioFit.verdictReason.mostlyExcellent",
  more_good_excellent_than_weak_poor: "portfolioFit.verdictReason.moreGoodExcellentThanWeakPoor",
  mixed: "portfolioFit.verdictReason.mixed",
};

export function describeFitVerdictCode(code: string | null, count: number | null, t: Translate): string | null {
  if (!code) return null;
  const key =
    code === "multiple_poor" && count === 1
      ? "portfolioFit.verdictReason.multiplePoorOne"
      : PORTFOLIO_FIT_VERDICT_KEY[code];
  if (!key) return null;
  return count != null ? t(key, { count }) : t(key);
}

/** The one sentence to show for an assessment's overall verdict --
 * prefers the translated, code-driven sentence over the backend's own
 * pre-rendered English, falling back to that raw text only for an
 * assessment old enough to carry no code at all (defensive; the
 * current contract always populates one whenever `overallReasoning`
 * is non-empty). */
export function describeFitVerdict(
  assessment: {
    overallReasoning: string[];
    overallReasoningCode: string | null;
    overallReasoningCount: number | null;
  },
  t: Translate,
): string | null {
  return (
    describeFitVerdictCode(assessment.overallReasoningCode, assessment.overallReasoningCount, t) ??
    assessment.overallReasoning[0] ??
    null
  );
}
