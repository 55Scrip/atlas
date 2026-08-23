import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { TickerEvidenceTimelineDetail } from "./TickerEvidenceTimelineDetail";
import type { EvidenceTimelineEntryPairView } from "./evidenceTimelineApi";

const ENTRIES: EvidenceTimelineEntryPairView[] = [
  {
    snapshot: {
      overallCoverage: "substantial_coverage",
      overallConfidence: "moderate",
      stanceLevel: "reduce",
      evidenceQuality: "fresh",
      conflictStatus: "consistent",
      freshness: "fresh",
      missingDimensions: [],
      capturedAt: "2026-08-20T12:00:00Z",
    },
    history: {
      isBaseline: false,
      transitions: [
        { id: "t1", category: "stance_changed", direction: "negative", previousState: "maintain", currentState: "reduce", isMaterial: true },
      ],
      newSourceEvidence: [],
      previousCapturedAt: "2026-08-19T12:00:00Z",
      currentCapturedAt: "2026-08-20T12:00:00Z",
    },
  },
];

function Harness({ ticker }: { ticker: string }) {
  const { t } = useTranslation();
  return <TickerEvidenceTimelineDetail ticker={ticker} summaryLabel="Hur har underlaget ändrats?" t={t} />;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("TickerEvidenceTimelineDetail (Atlas Intelligence Sprint 5)", () => {
  it("does not fetch until the detail is actually opened", () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    render(
      <LanguageProvider>
        <Harness ticker="NVDA" />
      </LanguageProvider>,
    );
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("fetches and shows the most recent transition sentence once opened, never a raw category token", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ENTRIES } as Response));

    render(
      <LanguageProvider>
        <Harness ticker="NVDA" />
      </LanguageProvider>,
    );

    fireEvent.click(screen.getByText("Hur har underlaget ändrats?"));

    await waitFor(() => expect(screen.getByText("Atlas syn har försvagats.")).toBeInTheDocument());
    expect(screen.queryByText("stance_changed")).not.toBeInTheDocument();
  });

  it("does not surface a non-material transition on the compact agenda-row view", async () => {
    const nonMaterialEntries: EvidenceTimelineEntryPairView[] = [
      {
        snapshot: ENTRIES[0]!.snapshot,
        history: {
          ...ENTRIES[0]!.history,
          transitions: [
            { id: "t1", category: "confidence_changed", direction: "positive", previousState: "moderate", currentState: "high", isMaterial: false },
          ],
        },
      },
    ];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => nonMaterialEntries } as Response));

    render(
      <LanguageProvider>
        <Harness ticker="NVDA" />
      </LanguageProvider>,
    );

    fireEvent.click(screen.getByText("Hur har underlaget ändrats?"));

    await waitFor(() => expect(screen.getByText("Inget i underlaget har ändrats sedan Atlas senast tittade.")).toBeInTheDocument());
  });

  it("shows the honest empty-history state when no Case exists for this ticker", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, status: 404, json: async () => null } as Response));

    render(
      <LanguageProvider>
        <Harness ticker="ZZZZZ" />
      </LanguageProvider>,
    );

    fireEvent.click(screen.getByText("Hur har underlaget ändrats?"));

    await waitFor(() => expect(screen.getByText("Atlas har inte registrerat tillräcklig historik för det här caset ännu.")).toBeInTheDocument());
  });
});
