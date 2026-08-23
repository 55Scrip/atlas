import { Heading, Inline, Stack, StatusBadge, Surface, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { BLOCKER_KEY, REASON_KEY, STATUS_KEY, STATUS_TONE, explainReadiness } from "./describeDecisionReadiness";
import type { DecisionReadinessChangeView, DecisionReadinessView } from "./decisionReadinessApi";

/**
 * Investment Case Integration (Atlas Intelligence Sprint 11,
 * Deliverable 6). "Kompakt. Evidence first. Progressively disclosed":
 * one always-visible status badge and explanation sentence, the full
 * blocker/reason lists one click away in `<ExpandableDetail>` -- the
 * same progressive-disclosure primitive `EvidenceGraphSection`
 * (Sprint 10) already uses.
 */
export function DecisionReadinessSection({
  readiness,
  change,
  t,
}: {
  readiness: DecisionReadinessView;
  change: DecisionReadinessChangeView | null;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const primaryBlocker = readiness.blockers[0] ?? null;
  const primaryReason = readiness.supportingReasons[0] ?? null;
  const explanation = explainReadiness(readiness.status, primaryBlocker?.kind ?? null, primaryReason?.kind ?? null, t);

  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Inline gap="row" align="center" wrap>
          <Heading level={3}>{t("decisionReadiness.section.heading")}</Heading>
          <StatusBadge label={t(STATUS_KEY[readiness.status])} tone={STATUS_TONE[readiness.status]} />
        </Inline>
        <Text color="secondary">{explanation}</Text>
        {change && (
          <Text color="tertiary">
            {t("decisionReadiness.change.line", {
              previous: t(STATUS_KEY[change.previousStatus]),
              current: t(STATUS_KEY[change.currentStatus]),
            })}
          </Text>
        )}
        {(readiness.blockers.length > 0 || readiness.supportingReasons.length > 0) && (
          <ExpandableDetail summaryLabel={t("decisionReadiness.section.expandLabel")}>
            <Stack gap="metadata">
              {readiness.blockers.map((blocker) => (
                <Text key={blocker.kind} color="secondary">
                  {t(BLOCKER_KEY[blocker.kind])}
                </Text>
              ))}
              {readiness.supportingReasons.map((reason) => (
                <Text key={reason.kind} color="secondary">
                  {t(REASON_KEY[reason.kind])}
                </Text>
              ))}
            </Stack>
          </ExpandableDetail>
        )}
      </Stack>
    </Surface>
  );
}
