import { Heading, Inline, Stack, StatusBadge, Surface, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { ALTERNATIVE_KIND_KEY, alternativeReasonLabel } from "./describeOpportunityCost";
import type { DecisionTradeoffView, OpportunityCostChangeView, OpportunityCostView } from "./opportunityCostApi";

/**
 * Investment Case Integration (Atlas Decision Layer Sprint 4,
 * Deliverable 6). Mirrors `DecisionPathSection`'s own "kompakt,
 * evidence first, progressively disclosed" shape: every real
 * alternative shown as a compact row (kind, ticker when one exists,
 * the real reason it exists), a fixed disclosure that Atlas never
 * chooses between them, and the full pairwise comparison one click
 * away.
 */
export function OpportunityCostSection({
  opportunityCost,
  currentTicker,
  change,
  t,
}: {
  opportunityCost: OpportunityCostView;
  currentTicker: string;
  change: OpportunityCostChangeView | null;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  if (opportunityCost.tradeoffs.length === 0) return null;

  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Heading level={3}>{t("opportunityCost.section.heading")}</Heading>
        <Stack gap="metadata">
          {opportunityCost.tradeoffs.map((tradeoff, index) => (
            <Inline key={`${tradeoff.alternative.kind}:${tradeoff.alternative.caseId ?? index}`} gap="row" align="center" wrap>
              <StatusBadge label={t(ALTERNATIVE_KIND_KEY[tradeoff.alternative.kind])} tone="neutral" />
              {tradeoff.alternative.ticker && (
                <Text as="span" style={{ fontWeight: 600 }}>
                  {tradeoff.alternative.ticker}
                </Text>
              )}
              <Text color="secondary">{alternativeReasonLabel(tradeoff.alternative.reason, t)}</Text>
            </Inline>
          ))}
        </Stack>
        <Text color="tertiary">{t("opportunityCost.section.whyCannotChoose")}</Text>
        {change && <Text color="tertiary">{t("opportunityCost.change.line")}</Text>}
        {opportunityCost.tradeoffs.some((t) => t.comparison !== null) && (
          <ExpandableDetail summaryLabel={t("opportunityCost.section.expandLabel")}>
            <Stack gap="metadata">
              {opportunityCost.tradeoffs.map((tradeoff, index) =>
                tradeoff.comparison ? (
                  <TradeoffComparisonRow
                    key={`${tradeoff.alternative.kind}:${tradeoff.alternative.caseId ?? index}`}
                    tradeoff={tradeoff}
                    currentTicker={currentTicker}
                    t={t}
                  />
                ) : null,
              )}
            </Stack>
          </ExpandableDetail>
        )}
      </Stack>
    </Surface>
  );
}

function TradeoffComparisonRow({
  tradeoff,
  currentTicker,
  t,
}: {
  tradeoff: DecisionTradeoffView;
  currentTicker: string;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const comparison = tradeoff.comparison;
  if (!comparison) return null;
  const alternativeTicker = tradeoff.alternative.ticker ?? "";
  const currentCaseId = comparison.conviction.a.caseId;
  const tickerFor = (caseId: string) => (caseId === currentCaseId ? currentTicker : alternativeTicker);

  return (
    <Stack gap="metadata">
      <Text as="span" style={{ fontWeight: 600 }}>
        {alternativeTicker}
      </Text>
      <Text color="secondary">
        {comparison.conviction.strongerCaseId
          ? t("opportunityCost.compare.strongerConviction", { ticker: tickerFor(comparison.conviction.strongerCaseId) })
          : t("opportunityCost.compare.strongerConvictionTie")}
      </Text>
      <Text color="secondary">
        {comparison.path.shorterPathCaseId
          ? t("opportunityCost.compare.shorterPath", { ticker: tickerFor(comparison.path.shorterPathCaseId) })
          : t("opportunityCost.compare.shorterPathTie")}
      </Text>
      <Text color="secondary">
        {comparison.moreDependencyBlockedCaseId
          ? t("opportunityCost.compare.moreDependencyBlocked", { ticker: tickerFor(comparison.moreDependencyBlockedCaseId) })
          : t("opportunityCost.compare.dependencyTie")}
      </Text>
    </Stack>
  );
}
