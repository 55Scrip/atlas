import { Inline, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import type { PortfolioDecisionMemoryBreakdownView } from "./decisionMemoryApi";

/**
 * Portfolio Integration (Atlas Decision Layer Sprint 5, Deliverable
 * 7). Mirrors `PortfolioOpportunityCostBreakdown`'s own shape exactly:
 * reuse the existing Portfolio UI, never introduce a second
 * prioritization system -- one compact summary line, ticker counts
 * grouped by real recorded-history fact only, no re-ranking.
 */
export function PortfolioDecisionMemoryBreakdown({
  breakdown,
  t,
}: {
  breakdown: PortfolioDecisionMemoryBreakdownView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const total =
    breakdown.recentlyChanged.length + breakdown.stable.length + breakdown.recentlyStrengthened.length + breakdown.recentlyWeakened.length;
  if (total === 0) return null;

  return (
    <Inline gap="row" wrap align="center">
      {breakdown.recentlyChanged.length > 0 && (
        <Text color="secondary">{t("decisionMemory.portfolio.recentlyChanged", { count: breakdown.recentlyChanged.length })}</Text>
      )}
      {breakdown.stable.length > 0 && <Text color="secondary">{t("decisionMemory.portfolio.stable", { count: breakdown.stable.length })}</Text>}
      {breakdown.recentlyStrengthened.length > 0 && (
        <Text color="secondary">
          {t("decisionMemory.portfolio.recentlyStrengthened", { count: breakdown.recentlyStrengthened.length })}
        </Text>
      )}
      {breakdown.recentlyWeakened.length > 0 && (
        <Text color="secondary">{t("decisionMemory.portfolio.recentlyWeakened", { count: breakdown.recentlyWeakened.length })}</Text>
      )}
    </Inline>
  );
}
