import { Inline, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import type { PortfolioReadinessBreakdownView } from "./decisionReadinessApi";

/**
 * Portfolio Integration (Atlas Intelligence Sprint 11, Deliverable 7).
 * "Reuse existing Portfolio UI. Never create a second prioritization
 * system": one compact summary line, ticker lists grouped by status
 * only -- no re-ranking, no new "what matters most" surface alongside
 * Portfolio's own existing Agenda/Attention sections.
 */
export function PortfolioReadinessBreakdown({
  breakdown,
  t,
}: {
  breakdown: PortfolioReadinessBreakdownView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const total =
    breakdown.ready.length +
    breakdown.almostReady.length +
    breakdown.waiting.length +
    breakdown.blocked.length +
    breakdown.unavailable.length;
  if (total === 0) return null;

  return (
    <Inline gap="row" wrap align="center">
      {breakdown.ready.length > 0 && <Text color="secondary">{t("decisionReadiness.portfolio.ready", { count: breakdown.ready.length })}</Text>}
      {breakdown.almostReady.length > 0 && (
        <Text color="secondary">{t("decisionReadiness.portfolio.almostReady", { count: breakdown.almostReady.length })}</Text>
      )}
      {breakdown.waiting.length > 0 && (
        <Text color="secondary">{t("decisionReadiness.portfolio.waiting", { count: breakdown.waiting.length })}</Text>
      )}
      {breakdown.blocked.length > 0 && (
        <Text color="secondary">{t("decisionReadiness.portfolio.blocked", { count: breakdown.blocked.length })}</Text>
      )}
      {breakdown.unavailable.length > 0 && (
        <Text color="secondary">{t("decisionReadiness.portfolio.unavailable", { count: breakdown.unavailable.length })}</Text>
      )}
    </Inline>
  );
}
