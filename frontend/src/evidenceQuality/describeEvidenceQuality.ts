import { dimensionLabel, humanize } from "../changeIntelligence/describeChange";
import type { Translate } from "../changeIntelligence/describeChange";
import { EVIDENCE_WARNING_KEY, type EvidenceWarningCode } from "../status/statusTone";
import type { EvidenceConflictView, FactQualityView, UnsupportedFindingView } from "./evidenceQualityApi";

/**
 * Atlas Intelligence Sprint 4 (Evidence Quality & Conflict Resolution).
 * `EvidenceWarningCode` sentences reuse `EVIDENCE_WARNING_KEY`
 * verbatim (Sprint 1/2's own "closed reason code, presentation layer
 * owns the sentence" convention). `UnsupportedFindingView.category` is
 * always a real `BusinessCategory`/`ValuationMethodKind`/`RiskCategory`
 * value -- the exact same "dimension" vocabulary Coverage/Explainability
 * already label via `dimensionLabel`, reused here rather than a second
 * label set. Fact kinds (`revenue`, `free_cash_flow`, ...) are a
 * different, raw-line-item vocabulary with no dedicated translation
 * table anywhere yet -- shown via `humanize`, the same honest fallback
 * `changeIntelligence/describeChange.ts`'s own docstring establishes
 * for "canonical enum values not worth a dedicated translation entry
 * each."
 */

export function evidenceWarningSentence(code: EvidenceWarningCode, t: Translate): string {
  return t(EVIDENCE_WARNING_KEY[code]);
}

export function factKindLabel(factKind: string): string {
  const spaced = humanize(factKind);
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

export function unsupportedFindingLabel(finding: UnsupportedFindingView, t: Translate): string {
  return dimensionLabel(finding.category, t);
}

export function conflictSentence(conflict: EvidenceConflictView, t: Translate): string {
  const values = conflict.values.map((v) => `${v.toLocaleString()} ${conflict.unit}`).join(t("evidenceQuality.conflict.valueSeparator"));
  return t("evidenceQuality.conflict.sentence", {
    factKind: factKindLabel(conflict.factKind),
    period: conflict.period,
    values,
    count: conflict.sourceRecordIds.length,
  });
}

export function factQualitySentence(fact: FactQualityView, t: Translate): string {
  return t("evidenceQuality.fact.sentence", {
    factKind: factKindLabel(fact.factKind),
    period: fact.latestPeriod ?? "",
  });
}
