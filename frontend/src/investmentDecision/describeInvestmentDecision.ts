import type { StatusTone } from "../foundation";
import type { TranslationKey } from "../i18n";
import { BLOCKER_KEY, REASON_KEY } from "../decisionReadiness/describeDecisionReadiness";
import { STANCE_REASON_KEY } from "../status/statusTone";
import type { StanceReasonCode } from "../stance/stanceApi";
import type { DecisionAction, DecisionQualifierKind, DecisionReasonView } from "./investmentDecisionApi";

/**
 * Language Audit (Deliverable 12) -- this module is the one place
 * `DecisionAction`/`DecisionQualifierKind`/`DecisionReasonView` (closed,
 * backend-internal names) are turned into plain investor language. No
 * internal engine terminology, no technical implementation wording, no
 * AI vocabulary anywhere in rendered copy.
 */

export const ACTION_KEY: Record<DecisionAction, TranslationKey> = {
  buy: "investmentDecision.action.buy",
  add: "investmentDecision.action.add",
  hold: "investmentDecision.action.hold",
  reduce: "investmentDecision.action.reduce",
  exit: "investmentDecision.action.exit",
  wait: "investmentDecision.action.wait",
  no_decision: "investmentDecision.action.noDecision",
};

export const ACTION_TONE: Record<DecisionAction, StatusTone> = {
  buy: "positive",
  add: "positive",
  hold: "neutral",
  reduce: "caution",
  exit: "caution",
  wait: "neutral",
  no_decision: "neutral",
};

export const QUALIFIER_KEY: Record<DecisionQualifierKind, TranslationKey> = {
  strong_decision: "investmentDecision.qualifier.strongDecision",
  careful_decision: "investmentDecision.qualifier.carefulDecision",
  temporary_decision: "investmentDecision.qualifier.temporaryDecision",
  operationally_delayed: "investmentDecision.qualifier.operationallyDelayed",
  evidence_limited: "investmentDecision.qualifier.evidenceLimited",
  decision_blocked: "investmentDecision.qualifier.decisionBlocked",
};

/**
 * A `DecisionReason` is a tagged pointer at one of three already-real,
 * already-translated vocabularies -- this function resolves it to the
 * right one rather than inventing a fourth.
 */
export function reasonLabel(reason: DecisionReasonView, t: (key: TranslationKey) => string): string {
  if (reason.source === "readiness_blocker") return t(BLOCKER_KEY[reason.code as keyof typeof BLOCKER_KEY]);
  if (reason.source === "readiness_support") return t(REASON_KEY[reason.code as keyof typeof REASON_KEY]);
  return t(STANCE_REASON_KEY[reason.code as StanceReasonCode]);
}

/**
 * `DecisionComparisonView.sharedBlockerCodes`/`sharedSupportingReasonCodes`
 * are plain code strings (the backend's own intersection has no source
 * tag left to dispatch on) -- this tries each of the same three closed
 * vocabularies `reasonLabel` uses, in the same order, falling back to
 * the raw code only if genuinely unmatched.
 */
export function codeLabel(code: string, t: (key: TranslationKey) => string): string {
  if (code in BLOCKER_KEY) return t(BLOCKER_KEY[code as keyof typeof BLOCKER_KEY]);
  if (code in REASON_KEY) return t(REASON_KEY[code as keyof typeof REASON_KEY]);
  if (code in STANCE_REASON_KEY) return t(STANCE_REASON_KEY[code as StanceReasonCode]);
  return code;
}
