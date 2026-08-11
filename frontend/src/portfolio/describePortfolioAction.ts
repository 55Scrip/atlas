/**
 * Workspace Migration Phase 4 (Daily Brief) — the enum-to-copy mappings
 * and title/reason text for a `PortfolioAction` (`derivePortfolioActions.ts`),
 * extracted out of `PortfolioPage.tsx`'s `ActionCenterRow` so Daily
 * Brief's "Today's Priorities" section can render the identical
 * severity labels, reason phrasings, and title copy for the same
 * underlying data — the same `statusTone.ts` "one enum-to-copy mapping,
 * not one per consuming page" discipline already applied to Conviction/
 * Risk/Analysis Coverage/Decision Support.
 */
import type { TranslationKey } from "../i18n";
import type { ActionSeverity, AttentionCategory, PortfolioAction } from "./derivePortfolioActions";

export const ACTION_CENTER_REASON_KEY: Record<AttentionCategory, TranslationKey> = {
  MISSING_CASE: "portfolio.actionCenter.reason.missingCase",
  DECISION_WITHOUT_OUTCOME: "portfolio.actionCenter.reason.decisionWithoutOutcome",
  OUTCOME_WITHOUT_EXECUTION: "portfolio.actionCenter.reason.outcomeWithoutExecution",
  AWAITING_RECONCILIATION: "portfolio.actionCenter.reason.awaitingReconciliation",
  VERY_OLD_CASE: "portfolio.actionCenter.reason.veryOldCase",
  OBSERVATION_WITHOUT_DECISION: "portfolio.actionCenter.reason.observationWithoutDecision",
};

export const SEVERITY_EMOJI: Record<ActionSeverity, string> = { highest: "🔴", high: "🟠", medium: "🟡" };
export const SEVERITY_LABEL_KEY: Record<ActionSeverity, TranslationKey> = {
  highest: "portfolio.actionCenter.severity.highest",
  high: "portfolio.actionCenter.severity.high",
  medium: "portfolio.actionCenter.severity.medium",
};

/** Reuses `portfolio.intelligence.keyFindings.*` for concentration
 * findings (the same translation `PortfolioPage.tsx`'s Key Findings
 * section already uses) rather than a second copy of that text. */
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
        title: t("portfolio.actionCenter.reviewTitle", { ticker: action.ticker ?? "" }),
        reason: t(ACTION_CENTER_REASON_KEY[action.reasonCategory!], { days: action.ageDays ?? 0 }),
      };
    case "evidence":
      return {
        title: t("portfolio.actionCenter.completeEvidenceTitle", { ticker: action.ticker ?? "" }),
        reason: t("portfolio.actionCenter.evidenceReason"),
      };
    case "concentration":
      return {
        title: t("portfolio.actionCenter.concentrationTitle", { ticker: action.ticker ?? "" }),
        reason: t(CONCENTRATION_FINDING_KEY[action.concentrationFindingKind!], { tickers: action.ticker ?? "" }),
      };
    case "allocation":
      return {
        title: t("portfolio.actionCenter.allocationTitle"),
        reason: t("portfolio.actionCenter.allocationReason", { percent: action.unallocatedPercent ?? 0 }),
      };
  }
}
