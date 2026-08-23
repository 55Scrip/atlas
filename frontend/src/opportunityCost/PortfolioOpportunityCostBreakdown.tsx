import { Inline, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import type { PortfolioOpportunityCostBreakdownView } from "./opportunityCostApi";

/**
 * Portfolio Integration (Atlas Decision Layer Sprint 4, Deliverable
 * 7). Mirrors `PortfolioDecisionPathBreakdown`'s own shape exactly:
 * reuse the existing Portfolio UI, never introduce a second
 * prioritization system -- one compact summary line, ticker counts
 * grouped by real trade-off fact only, no re-ranking, no allocation
 * suggestion.
 */
export function PortfolioOpportunityCostBreakdown({
  breakdown,
  t,
}: {
  breakdown: PortfolioOpportunityCostBreakdownView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const total =
    breakdown.holdingsCompetingForCapital.length +
    breakdown.watchlistCompetingWithHoldings.length +
    breakdown.waitingPreferable.length +
    breakdown.noActionAppropriate.length;
  if (total === 0) return null;

  return (
    <Inline gap="row" wrap align="center">
      {breakdown.holdingsCompetingForCapital.length > 0 && (
        <Text color="secondary">
          {t("opportunityCost.portfolio.competingForCapital", { count: breakdown.holdingsCompetingForCapital.length })}
        </Text>
      )}
      {breakdown.watchlistCompetingWithHoldings.length > 0 && (
        <Text color="secondary">
          {t("opportunityCost.portfolio.watchlistCompeting", { count: breakdown.watchlistCompetingWithHoldings.length })}
        </Text>
      )}
      {breakdown.waitingPreferable.length > 0 && (
        <Text color="secondary">{t("opportunityCost.portfolio.waitingPreferable", { count: breakdown.waitingPreferable.length })}</Text>
      )}
      {breakdown.noActionAppropriate.length > 0 && (
        <Text color="secondary">
          {t("opportunityCost.portfolio.noActionAppropriate", { count: breakdown.noActionAppropriate.length })}
        </Text>
      )}
    </Inline>
  );
}
