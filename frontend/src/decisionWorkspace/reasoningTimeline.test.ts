import { describe, expect, it } from "vitest";
import { buildReasoningTimeline } from "./reasoningTimeline";

describe("buildReasoningTimeline", () => {
  it("merges events from all three sources into one chronological list", () => {
    const timeline = buildReasoningTimeline({
      drafts: {
        "draft-1": [
          { id: "d1", eventType: "revised", recordedAt: "2026-01-01T00:00:00Z", committedDecisionId: null },
        ],
      },
      assumptions: {
        "assumption-1": [
          {
            id: "a1",
            eventType: "revised",
            recordedAt: "2026-01-02T00:00:00Z",
            severity: null,
            supersededByAssumptionId: null,
          },
        ],
      },
      caseConditions: {
        "condition-1": [
          {
            id: "c1",
            eventType: "revised",
            recordedAt: "2026-01-03T00:00:00Z",
            observedValue: null,
            supersededByConditionId: null,
          },
        ],
      },
    });

    expect(timeline.map((entry) => entry.source)).toEqual(["draft", "assumption", "caseCondition"]);
  });

  it("orders entries oldest first regardless of input order", () => {
    const timeline = buildReasoningTimeline({
      assumptions: {
        "assumption-1": [
          {
            id: "later",
            eventType: "challenged",
            recordedAt: "2026-06-01T00:00:00Z",
            severity: "challenged",
            supersededByAssumptionId: null,
          },
          {
            id: "earlier",
            eventType: "revised",
            recordedAt: "2026-01-01T00:00:00Z",
            severity: null,
            supersededByAssumptionId: null,
          },
        ],
      },
    });

    expect(timeline.map((entry) => entry.eventId)).toEqual(["earlier", "later"]);
  });

  it("breaks ties on identical recordedAt by eventId for determinism", () => {
    const sameInstant = "2026-01-01T00:00:00Z";
    const timeline = buildReasoningTimeline({
      caseConditions: {
        "condition-1": [
          { id: "b-event", eventType: "revised", recordedAt: sameInstant, observedValue: null, supersededByConditionId: null },
          { id: "a-event", eventType: "revised", recordedAt: sameInstant, observedValue: null, supersededByConditionId: null },
        ],
      },
    });

    expect(timeline.map((entry) => entry.eventId)).toEqual(["a-event", "b-event"]);
  });

  it("returns an empty list when nothing is supplied", () => {
    expect(buildReasoningTimeline({})).toEqual([]);
  });

  it("carries the source id through so entries can be attributed back to their aggregate", () => {
    const timeline = buildReasoningTimeline({
      drafts: {
        "draft-42": [
          { id: "d1", eventType: "revised", recordedAt: "2026-01-01T00:00:00Z", committedDecisionId: null },
        ],
      },
    });

    expect(timeline[0]?.sourceId).toBe("draft-42");
  });
});
