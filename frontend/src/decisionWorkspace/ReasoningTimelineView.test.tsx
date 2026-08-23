import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../testUtils";
import { ReasoningTimelineView } from "./ReasoningTimelineView";
import type { TimelineEntry } from "./reasoningTimeline";

describe("ReasoningTimelineView", () => {
  it("shows an empty-state message when there are no entries", () => {
    renderWithProviders(<ReasoningTimelineView entries={[]} />);
    expect(screen.getByText(/inga händelser/i)).toBeInTheDocument();
  });

  it("renders one card per entry, in the order given", () => {
    const entries: TimelineEntry[] = [
      { source: "draft", sourceId: "d1", eventId: "e1", eventType: "revised", recordedAt: "2026-01-01T00:00:00Z" },
      { source: "assumption", sourceId: "a1", eventId: "e2", eventType: "challenged", recordedAt: "2026-01-02T00:00:00Z" },
    ];

    renderWithProviders(<ReasoningTimelineView entries={entries} />);

    expect(screen.getByText(/Utkast/)).toBeInTheDocument();
    expect(screen.getByText(/Antagande/)).toBeInTheDocument();
  });

  it("falls back gracefully for an unrecognized event type rather than crashing", () => {
    const entries: TimelineEntry[] = [
      { source: "caseCondition", sourceId: "c1", eventId: "e1", eventType: "some_future_event_type", recordedAt: "2026-01-01T00:00:00Z" },
    ];

    expect(() => renderWithProviders(<ReasoningTimelineView entries={entries} />)).not.toThrow();
  });
});
