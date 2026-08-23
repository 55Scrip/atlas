/**
 * Thin typed client for the Evidence Timeline (Atlas Intelligence
 * Sprint 5, `atlas/alpha/evidence_timeline/api/`). Field names mirror
 * `EvidenceTimelineEntryPairView`/`EvidenceTimelineFeedView` exactly
 * (camelCase, via the backend's own `CamelModel`). This module adds no
 * logic of its own beyond the wire-format mapping.
 */

import type { AnalysisChangeDirection } from "../changeIntelligence/describeChange";

export type EvidenceTransitionCategory =
  | "coverage_changed"
  | "confidence_changed"
  | "stance_changed"
  | "freshness_changed"
  | "conflict_status_changed"
  | "evidence_quality_changed";

export interface EvidenceTransitionView {
  id: string;
  category: EvidenceTransitionCategory;
  direction: AnalysisChangeDirection;
  previousState: string;
  currentState: string;
  isMaterial: boolean;
}

/**
 * **Source Evidence History** -- a real `(factKind, period)` combination
 * new since the last capture. Deliberately never merged with
 * `EvidenceTransitionView` (**Atlas Analysis History**) -- see
 * `EvidenceHistoryView`'s own doc comment.
 */
export interface SourceEvidenceEventView {
  factKind: string;
  period: string;
}

export interface EvidenceSnapshotView {
  overallCoverage: string;
  overallConfidence: string;
  stanceLevel: string | null;
  evidenceQuality: string;
  conflictStatus: string;
  freshness: string;
  missingDimensions: string[];
  capturedAt: string;
}

export interface EvidenceHistoryView {
  isBaseline: boolean;
  /** Atlas Analysis History -- Atlas's own conclusions changing. */
  transitions: EvidenceTransitionView[];
  /** Source Evidence History -- new financial periods/facts becoming known. */
  newSourceEvidence: SourceEvidenceEventView[];
  previousCapturedAt: string | null;
  currentCapturedAt: string;
}

export interface EvidenceTimelineEntryPairView {
  snapshot: EvidenceSnapshotView;
  history: EvidenceHistoryView;
}

export interface EvidenceTimelineEntryView {
  caseId: string;
  ticker: string | null;
  snapshot: EvidenceSnapshotView;
  history: EvidenceHistoryView;
}

export interface EvidenceTimelineFeedView {
  generatedAt: string;
  entries: EvidenceTimelineEntryView[];
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T | null> {
  const response = await fetch(url, { signal: signal ?? null });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchEvidenceTimelineForCase(caseId: string, signal?: AbortSignal): Promise<EvidenceTimelineEntryPairView[] | null> {
  return getJson(`/api/evidence-timeline/case/${encodeURIComponent(caseId)}`, signal);
}

export function fetchEvidenceTimelineForTicker(ticker: string, signal?: AbortSignal): Promise<EvidenceTimelineEntryPairView[] | null> {
  return getJson(`/api/evidence-timeline/ticker/${encodeURIComponent(ticker)}`, signal);
}

export async function fetchEvidenceTimelineFeed(signal?: AbortSignal): Promise<EvidenceTimelineFeedView> {
  const response = await fetch("/api/evidence-timeline/feed", { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as EvidenceTimelineFeedView;
}
