import { Stack, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import type { PortfolioSharedWeakPointsView, SharedWeakPointView } from "./portfolioSharedWeakPointsApi";

/**
 * Portfolio Integration (Atlas Intelligence Sprint 10, Deliverable 7).
 * "Ingen ny ranking. Endast förståelse" -- this renders only real,
 * grouped facts (a shared assumption's own exact text, a shared
 * condition's own exact text, a shared missing evidence kind's own
 * name), never a score or priority order. Renders nothing at all when
 * there is genuinely nothing shared -- an honest absence.
 */
export function PortfolioSharedWeakPointsSection({
  points,
  t,
}: {
  points: PortfolioSharedWeakPointsView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const total =
    points.sharedWeakAssumptions.length + points.sharedConditions.length + points.sharedMissingEvidence.length;
  if (total === 0) return null;

  function line(point: SharedWeakPointView, key: TranslationKey) {
    return t(key, { tickers: point.tickers.join(", "), signature: point.signature });
  }

  return (
    <ExpandableDetail summaryLabel={`${t("evidenceGraph.portfolio.heading")} (${total})`}>
      <Stack gap="metadata">
        {points.sharedWeakAssumptions.map((point) => (
          <Text key={`assumption:${point.signature}`} color="secondary">
            {line(point, "evidenceGraph.portfolio.assumptions")}
          </Text>
        ))}
        {points.sharedConditions.map((point) => (
          <Text key={`condition:${point.signature}`} color="secondary">
            {line(point, "evidenceGraph.portfolio.conditions")}
          </Text>
        ))}
        {points.sharedMissingEvidence.map((point) => (
          <Text key={`missing:${point.signature}`} color="secondary">
            {line(point, "evidenceGraph.portfolio.missingEvidence")}
          </Text>
        ))}
      </Stack>
    </ExpandableDetail>
  );
}
