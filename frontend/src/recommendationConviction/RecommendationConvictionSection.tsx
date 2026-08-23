import { Heading, Inline, Stack, StatusBadge, Surface, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { STABILITY_KEY, STABILITY_TONE, STRENGTH_KEY, STRENGTH_TONE, reasonLabel } from "./describeRecommendationConviction";
import type { ConvictionChangeView, RecommendationConvictionView } from "./recommendationConvictionApi";

/**
 * Investment Case Integration (Atlas Decision Layer Sprint 2,
 * Deliverable 6). Mirrors `InvestmentDecisionSection`'s own "kompakt,
 * evidence first, progressively disclosed" shape: strength + stability
 * badges always visible, the primary supporting/limiting reason and
 * the strengthening trigger as the compact answer, the full reason
 * lists one click away.
 */
export function RecommendationConvictionSection({
  conviction,
  change,
  t,
}: {
  conviction: RecommendationConvictionView;
  change: ConvictionChangeView | null;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const primarySupportingReason = conviction.supportingReasons[0] ?? null;
  const primaryLimitingReason = conviction.limitingReasons[0] ?? null;

  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Inline gap="row" align="center" wrap>
          <Heading level={3}>{t("recommendationConviction.section.heading")}</Heading>
          <StatusBadge label={t(STRENGTH_KEY[conviction.strength])} tone={STRENGTH_TONE[conviction.strength]} />
          <StatusBadge label={t(STABILITY_KEY[conviction.stability])} tone={STABILITY_TONE[conviction.stability]} />
        </Inline>
        {primarySupportingReason && (
          <Text color="secondary">
            {t("recommendationConviction.section.topSupporting")}: {reasonLabel(primarySupportingReason, t)}
          </Text>
        )}
        {primaryLimitingReason && (
          <Text color="secondary">
            {t("recommendationConviction.section.topLimiting")}: {reasonLabel(primaryLimitingReason, t)}
          </Text>
        )}
        {conviction.strengtheningTrigger && (
          <Text color="secondary">
            {t("recommendationConviction.section.strengthenTrigger")}: {reasonLabel(conviction.strengtheningTrigger, t)}
          </Text>
        )}
        {change && (
          <Text color="tertiary">
            {t("recommendationConviction.change.line", {
              previousStrength: t(STRENGTH_KEY[change.previousStrength]),
              currentStrength: t(STRENGTH_KEY[change.currentStrength]),
            })}
          </Text>
        )}
        {(conviction.limitingReasons.length > 0 || conviction.supportingReasons.length > 0) && (
          <ExpandableDetail summaryLabel={t("recommendationConviction.section.expandLabel")}>
            <Stack gap="metadata">
              {conviction.supportingReasons.map((reason, index) => (
                <Text key={`${reason.source}:${reason.code}:${index}`} color="secondary">
                  {reasonLabel(reason, t)}
                </Text>
              ))}
              {conviction.limitingReasons.map((reason, index) => (
                <Text key={`${reason.source}:${reason.code}:${index}`} color="secondary">
                  {reasonLabel(reason, t)}
                </Text>
              ))}
            </Stack>
          </ExpandableDetail>
        )}
      </Stack>
    </Surface>
  );
}
