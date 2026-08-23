import type { StatusTone } from "../foundation";
import type { TranslationKey } from "../i18n";
import { CONFIDENCE_REASON_KEY, confidenceReasonKey } from "../coverage/describeCoverage";
import type { ConfidenceReasonCode } from "../coverage/coverageApi";
import { BLOCKER_KEY, REASON_KEY } from "../decisionReadiness/describeDecisionReadiness";
import { EVIDENCE_QUALITY_LEVEL_KEY, EVIDENCE_WARNING_KEY } from "../status/statusTone";
import type { EvidenceQualityLevel, EvidenceWarningCode } from "../status/statusTone";
import type { ReliabilityLevel, ReliabilityReasonView, ReliabilityReferenceView, ReliabilitySource } from "./decisionReliabilityApi";

/**
 * Language Audit (Deliverable 15) -- this module is the one place
 * `ReliabilityLevel`/`ReliabilityReasonView` (closed, backend-internal
 * names) are turned into plain investor language. No AI wording, no
 * guessing, no prediction/probability/psychology wording anywhere in
 * rendered copy -- every reason routes through one of the four
 * already-translated closed vocabularies this codebase already
 * established (`CONFIDENCE_REASON_KEY`/`EVIDENCE_QUALITY_LEVEL_KEY`/
 * `EVIDENCE_WARNING_KEY`/`BLOCKER_KEY`/`REASON_KEY`), dispatched by
 * `reason.source` -- the exact same "tagged pointer, resolve through
 * the real vocabulary it names" discipline every prior Decision Layer
 * sprint's own `reasonLabel`/`codeLabel` already established. Never a
 * sixth, newly invented one.
 */

export const LEVEL_KEY: Record<ReliabilityLevel, TranslationKey> = {
  high: "decisionReliability.level.high",
  moderate: "decisionReliability.level.moderate",
  limited: "decisionReliability.level.limited",
  unavailable: "decisionReliability.level.unavailable",
  unknown: "decisionReliability.level.unknown",
};

export const SOURCE_KEY: Record<ReliabilitySource, TranslationKey> = {
  confidence: "decisionReliability.source.confidence",
  evidence_quality: "decisionReliability.source.evidenceQuality",
  readiness_blocker: "decisionReliability.source.readinessBlocker",
  readiness_support: "decisionReliability.source.readinessSupport",
};

export const LEVEL_TONE: Record<ReliabilityLevel, StatusTone> = {
  high: "positive",
  moderate: "neutral",
  limited: "caution",
  unavailable: "caution",
  unknown: "neutral",
};

/**
 * One real, already-translated sentence for a reason -- dispatched by
 * `source`, never guessed from the bare code's own shape.
 * `count`/`total`, when present, are real, already-counted upstream
 * values (`ConfidenceReason.count`/`.total`), interpolated, never
 * invented.
 */
export function reliabilityReasonLabel(reason: ReliabilityReasonView, t: (key: TranslationKey, params?: Record<string, string | number>) => string): string {
  const code = reason.reference.id;
  if (reason.source === "confidence") {
    const count = reason.count ?? 0;
    return t(confidenceReasonKey(code as ConfidenceReasonCode, count), { count, total: reason.total ?? 0 });
  }
  if (reason.source === "evidence_quality") {
    if (code in EVIDENCE_QUALITY_LEVEL_KEY) return t(EVIDENCE_QUALITY_LEVEL_KEY[code as EvidenceQualityLevel]);
    return t(EVIDENCE_WARNING_KEY[code as EvidenceWarningCode]);
  }
  if (reason.source === "readiness_blocker") return t(BLOCKER_KEY[code as keyof typeof BLOCKER_KEY]);
  return t(REASON_KEY[code as keyof typeof REASON_KEY]);
}

/**
 * Live Verification finding (Sprint 7, Deliverable 17) -- three of the
 * six `ConfidenceReasonCode` sentences require a real `{{count}}`/
 * `{{total}}` (`dimensionsConclusive`/`dimensionsUnavailable`/
 * `dimensionsPartial`); a comparison's own shared/differing reference
 * lists carry no such number (per-Case, not shared). An earlier
 * version of `referenceCodeLabel` filled the placeholder with a
 * literal `0`, which read as a real, wrong count ("0 dimension(s)...")
 * rather than an honest omission -- confirmed live, then fixed here
 * with count-free category labels used only in this comparison
 * context; the per-Case `reliabilityReasonLabel` above still shows the
 * real count.
 */
const _COMPARISON_CONFIDENCE_LABEL_KEY: Partial<Record<ConfidenceReasonCode, TranslationKey>> = {
  dimensions_conclusive: "decisionReliability.compare.confidenceReason.dimensionsConclusive",
  dimensions_unavailable: "decisionReliability.compare.confidenceReason.dimensionsUnavailable",
  dimensions_partial: "decisionReliability.compare.confidenceReason.dimensionsPartial",
};

/**
 * A comparison's own shared/differing reference lists (Deliverable
 * 10) carry no `source` tag -- the same real-code-string-only shape
 * `atlas.alpha.decision_explanation`'s own `DecisionExplanationComparison`
 * originally had before Sprint 6's own Live Verification found it
 * rendering a raw technical id. This resolver tries each of the four
 * closed vocabularies in turn (never ambiguous: the four are disjoint
 * real enums), falling back to the raw code only if genuinely
 * unmatched by any of them -- the same `codeLabel` fallback discipline
 * `investmentDecision/describeInvestmentDecision.ts` already
 * established.
 */
export function referenceCodeLabel(reference: ReliabilityReferenceView, t: (key: TranslationKey, params?: Record<string, string | number>) => string): string {
  const code = reference.id;
  if (code in _COMPARISON_CONFIDENCE_LABEL_KEY) return t(_COMPARISON_CONFIDENCE_LABEL_KEY[code as ConfidenceReasonCode]!);
  if (code in CONFIDENCE_REASON_KEY) return t(CONFIDENCE_REASON_KEY[code as ConfidenceReasonCode], { count: 0, total: 0 });
  if (code in EVIDENCE_QUALITY_LEVEL_KEY) return t(EVIDENCE_QUALITY_LEVEL_KEY[code as EvidenceQualityLevel]);
  if (code in EVIDENCE_WARNING_KEY) return t(EVIDENCE_WARNING_KEY[code as EvidenceWarningCode]);
  if (code in BLOCKER_KEY) return t(BLOCKER_KEY[code as keyof typeof BLOCKER_KEY]);
  if (code in REASON_KEY) return t(REASON_KEY[code as keyof typeof REASON_KEY]);
  return code;
}
