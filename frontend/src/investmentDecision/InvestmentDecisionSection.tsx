import { Heading, Inline, Stack, StatusBadge, Surface, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { ACTION_KEY, ACTION_TONE, QUALIFIER_KEY, reasonLabel } from "./describeInvestmentDecision";
import type { DecisionChangeView, InvestmentDecisionView } from "./investmentDecisionApi";

/**
 * Investment Case Integration (Atlas Decision Layer Sprint 1,
 * Deliverable 6). Mirrors `DecisionReadinessSection`'s own "kompakt,
 * evidence first, progressively disclosed" shape: one always-visible
 * action badge plus qualifier badges, the primary supporting reason and
 * primary blocker as the compact Why/Why-not-changed answer, the full
 * reason lists one click away.
 */
export function InvestmentDecisionSection({
  decision,
  change,
  t,
}: {
  decision: InvestmentDecisionView;
  change: DecisionChangeView | null;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const primarySupportingReason = decision.supportingReasons[0] ?? null;
  const primaryBlocker = decision.blockers[0] ?? null;

  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Inline gap="row" align="center" wrap>
          <Heading level={3}>{t("investmentDecision.section.heading")}</Heading>
          <StatusBadge label={t(ACTION_KEY[decision.action])} tone={ACTION_TONE[decision.action]} />
          {decision.qualifiers.map((qualifier) => (
            <StatusBadge key={qualifier.kind} label={t(QUALIFIER_KEY[qualifier.kind])} tone="neutral" />
          ))}
        </Inline>
        {primarySupportingReason && (
          <Text color="secondary">
            {t("investmentDecision.section.whyNow")}: {reasonLabel(primarySupportingReason, t)}
          </Text>
        )}
        {primaryBlocker && (
          <Text color="secondary">
            {t("investmentDecision.section.changeTrigger")}: {reasonLabel(primaryBlocker, t)}
          </Text>
        )}
        {change && (
          <Text color="tertiary">
            {t("investmentDecision.change.line", {
              previous: t(ACTION_KEY[change.previousAction]),
              current: t(ACTION_KEY[change.currentAction]),
            })}
          </Text>
        )}
        {(decision.blockers.length > 0 || decision.supportingReasons.length > 0) && (
          <ExpandableDetail summaryLabel={t("investmentDecision.section.expandLabel")}>
            <Stack gap="metadata">
              {decision.supportingReasons.map((reason, index) => (
                <Text key={`${reason.source}:${reason.code}:${index}`} color="secondary">
                  {reasonLabel(reason, t)}
                </Text>
              ))}
              {decision.blockers.map((blocker, index) => (
                <Text key={`${blocker.source}:${blocker.code}:${index}`} color="secondary">
                  {reasonLabel(blocker, t)}
                </Text>
              ))}
            </Stack>
          </ExpandableDetail>
        )}
      </Stack>
    </Surface>
  );
}
