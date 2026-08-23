/**
 * Sprint 13 §2 (Reasoning Timeline) — a pure, presentation-only merge
 * of three already-fetched event histories
 * (`DecisionDraftEvent`/`AssumptionEvent`/`CaseConditionEvent`, each
 * read verbatim from its own existing `.../events` endpoint, Sprints
 * 9-11) into one chronologically-ordered list.
 *
 * This is *not* a new projection: no field is computed from anything
 * other than what each event row already carries (`recordedAt`,
 * `eventType`, and a couple of already-present identifying fields).
 * "No merged persistence" (Sprint 13 §2) is honored literally — this
 * function persists nothing; it runs fresh in the browser on data
 * already in memory and produces a plain array, not a store.
 */
import type {
  AssumptionEventRow,
  CaseConditionEventRow,
  DecisionDraftEventRow,
} from "./reasoningWorkspaceApi";

export type TimelineSource = "draft" | "assumption" | "caseCondition";

export interface TimelineEntry {
  source: TimelineSource;
  sourceId: string;
  eventId: string;
  eventType: string;
  recordedAt: string;
}

export function buildReasoningTimeline(input: {
  drafts?: Record<string, DecisionDraftEventRow[]>;
  assumptions?: Record<string, AssumptionEventRow[]>;
  caseConditions?: Record<string, CaseConditionEventRow[]>;
}): TimelineEntry[] {
  const entries: TimelineEntry[] = [];

  for (const [draftId, events] of Object.entries(input.drafts ?? {})) {
    for (const event of events) {
      entries.push({
        source: "draft",
        sourceId: draftId,
        eventId: event.id,
        eventType: event.eventType,
        recordedAt: event.recordedAt,
      });
    }
  }

  for (const [assumptionId, events] of Object.entries(input.assumptions ?? {})) {
    for (const event of events) {
      entries.push({
        source: "assumption",
        sourceId: assumptionId,
        eventId: event.id,
        eventType: event.eventType,
        recordedAt: event.recordedAt,
      });
    }
  }

  for (const [conditionId, events] of Object.entries(input.caseConditions ?? {})) {
    for (const event of events) {
      entries.push({
        source: "caseCondition",
        sourceId: conditionId,
        eventId: event.id,
        eventType: event.eventType,
        recordedAt: event.recordedAt,
      });
    }
  }

  // Oldest first, matching every existing `.../events` endpoint's own
  // ordering; a stable tiebreak on eventId keeps output deterministic
  // when two events share an identical `recordedAt` (the same
  // deterministic-ordering concern `get_latest_event`'s own
  // `(recorded_at, id)` tiebreak already exists to solve server-side).
  return entries.sort((a, b) => {
    const byTime = a.recordedAt.localeCompare(b.recordedAt);
    if (byTime !== 0) return byTime;
    return a.eventId.localeCompare(b.eventId);
  });
}
