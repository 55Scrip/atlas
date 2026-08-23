import { Heading, Inline, Stack, StatusBadge, Surface, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { LEVEL_KEY, LEVEL_TONE, SOURCE_KEY, reliabilityReasonLabel } from "./describeDecisionReliability";
import type { DecisionReliabilityView, ReliabilityReasonView } from "./decisionReliabilityApi";

/**
 * Investment Case Integration (Atlas Decision Layer Sprint 7,
 * Deliverable 7). Reliability level, why, supporting/limiting
 * reasons -- progressively disclosed: the level and primary
 * limitation always visible, the full breakdown one click away. Every
 * reason renders through `reliabilityReasonLabel` (never a raw
 * technical code as prose) and carries its own `source` tag, so a
 * reader can always see which real Atlas judgment it came from.
 */
export function DecisionReliabilitySection({
  reliability,
  t,
}: {
  reliability: DecisionReliabilityView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const hasMore = reliability.supportingReasons.length > 0 || reliability.limitingReasons.length > 0;

  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Heading level={3}>{t("decisionReliability.section.heading")}</Heading>
        <StatusBadge label={t(LEVEL_KEY[reliability.level])} tone={LEVEL_TONE[reliability.level]} />
        {reliability.primaryLimitingReason ? (
          <Text color="secondary">
            {t("decisionReliability.section.primaryLimiting", { fact: reliabilityReasonLabel(reliability.primaryLimitingReason, t) })}
          </Text>
        ) : (
          <Text color="tertiary">{t("decisionReliability.section.noLimiting")}</Text>
        )}
        {hasMore && (
          <ExpandableDetail summaryLabel={t("decisionReliability.section.expandLabel")}>
            <Stack gap="intra-section">
              <ReasonList heading={t("decisionReliability.section.supportingHeading")} reasons={reliability.supportingReasons} t={t} />
              <ReasonList heading={t("decisionReliability.section.limitingHeading")} reasons={reliability.limitingReasons} t={t} />
            </Stack>
          </ExpandableDetail>
        )}
      </Stack>
    </Surface>
  );
}

function ReasonList({
  heading,
  reasons,
  t,
}: {
  heading: string;
  reasons: ReliabilityReasonView[];
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  if (reasons.length === 0) return null;
  return (
    <Stack gap="metadata">
      <Text as="span" style={{ fontWeight: 600 }}>
        {heading}
      </Text>
      {reasons.map((reason, index) => (
        <Inline key={`${reason.source}:${reason.reference.id}:${index}`} gap="row" align="center" wrap>
          <Text color="secondary">{reliabilityReasonLabel(reason, t)}</Text>
          <Text color="tertiary" as="span">
            {t(SOURCE_KEY[reason.source])}
          </Text>
        </Inline>
      ))}
    </Stack>
  );
}
