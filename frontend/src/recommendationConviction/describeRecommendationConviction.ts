import type { StatusTone } from "../foundation";
import type { TranslationKey } from "../i18n";
import { BLOCKER_KEY, REASON_KEY } from "../decisionReadiness/describeDecisionReadiness";
import { CONVICTION_REASON_KEY, type ConvictionReasonCode } from "../status/statusTone";
import { WEAKNESS_KEY } from "../evidenceGraph/describeEvidenceGraph";
import type { WeaknessKind } from "../evidenceGraph/evidenceGraphApi";
import type { ConvictionReasonView, ConvictionStrength, RecommendationStability } from "./recommendationConvictionApi";

/**
 * Language Audit (Deliverable 13) -- this module is the one place
 * `ConvictionStrength`/`RecommendationStability`/`ConvictionReasonView`
 * (closed, backend-internal names) are turned into plain investor
 * language. No probability wording, no AI vocabulary, no forecast
 * language, no confidence-score wording anywhere in rendered copy --
 * every reason routes through one of four already-translated
 * vocabularies (`BLOCKER_KEY`/`REASON_KEY`/`CONVICTION_REASON_KEY`/
 * `WEAKNESS_KEY`), never a fifth, newly invented one.
 */

export const STRENGTH_KEY: Record<ConvictionStrength, TranslationKey> = {
  very_strong: "recommendationConviction.strength.veryStrong",
  strong: "recommendationConviction.strength.strong",
  moderate: "recommendationConviction.strength.moderate",
  weak: "recommendationConviction.strength.weak",
  very_weak: "recommendationConviction.strength.veryWeak",
  unavailable: "recommendationConviction.strength.unavailable",
};

export const STRENGTH_TONE: Record<ConvictionStrength, StatusTone> = {
  very_strong: "positive",
  strong: "positive",
  moderate: "neutral",
  weak: "caution",
  very_weak: "caution",
  unavailable: "neutral",
};

export const STABILITY_KEY: Record<RecommendationStability, TranslationKey> = {
  stable: "recommendationConviction.stability.stable",
  fragile: "recommendationConviction.stability.fragile",
  waiting_for_evidence: "recommendationConviction.stability.waitingForEvidence",
  operationally_blocked: "recommendationConviction.stability.operationallyBlocked",
  evidence_limited: "recommendationConviction.stability.evidenceLimited",
};

export const STABILITY_TONE: Record<RecommendationStability, StatusTone> = {
  stable: "positive",
  fragile: "caution",
  waiting_for_evidence: "neutral",
  operationally_blocked: "caution",
  evidence_limited: "caution",
};

/**
 * A `ConvictionReason` is a tagged pointer at one of four already-real,
 * already-translated vocabularies -- this function resolves it to the
 * right one rather than inventing a fifth.
 */
export function reasonLabel(reason: ConvictionReasonView, t: (key: TranslationKey) => string): string {
  if (reason.source === "readiness_blocker") return t(BLOCKER_KEY[reason.code as keyof typeof BLOCKER_KEY]);
  if (reason.source === "readiness_support") return t(REASON_KEY[reason.code as keyof typeof REASON_KEY]);
  if (reason.source === "analysis_conviction") return t(CONVICTION_REASON_KEY[reason.code as ConvictionReasonCode]);
  return t(WEAKNESS_KEY[reason.code as WeaknessKind]);
}
