import { describe, expect, it } from "vitest";
import { filterDuplicateMonitoringChanges } from "./filterDuplicateMonitoringChanges";
import type { MonitoringChangeView, MonitoringResultView } from "./monitoringApi";

function change(overrides: Partial<MonitoringChangeView> = {}): MonitoringChangeView {
  return {
    id: "change-1",
    category: "new_material_evidence",
    materiality: "material",
    direction: "neutral",
    reason: "Atlas received new evidence that materially changed its reading of AMAT.",
    sourceCapability: "change_intelligence",
    evidenceReference: null,
    ...overrides,
  };
}

function result(overrides: Partial<MonitoringResultView> = {}): MonitoringResultView {
  return {
    caseId: "case-amat",
    ticker: "AMAT",
    scope: "portfolio",
    status: "changed_review_suggested",
    changes: [change()],
    stanceLevel: null,
    confidenceLevel: null,
    coverageLevel: null,
    latestMeaningfulEvidenceAt: null,
    recommendedAction: null,
    generatedAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("filterDuplicateMonitoringChanges (Daily Brief Consolidation)", () => {
  it("drops a change whose exact reason text is already shown in the Daily Brief agenda for the same ticker", () => {
    const agendaReasons = new Map([
      ["AMAT", new Set(["Atlas received new evidence that materially changed its reading of AMAT."])],
    ]);
    const filtered = filterDuplicateMonitoringChanges([result()], agendaReasons);
    expect(filtered).toEqual([]);
  });

  it("keeps a minor change even when the ticker has an agenda entry, since minor changes are never promoted into the agenda", () => {
    const agendaReasons = new Map([["AMAT", new Set(["some other material reason"])]]);
    const minor = result({ changes: [change({ id: "c2", materiality: "minor", reason: "Confidence increased slightly." })] });
    const filtered = filterDuplicateMonitoringChanges([minor], agendaReasons);
    expect(filtered).toHaveLength(1);
    expect(filtered[0]!.changes).toHaveLength(1);
  });

  it("keeps a change for a ticker with no agenda entry at all untouched", () => {
    const filtered = filterDuplicateMonitoringChanges([result()], new Map());
    expect(filtered).toEqual([result()]);
  });

  it("keeps a result with no changes when its status is unavailable, matching MonitoringChangeFeed's own existing filter", () => {
    const unavailable = result({ changes: [], status: "unavailable" });
    const filtered = filterDuplicateMonitoringChanges([unavailable], new Map());
    expect(filtered).toEqual([unavailable]);
  });

  it("drops a result entirely once all of its changes are deduplicated away", () => {
    const agendaReasons = new Map([["AMAT", new Set(["Atlas received new evidence that materially changed its reading of AMAT."])]]);
    const filtered = filterDuplicateMonitoringChanges([result({ status: "changed_review_suggested" })], agendaReasons);
    expect(filtered).toEqual([]);
  });

  it("partially filters a ticker with both a duplicated and a unique change, keeping only the unique one", () => {
    const agendaReasons = new Map([["AMAT", new Set(["duplicate reason"])]]);
    const mixed = result({
      changes: [
        change({ id: "c1", reason: "duplicate reason" }),
        change({ id: "c2", reason: "unique reason" }),
      ],
    });
    const filtered = filterDuplicateMonitoringChanges([mixed], agendaReasons);
    expect(filtered).toHaveLength(1);
    expect(filtered[0]!.changes.map((c) => c.reason)).toEqual(["unique reason"]);
  });
});
