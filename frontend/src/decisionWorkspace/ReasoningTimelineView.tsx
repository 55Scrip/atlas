import { Label, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import type { TimelineEntry, TimelineSource } from "./reasoningTimeline";

const SOURCE_LABEL_KEY: Record<TimelineSource, TranslationKey> = {
  draft: "decisionWorkspace.timeline.sourceDraft",
  assumption: "decisionWorkspace.timeline.sourceAssumption",
  caseCondition: "decisionWorkspace.timeline.sourceCaseCondition",
};

const EVENT_LABEL_KEY: Record<string, TranslationKey> = {
  revised: "decisionWorkspace.timeline.eventRevised",
  challenged: "decisionWorkspace.timeline.eventChallenged",
  evaluated_satisfied: "decisionWorkspace.timeline.eventEvaluatedSatisfied",
  retired: "decisionWorkspace.timeline.eventRetired",
  superseded: "decisionWorkspace.timeline.eventSuperseded",
  abandoned: "decisionWorkspace.timeline.eventAbandoned",
  committed: "decisionWorkspace.timeline.eventCommitted",
};

/**
 * Sprint 13 §2 — a pure presentation of an already-merged
 * `TimelineEntry[]` (`reasoningTimeline.ts`). Renders each entry's own
 * event type and recorded timestamp; never recomputes status, never
 * re-derives which event is "latest" for anything — that remains
 * exclusively the backend's own job (`reconstruct_current_state`,
 * Sprints 9-11), read separately via each aggregate's own current-state
 * view, never from this timeline.
 */
export function ReasoningTimelineView({ entries }: { entries: TimelineEntry[] }) {
  const { t, language } = useTranslation();

  if (entries.length === 0) {
    return <Text color="secondary">{t("decisionWorkspace.timeline.none")}</Text>;
  }

  return (
    <Stack gap="row">
      {entries.map((entry) => (
        <Surface key={`${entry.source}-${entry.eventId}`} tier="primary" bordered>
          <Stack gap="metadata">
            <Label>
              {t(SOURCE_LABEL_KEY[entry.source])} {t(EVENT_LABEL_KEY[entry.eventType] ?? "decisionWorkspace.timeline.eventRevised")}
            </Label>
            <Text color="tertiary" as="span">
              {new Date(entry.recordedAt).toLocaleString(language === "sv" ? "sv-SE" : "en-US")}
            </Text>
          </Stack>
        </Surface>
      ))}
    </Stack>
  );
}
