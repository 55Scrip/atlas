import {
  BUSINESS_CATEGORY_KEY,
  BUSINESS_DATA_GAP_KEY,
  dimensionLabel,
  humanize,
  RISK_CATEGORY_KEY,
  RISK_DATA_GAP_KEY,
  VALUATION_DATA_GAP_KEY,
  type BusinessDataGapKind,
  type RiskDataGapKind,
  type Translate,
  type ValuationDataGapKind,
} from "../changeIntelligence/describeChange";
import type { ConfidenceReasonCode, ConfidenceReasonView } from "./coverageApi";
import type { TranslationKey } from "../i18n";

/**
 * Atlas Intelligence Sprint 1. `DimensionCoverage.reasoning` (backend
 * `atlas.alpha.coverage.models.DimensionCoverage.reasoning`) always
 * holds real, closed gap-kind enum values -- exactly the same
 * `BusinessDataGapKind`/`ValuationDataGapKind`/`RiskDataGapKind`
 * members `BUSINESS_DATA_GAP_KEY`/`VALUATION_DATA_GAP_KEY`/
 * `RISK_DATA_GAP_KEY` already translate elsewhere on this page (the
 * "Show supporting evidence" expand). This module reuses those three
 * maps verbatim -- no new copy is written for "why is this dimension's
 * coverage what it is," only a dispatch by which family the dimension
 * belongs to, exactly `dimensionLabel`'s own existing dispatch pattern.
 */

export function coverageDimensionLabel(dimension: string, t: Translate): string {
  return dimensionLabel(dimension, t);
}

export function coverageReasonLabel(dimension: string, reason: string, t: Translate): string {
  if (dimension in BUSINESS_CATEGORY_KEY && reason in BUSINESS_DATA_GAP_KEY) {
    return t(BUSINESS_DATA_GAP_KEY[reason as BusinessDataGapKind]);
  }
  if (dimension in RISK_CATEGORY_KEY && reason in RISK_DATA_GAP_KEY) {
    return t(RISK_DATA_GAP_KEY[reason as RiskDataGapKind]);
  }
  if (reason in VALUATION_DATA_GAP_KEY) {
    return t(VALUATION_DATA_GAP_KEY[reason as ValuationDataGapKind]);
  }
  return humanize(reason);
}

/** Mirrors `atlas.alpha.coverage.models.ConfidenceReasonCode` exactly
 * (six members). `{{count}}`/`{{total}}` placeholders are filled from
 * the reason's own real, backend-counted values -- never invented
 * here, only interpolated. */
/** `dimensions_unavailable`/`dimensions_partial` point at their own
 * `...Other` variant here -- the correct, count-agnostic default for
 * every caller that has no real count to pluralize by (e.g.
 * `referenceCodeLabel`'s own `count: 0` fallback below, where "0" is
 * itself the plural form in both English and Swedish). Any caller that
 * *does* have a real count must resolve through `confidenceReasonKey`
 * below instead, never this map directly, for those two codes. */
export const CONFIDENCE_REASON_KEY: Record<ConfidenceReasonCode, TranslationKey> = {
  no_company_data: "coverage.confidenceReason.noCompanyData",
  dimensions_conclusive: "coverage.confidenceReason.dimensionsConclusive",
  dimensions_unavailable: "coverage.confidenceReason.dimensionsUnavailableOther",
  dimensions_partial: "coverage.confidenceReason.dimensionsPartialOther",
  contradicting_evidence_present: "coverage.confidenceReason.contradictingEvidencePresent",
  thesis_stale: "coverage.confidenceReason.thesisStale",
};

/** Internal Alpha Sprint 1 (Product Polish) -- `dimensions_unavailable`/
 * `dimensions_partial` are the only two codes whose sentence is a raw
 * count of dimensions (every other code's own sentence reads correctly
 * regardless of count); those two alone need a singular/plural variant,
 * selected by the real count exactly like every other `...One`/
 * `...Other` pair already established elsewhere in this codebase. */
const PLURALIZED_CONFIDENCE_REASON_KEY: Partial<Record<ConfidenceReasonCode, { one: TranslationKey; other: TranslationKey }>> = {
  dimensions_unavailable: {
    one: "coverage.confidenceReason.dimensionsUnavailableOne",
    other: "coverage.confidenceReason.dimensionsUnavailableOther",
  },
  dimensions_partial: {
    one: "coverage.confidenceReason.dimensionsPartialOne",
    other: "coverage.confidenceReason.dimensionsPartialOther",
  },
};

/** The real, count-aware key for a `ConfidenceReasonCode` -- every
 * caller that has a real `count` (never a fallback `0`) should resolve
 * through this rather than `CONFIDENCE_REASON_KEY` directly. */
export function confidenceReasonKey(code: ConfidenceReasonCode, count: number): TranslationKey {
  const pluralized = PLURALIZED_CONFIDENCE_REASON_KEY[code];
  if (!pluralized) return CONFIDENCE_REASON_KEY[code];
  return count === 1 ? pluralized.one : pluralized.other;
}

export function confidenceReasonSentence(reason: ConfidenceReasonView, t: Translate): string {
  return t(confidenceReasonKey(reason.code, reason.count ?? 0), { count: reason.count ?? 0, total: reason.total ?? 0 });
}
