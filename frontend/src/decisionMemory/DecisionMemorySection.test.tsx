import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LanguageProvider, useTranslation } from "../i18n";
import { DecisionMemorySection } from "./DecisionMemorySection";
import type { DecisionMemoryView, DecisionSnapshotView, DecisionTimelineEntryView } from "./decisionMemoryApi";

function snapshot(overrides: Partial<DecisionSnapshotView> = {}): DecisionSnapshotView {
  return {
    caseId: "case-1",
    action: "hold",
    readinessStatus: "ready",
    blockerCodes: [],
    convictionStrength: "moderate",
    convictionStability: "stable",
    decisionPathStepCount: 0,
    decisionPathFinalState: "already_reached",
    primaryAlternativeKind: null,
    alternativeCount: 0,
    contentHash: "hash-1",
    recordedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function memory(overrides: Partial<DecisionMemoryView> = {}): DecisionMemoryView {
  const current = snapshot();
  const baselineEntry: DecisionTimelineEntryView = {
    snapshot: current,
    change: {
      caseId: "case-1",
      isBaseline: true,
      previousAction: null,
      currentAction: "hold",
      recommendationChanged: false,
      convictionDirection: null,
      readinessDirection: null,
      decisionPathDirection: null,
      blockersResolved: [],
      blockersAdded: [],
      alternativeChanged: false,
      detectedAt: "2026-01-01T00:00:00Z",
    },
  };
  return {
    caseId: "case-1",
    currentSnapshot: current,
    previousSnapshot: null,
    latestChange: null,
    history: { caseId: "case-1", entries: [baselineEntry] },
    ...overrides,
  };
}

function Wrapper({ memory: m }: { memory: DecisionMemoryView }) {
  const { t } = useTranslation();
  return <DecisionMemorySection memory={m} t={t} />;
}

function renderSection(m: DecisionMemoryView) {
  return render(
    <LanguageProvider>
      <Wrapper memory={m} />
    </LanguageProvider>,
  );
}

describe("DecisionMemorySection", () => {
  it("shows the current snapshot's translated badges", () => {
    renderSection(memory());
    expect(screen.getByText("Behåll")).toBeInTheDocument();
    expect(screen.getByText("Måttligt")).toBeInTheDocument();
  });

  it("shows the baseline disclosure when there is no latest change", () => {
    renderSection(memory());
    expect(screen.getByText("Det här är det första registrerade beslutet för det här caset.")).toBeInTheDocument();
  });

  it("shows structured change facts when a real change is present", () => {
    renderSection(
      memory({
        latestChange: {
          caseId: "case-1",
          isBaseline: false,
          previousAction: "hold",
          currentAction: "add",
          recommendationChanged: true,
          convictionDirection: "stronger",
          readinessDirection: null,
          decisionPathDirection: null,
          blockersResolved: [],
          blockersAdded: [],
          alternativeChanged: false,
          detectedAt: "2026-01-02T00:00:00Z",
        },
      }),
    );
    expect(screen.getByText("Rekommendationen ändrades från Behåll till Öka innehav.")).toBeInTheDocument();
    expect(screen.getByText("Övertygelsen stärktes.")).toBeInTheDocument();
  });

  it("only shows the expandable full history when more than one entry exists", () => {
    const { rerender } = render(
      <LanguageProvider>
        <Wrapper memory={memory()} />
      </LanguageProvider>,
    );
    expect(screen.queryByText("Visa fullständig historik")).not.toBeInTheDocument();

    const secondSnapshot = snapshot({ contentHash: "hash-2", action: "add", recordedAt: "2026-01-02T00:00:00Z" });
    const firstEntry: DecisionTimelineEntryView = memory().history.entries[0] ?? {
      snapshot: snapshot(),
      change: {
        caseId: "case-1",
        isBaseline: true,
        previousAction: null,
        currentAction: "hold",
        recommendationChanged: false,
        convictionDirection: null,
        readinessDirection: null,
        decisionPathDirection: null,
        blockersResolved: [],
        blockersAdded: [],
        alternativeChanged: false,
        detectedAt: "2026-01-01T00:00:00Z",
      },
    };
    const twoEntryMemory = memory({
      currentSnapshot: secondSnapshot,
      previousSnapshot: snapshot(),
      history: {
        caseId: "case-1",
        entries: [
          firstEntry,
          {
            snapshot: secondSnapshot,
            change: {
              caseId: "case-1",
              isBaseline: false,
              previousAction: "hold",
              currentAction: "add",
              recommendationChanged: true,
              convictionDirection: null,
              readinessDirection: null,
              decisionPathDirection: null,
              blockersResolved: [],
              blockersAdded: [],
              alternativeChanged: false,
              detectedAt: "2026-01-02T00:00:00Z",
            },
          },
        ],
      },
    });
    rerender(
      <LanguageProvider>
        <Wrapper memory={twoEntryMemory} />
      </LanguageProvider>,
    );
    expect(screen.getByText("Visa fullständig historik")).toBeInTheDocument();
  });

  it("never renders raw technical or memory/learning vocabulary", () => {
    renderSection(memory());
    expect(screen.queryByText(/\bengine\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\blearned\b/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bpersonalized\b/i)).not.toBeInTheDocument();
  });
});
