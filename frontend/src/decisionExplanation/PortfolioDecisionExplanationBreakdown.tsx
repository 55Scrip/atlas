import { Inline, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import type { PortfolioDecisionExplanationBreakdownView } from "./decisionExplanationApi";

/**
 * Portfolio Integration (Atlas Decision Layer Sprint 6, Deliverable
 * 7). Mirrors `PortfolioDecisionMemoryBreakdown`'s own shape exactly:
 * reuse the existing Portfolio UI, never introduce a second
 * prioritization system -- one compact summary line, ticker counts
 * grouped by real explanation-change fact only, no re-ranking.
 */
export function PortfolioDecisionExplanationBreakdown({
  breakdown,
  t,
}: {
  breakdown: PortfolioDecisionExplanationBreakdownView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const total =
    breakdown.recentlyChanged.length +
    breakdown.newSupportingFindings.length +
    breakdown.resolvedBlockers.length +
    breakdown.recentlyStrengthened.length;
  if (total === 0) return null;

  return (
    <Inline gap="row" wrap align="center">
      {breakdown.recentlyChanged.length > 0 && (
        <Text color="secondary">{t("decisionExplanation.portfolio.recentlyChanged", { count: breakdown.recentlyChanged.length })}</Text>
      )}
      {breakdown.newSupportingFindings.length > 0 && (
        <Text color="secondary">
          {t("decisionExplanation.portfolio.newSupportingFindings", { count: breakdown.newSupportingFindings.length })}
        </Text>
      )}
      {breakdown.resolvedBlockers.length > 0 && (
        <Text color="secondary">{t("decisionExplanation.portfolio.resolvedBlockers", { count: breakdown.resolvedBlockers.length })}</Text>
      )}
      {breakdown.recentlyStrengthened.length > 0 && (
        <Text color="secondary">
          {t("decisionExplanation.portfolio.recentlyStrengthened", { count: breakdown.recentlyStrengthened.length })}
        </Text>
      )}
    </Inline>
  );
}
