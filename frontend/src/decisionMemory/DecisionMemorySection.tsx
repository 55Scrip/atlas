import { Heading, Inline, Stack, StatusBadge, Surface, Text } from "../foundation";
import type { TranslationKey } from "../i18n";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { ACTION_KEY } from "../investmentDecision/describeInvestmentDecision";
import { STATUS_KEY } from "../decisionReadiness/describeDecisionReadiness";
import { STRENGTH_KEY } from "../recommendationConviction/describeRecommendationConviction";
import { FINAL_STATE_KEY } from "../decisionPath/describeDecisionPath";
import { CHANGE_DIRECTION_KEY, CHANGE_DIRECTION_TONE, blockerCodeLabel } from "./describeDecisionMemory";
import type { DecisionMemoryChangeView, DecisionMemoryView, DecisionSnapshotView, DecisionTimelineEntryView } from "./decisionMemoryApi";

/**
 * Investment Case Integration (Atlas Decision Layer Sprint 5,
 * Deliverable 6). Mirrors every prior Decision Layer section's own
 * "kompakt, evidence first, progressively disclosed" shape: the
 * current snapshot always visible, the latest real change as the
 * compact answer, the full append-only history one click away.
 *
 * `key`s on history entries use `snapshot.recordedAt`, never
 * `snapshot.contentHash` and never an array index. `contentHash`
 * (`atlas.alpha.decision_memory.engine`'s own `content_hash`) is
 * computed only over the decision-relevant fields and deliberately
 * excludes `recorded_at` -- it exists so the repository's `add` can be
 * idempotent-by-content against the current head, not to identify a
 * row. Two distinct, real snapshots (recorded at different times) can
 * legitimately hash identically if the decision state cycles back to
 * an earlier configuration (e.g. BUY -> HOLD -> BUY with every other
 * field unchanged) -- the idempotency check only ever compares against
 * the immediate current head, not the full history, so this is not an
 * edge case to special-case away. `recordedAt` is the real per-case
 * unique identity: the backend's own table primary key is the
 * synthetic `f"{case_id}:{recorded_at}"` (`decision_memory/table.py`),
 * and every entry rendered here already belongs to one fixed `caseId`.
 */
export function DecisionMemorySection({
  memory,
  t,
}: {
  memory: DecisionMemoryView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Surface tier="primary">
      <Stack gap="metadata">
        <Heading level={3}>{t("decisionMemory.section.heading")}</Heading>
        <SnapshotBadges snapshot={memory.currentSnapshot} t={t} />
        {memory.latestChange ? (
          <Stack gap="metadata">
            <Text color="secondary" as="span">
              {t("decisionMemory.section.latestChange")}:
            </Text>
            <ChangeFacts change={memory.latestChange} t={t} />
          </Stack>
        ) : (
          <Text color="tertiary">{t("decisionMemory.section.baseline")}</Text>
        )}
        {memory.history.entries.length > 1 && (
          <ExpandableDetail summaryLabel={t("decisionMemory.section.expandLabel")}>
            <Stack gap="metadata">
              {[...memory.history.entries].reverse().map((entry) => (
                <HistoryEntryRow key={entry.snapshot.recordedAt} entry={entry} t={t} />
              ))}
            </Stack>
          </ExpandableDetail>
        )}
      </Stack>
    </Surface>
  );
}

function SnapshotBadges({
  snapshot,
  t,
}: {
  snapshot: DecisionSnapshotView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Inline gap="row" align="center" wrap>
      <StatusBadge label={t(ACTION_KEY[snapshot.action as keyof typeof ACTION_KEY])} tone="neutral" />
      <StatusBadge label={t(STRENGTH_KEY[snapshot.convictionStrength as keyof typeof STRENGTH_KEY])} tone="neutral" />
      <StatusBadge label={t(STATUS_KEY[snapshot.readinessStatus as keyof typeof STATUS_KEY])} tone="neutral" />
      <StatusBadge label={t(FINAL_STATE_KEY[snapshot.decisionPathFinalState as keyof typeof FINAL_STATE_KEY])} tone="neutral" />
    </Inline>
  );
}

/** Exported for History's own Decision Memory timeline (Product
 * Intelligence Sprint 4 -- History & Decision Memory Activation),
 * which reuses this exact rendering rather than duplicating it. */
export function ChangeFacts({
  change,
  t,
}: {
  change: DecisionMemoryChangeView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Stack gap="metadata">
      {change.recommendationChanged && (
        <Text color="secondary">
          {t("decisionMemory.change.recommendationChanged", {
            previous: change.previousAction ? t(ACTION_KEY[change.previousAction as keyof typeof ACTION_KEY]) : "",
            current: t(ACTION_KEY[change.currentAction as keyof typeof ACTION_KEY]),
          })}
        </Text>
      )}
      {change.convictionDirection && change.convictionDirection !== "unchanged" && (
        <Inline gap="row" align="center">
          <Text color="secondary">
            {t("decisionMemory.change.convictionDirection", { direction: t(CHANGE_DIRECTION_KEY[change.convictionDirection]) })}
          </Text>
          <StatusBadge label={t(CHANGE_DIRECTION_KEY[change.convictionDirection])} tone={CHANGE_DIRECTION_TONE[change.convictionDirection]} />
        </Inline>
      )}
      {change.readinessDirection && change.readinessDirection !== "unchanged" && (
        <Text color="secondary">
          {t("decisionMemory.change.readinessDirection", { direction: t(CHANGE_DIRECTION_KEY[change.readinessDirection]) })}
        </Text>
      )}
      {change.decisionPathDirection && change.decisionPathDirection !== "unchanged" && (
        <Text color="secondary">
          {t("decisionMemory.change.pathDirection", { direction: t(CHANGE_DIRECTION_KEY[change.decisionPathDirection]) })}
        </Text>
      )}
      {change.blockersResolved.length > 0 && (
        <Text color="secondary">
          {t("decisionMemory.change.blockersResolved", { items: change.blockersResolved.map((c) => blockerCodeLabel(c, t)).join(" · ") })}
        </Text>
      )}
      {change.blockersAdded.length > 0 && (
        <Text color="secondary">
          {t("decisionMemory.change.blockersAdded", { items: change.blockersAdded.map((c) => blockerCodeLabel(c, t)).join(" · ") })}
        </Text>
      )}
      {change.alternativeChanged && <Text color="secondary">{t("decisionMemory.change.alternativeChanged")}</Text>}
    </Stack>
  );
}

function HistoryEntryRow({
  entry,
  t,
}: {
  entry: DecisionTimelineEntryView;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Stack gap="metadata">
      <Inline gap="row" align="center" wrap>
        <Text as="span" style={{ fontWeight: 600 }}>
          {new Date(entry.snapshot.recordedAt).toLocaleString()}
        </Text>
        <StatusBadge label={t(ACTION_KEY[entry.snapshot.action as keyof typeof ACTION_KEY])} tone="neutral" />
      </Inline>
      {entry.change.isBaseline ? (
        <Text color="tertiary">{t("decisionMemory.section.baseline")}</Text>
      ) : (
        <ChangeFacts change={entry.change} t={t} />
      )}
    </Stack>
  );
}
