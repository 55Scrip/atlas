/**
 * Figma-fidelity rebuild — the enum-to-copy mappings and title/reason
 * text for a `PortfolioAction` (`derivePortfolioActions.ts`), shared by
 * Portfolio's dense priority strip and Daily Brief's "Today's
 * Priorities" section so both render identical phrasing and title copy
 * for the same underlying data — the same `statusTone.ts` "one enum-to-
 * copy mapping, not one per consuming page" discipline already applied
 * to Conviction/Risk/Analysis Coverage/Decision Support. No severity-
 * tier group labels here: neither Figma screen groups actions under a
 * "Highest/High/Medium Priority" heading, both show a flat, ordered
 * list, so that presentation is gone rather than migrated.
 */
import type { TranslationKey } from "../i18n";
import type { ActionSeverity, AttentionCategory, PortfolioAction } from "./derivePortfolioActions";

export const ACTION_REASON_KEY: Record<AttentionCategory, TranslationKey> = {
  MISSING_CASE: "portfolio.priorityStrip.reason.missingCase",
  DECISION_WITHOUT_OUTCOME: "portfolio.priorityStrip.reason.decisionWithoutOutcome",
  OUTCOME_WITHOUT_EXECUTION: "portfolio.priorityStrip.reason.outcomeWithoutExecution",
  AWAITING_RECONCILIATION: "portfolio.priorityStrip.reason.awaitingReconciliation",
  VERY_OLD_CASE: "portfolio.priorityStrip.reason.veryOldCase",
  OBSERVATION_WITHOUT_DECISION: "portfolio.priorityStrip.reason.observationWithoutDecision",
};

export const SEVERITY_EMOJI: Record<ActionSeverity, string> = { highest: "🔴", high: "🟠", medium: "🟡" };

/** Reuses `portfolio.intelligence.keyFindings.*` for concentration
 * findings (the same translation the Key Findings panel already uses)
 * rather than a second copy of that text. */
const CONCENTRATION_FINDING_KEY: Record<"high_concentration" | "elevated_concentration", TranslationKey> = {
  high_concentration: "portfolio.intelligence.keyFindings.high_concentration",
  elevated_concentration: "portfolio.intelligence.keyFindings.elevated_concentration",
};

export function describePortfolioAction(
  action: PortfolioAction,
  t: (key: TranslationKey, params?: Record<string, string | number>) => string,
): { title: string; reason: string } {
  switch (action.kind) {
    case "workflow":
      return {
        title: t("portfolio.priorityStrip.reviewTitle", { ticker: action.ticker ?? "" }),
        reason: t(ACTION_REASON_KEY[action.reasonCategory!], { days: action.ageDays ?? 0 }),
      };
    case "evidence":
      return {
        title: t("portfolio.priorityStrip.completeEvidenceTitle", { ticker: action.ticker ?? "" }),
        reason: t("portfolio.priorityStrip.evidenceReason"),
      };
    case "concentration":
      return {
        title: t("portfolio.priorityStrip.concentrationTitle", { ticker: action.ticker ?? "" }),
        reason: t(CONCENTRATION_FINDING_KEY[action.concentrationFindingKind!], { tickers: action.ticker ?? "" }),
      };
    case "allocation":
      return {
        title: t("portfolio.priorityStrip.allocationTitle"),
        reason: t("portfolio.priorityStrip.allocationReason", { percent: action.unallocatedPercent ?? 0 }),
      };
  }
}
