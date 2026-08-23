import type { DimensionCoverageLevel, ConfidenceLevel, AnalysisCoverageLevel } from "../status/statusTone";

/**
 * Atlas Intelligence Sprint 1 (Data Coverage & Confidence Engine). Wire
 * shape mirrors `atlas.alpha.coverage.api...CoverageAssessmentView`
 * exactly (camelCase) -- the same object is embedded, field-for-field
 * identical, on Investment Case's `coverage`, Portfolio Cockpit's
 * per-holding `coverage`, and Portfolio Fit's own `coverage` (which is
 * what Discovery's candidate cards and Portfolio's best/worst-fit
 * sections read). One shared frontend type, unlike the backend's own
 * per-package View duplication convention -- this codebase already
 * shares presentation types freely across pages (see
 * `changeIntelligence/describeChange.ts`/`status/statusTone.ts`).
 */
export interface DimensionCoverageView {
  dimension: string;
  level: DimensionCoverageLevel;
  reasoning: string[];
}

/** Mirrors `atlas.alpha.coverage.models.ConfidenceReasonCode` exactly
 * (six members). A closed reason code plus whatever real count it
 * names -- never a pre-written sentence; this frontend owns the
 * sentence via `CONFIDENCE_REASON_KEY` below, the same "presentation
 * layer writes the prose, backend only counts" convention
 * `CONVICTION_REASON_KEY` already established. */
export type ConfidenceReasonCode =
  | "no_company_data"
  | "dimensions_conclusive"
  | "dimensions_unavailable"
  | "dimensions_partial"
  | "contradicting_evidence_present"
  | "thesis_stale";

export interface ConfidenceReasonView {
  code: ConfidenceReasonCode;
  count: number | null;
  total: number | null;
}

export interface CoverageAssessmentView {
  dimensions: DimensionCoverageView[];
  overallCoverage: AnalysisCoverageLevel;
  overallConfidence: ConfidenceLevel;
  missingDimensions: string[];
  notApplicableDimensions: string[];
  reasoning: ConfidenceReasonView[];
}
