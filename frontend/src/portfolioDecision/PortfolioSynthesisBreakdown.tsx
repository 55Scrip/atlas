import { Inline, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import type { PortfolioSynthesisBreakdownView } from "./portfolioDecisionApi";

/**
 * Portfolio Integration (Atlas Decision Layer Sprint 8, Deliverable
 * 8). Mirrors `PortfolioReliabilityBreakdown`'s own shape exactly:
 * reuse the existing Portfolio UI, never introduce a second
 * prioritization system -- one compact summary line, ticker counts
 * grouped by real portfolio-decision fact only, no re-ranking, never
 * a re-ordering of holdings themselves.
 */
export function PortfolioSynthesisBreakdown({
  breakdown,
  t,
}: {
  breakdown: PortfolioSynthesisBreakdownView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const total =
    breakdown.supportsPortfolio.length + breakdown.highestCapitalCompetition.length + breakdown.conflictsWithPortfolio.length + breakdown.neutral.length;
  if (total === 0) return null;

  return (
    <Inline gap="row" wrap align="center">
      {breakdown.supportsPortfolio.length > 0 && (
        <Text color="secondary">{t("portfolioDecision.portfolio.supportsPortfolio", { count: breakdown.supportsPortfolio.length })}</Text>
      )}
      {breakdown.highestCapitalCompetition.length > 0 && (
        <Text color="secondary">
          {t("portfolioDecision.portfolio.highestCapitalCompetition", { count: breakdown.highestCapitalCompetition.length })}
        </Text>
      )}
      {breakdown.conflictsWithPortfolio.length > 0 && (
        <Text color="secondary">{t("portfolioDecision.portfolio.conflictsWithPortfolio", { count: breakdown.conflictsWithPortfolio.length })}</Text>
      )}
      {breakdown.neutral.length > 0 && (
        <Text color="secondary">{t("portfolioDecision.portfolio.neutral", { count: breakdown.neutral.length })}</Text>
      )}
    </Inline>
  );
}
