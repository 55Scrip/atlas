import type { StatusTone } from "../foundation";
import type { TranslationKey } from "../i18n";
import { BLOCKER_KEY, REASON_KEY } from "../decisionReadiness/describeDecisionReadiness";
import type {
  DecisionStepView,
  FinalReachableState,
  ReachabilityStatus,
  RequiredProgressKind,
} from "./decisionPathApi";

/**
 * Language Audit (Deliverable 14) -- this module is the one place
 * `RequiredProgressKind`/`ReachabilityStatus`/`FinalReachableState`/
 * `DecisionStepView` (closed, backend-internal names) are turned into
 * plain, operational, dependency-grounded language. No goal wording
 * ("improve valuation"), no coaching wording ("increase confidence"),
 * no AI/forecast wording -- every step routes through the same two
 * already-translated vocabularies Sprint 11 established
 * (`BLOCKER_KEY`/`REASON_KEY`), never a third, newly invented one.
 */

export const PROGRESS_KIND_KEY: Record<RequiredProgressKind, TranslationKey> = {
  operational: "decisionPath.progressKind.operational",
  evidence: "decisionPath.progressKind.evidence",
  coverage: "decisionPath.progressKind.coverage",
  readiness: "decisionPath.progressKind.readiness",
  dependency: "decisionPath.progressKind.dependency",
  decision: "decisionPath.progressKind.decision",
};

export const REACHABILITY_KEY: Record<ReachabilityStatus, TranslationKey> = {
  reachable: "decisionPath.reachability.reachable",
  blocked: "decisionPath.reachability.blocked",
  not_reachable: "decisionPath.reachability.notReachable",
};

export const REACHABILITY_TONE: Record<ReachabilityStatus, StatusTone> = {
  reachable: "positive",
  blocked: "caution",
  not_reachable: "caution",
};

export const FINAL_STATE_KEY: Record<FinalReachableState, TranslationKey> = {
  already_reached: "decisionPath.finalState.alreadyReached",
  fully_reachable: "decisionPath.finalState.fullyReachable",
  partially_reachable: "decisionPath.finalState.partiallyReachable",
  not_reachable: "decisionPath.finalState.notReachable",
};

export const FINAL_STATE_TONE: Record<FinalReachableState, StatusTone> = {
  already_reached: "positive",
  fully_reachable: "positive",
  partially_reachable: "neutral",
  not_reachable: "caution",
};

/**
 * The one `readiness_progress` code this package ever constructs
 * (`confidence_established`) needs its own, dedicated phrasing here --
 * `REASON_KEY`'s own copy for that code is written for the *positive*
 * case (a real, already-reached supporting reason), and would read
 * backwards ("Atlas's understanding is well established") if reused
 * verbatim to describe something *not yet* reached. Deliverable 12's
 * own "operational audit" caught this: never show achieved-state
 * copy in an outstanding-requirement context.
 */
const READINESS_PROGRESS_KEY: Record<string, TranslationKey> = {
  confidence_established: "decisionPath.progress.confidenceNotYetEstablished",
};

/**
 * A `DecisionStepView` is a tagged pointer at one of two already-real
 * vocabularies -- this function resolves it to the right one rather
 * than inventing a third. Deliverable 12's own "operational audit":
 * the resolved text always names the real dependency itself (e.g.
 * "some conclusions lack supporting evidence"), never a vague
 * instruction to the investor, and never achieved-state copy shown as
 * something still outstanding.
 */
export function stepLabel(step: DecisionStepView, t: (key: TranslationKey) => string): string {
  if (step.source === "readiness_blocker") return t(BLOCKER_KEY[step.code as keyof typeof BLOCKER_KEY]);
  return t(READINESS_PROGRESS_KEY[step.code] ?? REASON_KEY[step.code as keyof typeof REASON_KEY]);
}
