import { Inline, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import type { PortfolioActionDistributionView } from "./investmentDecisionApi";

/**
 * Portfolio Integration (Atlas Decision Layer Sprint 1, Deliverable 7).
 * Mirrors `PortfolioReadinessBreakdown`'s own shape exactly: reuse the
 * existing Portfolio UI, never introduce a second prioritization
 * system -- one compact summary line, ticker counts grouped by action
 * only, no re-ranking.
 */
export function PortfolioActionDistribution({
  distribution,
  t,
}: {
  distribution: PortfolioActionDistributionView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const total =
    distribution.buy.length +
    distribution.add.length +
    distribution.hold.length +
    distribution.reduce.length +
    distribution.exit.length +
    distribution.wait.length +
    distribution.noDecision.length;
  if (total === 0) return null;

  return (
    <Inline gap="row" wrap align="center">
      {distribution.buy.length > 0 && <Text color="secondary">{t("investmentDecision.portfolio.buy", { count: distribution.buy.length })}</Text>}
      {distribution.add.length > 0 && <Text color="secondary">{t("investmentDecision.portfolio.add", { count: distribution.add.length })}</Text>}
      {distribution.hold.length > 0 && <Text color="secondary">{t("investmentDecision.portfolio.hold", { count: distribution.hold.length })}</Text>}
      {distribution.reduce.length > 0 && (
        <Text color="secondary">{t("investmentDecision.portfolio.reduce", { count: distribution.reduce.length })}</Text>
      )}
      {distribution.exit.length > 0 && <Text color="secondary">{t("investmentDecision.portfolio.exit", { count: distribution.exit.length })}</Text>}
      {distribution.wait.length > 0 && <Text color="secondary">{t("investmentDecision.portfolio.wait", { count: distribution.wait.length })}</Text>}
      {distribution.noDecision.length > 0 && (
        <Text color="secondary">{t("investmentDecision.portfolio.noDecision", { count: distribution.noDecision.length })}</Text>
      )}
    </Inline>
  );
}
