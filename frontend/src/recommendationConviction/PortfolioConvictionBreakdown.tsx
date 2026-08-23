import { Inline, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import type { PortfolioConvictionBreakdownView } from "./recommendationConvictionApi";

/**
 * Portfolio Integration (Atlas Decision Layer Sprint 2, Deliverable 7).
 * Mirrors `PortfolioReadinessBreakdown`/`PortfolioActionDistribution`'s
 * own shape exactly: reuse the existing Portfolio UI, never introduce
 * a second prioritization system -- one compact summary line, ticker
 * counts grouped by conviction fact only, no re-ranking, no allocation
 * suggestion.
 */
export function PortfolioConvictionBreakdown({
  breakdown,
  t,
}: {
  breakdown: PortfolioConvictionBreakdownView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const total =
    breakdown.highestConviction.length +
    breakdown.lowestConviction.length +
    breakdown.evidenceLimited.length +
    breakdown.operationallyBlocked.length;
  if (total === 0) return null;

  return (
    <Inline gap="row" wrap align="center">
      {breakdown.highestConviction.length > 0 && (
        <Text color="secondary">{t("recommendationConviction.portfolio.highest", { count: breakdown.highestConviction.length })}</Text>
      )}
      {breakdown.lowestConviction.length > 0 && (
        <Text color="secondary">{t("recommendationConviction.portfolio.lowest", { count: breakdown.lowestConviction.length })}</Text>
      )}
      {breakdown.evidenceLimited.length > 0 && (
        <Text color="secondary">
          {t("recommendationConviction.portfolio.evidenceLimited", { count: breakdown.evidenceLimited.length })}
        </Text>
      )}
      {breakdown.operationallyBlocked.length > 0 && (
        <Text color="secondary">
          {t("recommendationConviction.portfolio.operationallyBlocked", { count: breakdown.operationallyBlocked.length })}
        </Text>
      )}
    </Inline>
  );
}
