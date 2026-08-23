import { Inline, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import type { PortfolioDecisionPathBreakdownView } from "./decisionPathApi";

/**
 * Portfolio Integration (Atlas Decision Layer Sprint 3, Deliverable
 * 7). Mirrors `PortfolioConvictionBreakdown`/`PortfolioActionDistribution`'s
 * own shape exactly: reuse the existing Portfolio UI, never introduce
 * a second prioritization system -- one compact summary line, ticker
 * counts grouped by real dependency fact only, no re-ranking, no
 * allocation suggestion.
 */
export function PortfolioDecisionPathBreakdown({
  breakdown,
  t,
}: {
  breakdown: PortfolioDecisionPathBreakdownView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const total =
    breakdown.closestToInvestable.length +
    breakdown.operationallyBlocked.length +
    breakdown.requiringMoreEvidence.length +
    breakdown.requiringDependencyResolution.length;
  if (total === 0) return null;

  return (
    <Inline gap="row" wrap align="center">
      {breakdown.closestToInvestable.length > 0 && (
        <Text color="secondary">
          {t("decisionPath.portfolio.closestToInvestable", { count: breakdown.closestToInvestable.length })}
        </Text>
      )}
      {breakdown.operationallyBlocked.length > 0 && (
        <Text color="secondary">
          {t("decisionPath.portfolio.operationallyBlocked", { count: breakdown.operationallyBlocked.length })}
        </Text>
      )}
      {breakdown.requiringMoreEvidence.length > 0 && (
        <Text color="secondary">
          {t("decisionPath.portfolio.requiringMoreEvidence", { count: breakdown.requiringMoreEvidence.length })}
        </Text>
      )}
      {breakdown.requiringDependencyResolution.length > 0 && (
        <Text color="secondary">
          {t("decisionPath.portfolio.requiringDependencyResolution", {
            count: breakdown.requiringDependencyResolution.length,
          })}
        </Text>
      )}
    </Inline>
  );
}
