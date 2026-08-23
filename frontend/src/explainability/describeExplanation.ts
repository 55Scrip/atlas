import { coverageDimensionLabel, coverageReasonLabel } from "../coverage/describeCoverage";
import type { DimensionCoverageView } from "../coverage/coverageApi";
import type { Translate } from "../changeIntelligence/describeChange";

/**
 * Atlas Intelligence Sprint 3 (Decision Explainability & Evidence
 * Trace, Deliverable 9 -- Missing Information). Every sentence for the
 * four reused evidence buckets (supporting/contradicting/limiting/
 * confidence drivers) already exists -- `stanceReasonSentence` (Sprint
 * 2, `../stance/describeStance`) and `confidenceReasonSentence`
 * (Sprint 1, `../coverage/describeCoverage`). This module writes only
 * the one genuinely new sentence: naming the single most valuable
 * missing dimension, using the same `coverageDimensionLabel`/
 * `coverageReasonLabel` dispatch the Coverage panel already uses for
 * every other dimension, never a new label vocabulary.
 */
export function mostValuableMissingInformationSentence(dimension: DimensionCoverageView, t: Translate): string {
  const label = coverageDimensionLabel(dimension.dimension, t);
  const reason = dimension.reasoning[0];
  const reasonText = reason ? coverageReasonLabel(dimension.dimension, reason, t) : null;
  return reasonText
    ? t("explainability.panel.mostValuableMissingSentence", { dimension: label, reason: reasonText })
    : t("explainability.panel.mostValuableMissingSentenceNoReason", { dimension: label });
}
