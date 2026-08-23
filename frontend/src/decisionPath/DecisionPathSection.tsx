import { Heading, Inline, Stack, StatusBadge, Surface, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import {
  FINAL_STATE_KEY,
  FINAL_STATE_TONE,
  PROGRESS_KIND_KEY,
  REACHABILITY_KEY,
  REACHABILITY_TONE,
  stepLabel,
} from "./describeDecisionPath";
import type { DecisionPathChangeView, DecisionPathView } from "./decisionPathApi";

/**
 * Investment Case Integration (Atlas Decision Layer Sprint 3,
 * Deliverable 6). Mirrors `RecommendationConvictionSection`'s own
 * "kompakt, evidence first, progressively disclosed" shape: the
 * current endpoint badge always visible, the immediate blocker and
 * next achievable improvement as the compact answer, the full step
 * list (with each step's own progress kind and reachability) one
 * click away.
 */
export function DecisionPathSection({
  path,
  change,
  t,
}: {
  path: DecisionPathView;
  change: DecisionPathChangeView | null;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Inline gap="row" align="center" wrap>
          <Heading level={3}>{t("decisionPath.section.heading")}</Heading>
        </Inline>
        <Inline gap="row" align="center" wrap>
          <Text color="secondary" as="span">
            {t("decisionPath.section.currentEndpoint")}:
          </Text>
          <StatusBadge label={t(FINAL_STATE_KEY[path.finalReachableState])} tone={FINAL_STATE_TONE[path.finalReachableState]} />
        </Inline>
        {path.immediateBlocker && (
          <Text color="secondary">
            {t("decisionPath.section.immediateBlocker")}: {stepLabel(path.immediateBlocker, t)} (
            {t(PROGRESS_KIND_KEY[path.immediateBlocker.progressKind])} ·{" "}
            {t(REACHABILITY_KEY[path.immediateBlocker.reachability])})
          </Text>
        )}
        {path.nextAchievableImprovement && (
          <Text color="secondary">
            {t("decisionPath.section.nextAchievableImprovement")}: {stepLabel(path.nextAchievableImprovement, t)}
          </Text>
        )}
        {change && (
          <Text color="tertiary">
            {t("decisionPath.change.line", {
              previous: t(FINAL_STATE_KEY[change.previousFinalReachableState]),
              current: t(FINAL_STATE_KEY[change.currentFinalReachableState]),
            })}
          </Text>
        )}
        {path.steps.length > 0 && (
          <ExpandableDetail summaryLabel={t("decisionPath.section.expandLabel")}>
            <Stack gap="metadata">
              {path.steps.map((step, index) => (
                <Inline key={`${step.source}:${step.code}:${index}`} gap="row" align="center" wrap>
                  <Text color="secondary">{stepLabel(step, t)}</Text>
                  <StatusBadge label={t(PROGRESS_KIND_KEY[step.progressKind])} tone="neutral" />
                  <StatusBadge label={t(REACHABILITY_KEY[step.reachability])} tone={REACHABILITY_TONE[step.reachability]} />
                </Inline>
              ))}
            </Stack>
          </ExpandableDetail>
        )}
      </Stack>
    </Surface>
  );
}
