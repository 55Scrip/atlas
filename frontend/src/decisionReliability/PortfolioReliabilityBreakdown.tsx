import { Inline, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import type { PortfolioReliabilityBreakdownView } from "./decisionReliabilityApi";

/**
 * Portfolio Integration (Atlas Decision Layer Sprint 7, Deliverable
 * 8). Mirrors `PortfolioDecisionExplanationBreakdown`'s own shape
 * exactly: reuse the existing Portfolio UI, never introduce a second
 * prioritization system -- one compact summary line, ticker counts
 * grouped by real reliability fact only, no re-ranking.
 */
export function PortfolioReliabilityBreakdown({
  breakdown,
  t,
}: {
  breakdown: PortfolioReliabilityBreakdownView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const total =
    breakdown.mostReliable.length + breakdown.leastReliable.length + breakdown.recentlyImproved.length + breakdown.recentlyWeakened.length;
  if (total === 0) return null;

  return (
    <Inline gap="row" wrap align="center">
      {breakdown.mostReliable.length > 0 && (
        <Text color="secondary">{t("decisionReliability.portfolio.mostReliable", { count: breakdown.mostReliable.length })}</Text>
      )}
      {breakdown.leastReliable.length > 0 && (
        <Text color="secondary">{t("decisionReliability.portfolio.leastReliable", { count: breakdown.leastReliable.length })}</Text>
      )}
      {breakdown.recentlyImproved.length > 0 && (
        <Text color="secondary">{t("decisionReliability.portfolio.recentlyImproved", { count: breakdown.recentlyImproved.length })}</Text>
      )}
      {breakdown.recentlyWeakened.length > 0 && (
        <Text color="secondary">{t("decisionReliability.portfolio.recentlyWeakened", { count: breakdown.recentlyWeakened.length })}</Text>
      )}
    </Inline>
  );
}
