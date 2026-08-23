import type { TranslationKey } from "../i18n";
import { BLOCKER_KEY, REASON_KEY } from "../decisionReadiness/describeDecisionReadiness";
import { STANCE_REASON_KEY } from "../status/statusTone";
import type { StanceReasonCode } from "../stance/stanceApi";
import type { AlternativeKind, AlternativeReasonView } from "./opportunityCostApi";

/**
 * Language Audit (Deliverable 14) -- this module is the one place
 * `AlternativeKind`/`AlternativeReasonView` (closed, backend-internal
 * names) are turned into plain trade-off/alternative/decision
 * language. No ranking wording, no winner wording, no optimization or
 * portfolio-manager wording -- every reason routes through one of the
 * same already-translated vocabularies Sprint 11/2 established, never
 * a new one.
 */

export const ALTERNATIVE_KIND_KEY: Record<AlternativeKind, TranslationKey> = {
  increase_existing_holding: "opportunityCost.kind.increaseExistingHolding",
  open_new_position: "opportunityCost.kind.openNewPosition",
  wait: "opportunityCost.kind.wait",
  no_action: "opportunityCost.kind.noAction",
  keep_cash: "opportunityCost.kind.keepCash",
};

/**
 * The one `readiness_progress` code this program ever constructs
 * (`confidence_established`) needs the same dedicated, "not yet"
 * phrasing `atlas.alpha.decision_path`'s own frontend already
 * established -- `REASON_KEY`'s own copy is written for the
 * *positive*, already-reached case and would read backwards here.
 */
const READINESS_PROGRESS_KEY: Record<string, TranslationKey> = {
  confidence_established: "decisionPath.progress.confidenceNotYetEstablished",
};

/**
 * An `AlternativeReasonView` is a tagged pointer at one of four
 * already-real, already-translated vocabularies -- this function
 * resolves it to the right one rather than inventing a fifth.
 */
export function alternativeReasonLabel(reason: AlternativeReasonView, t: (key: TranslationKey) => string): string {
  if (reason.source === "readiness_blocker") return t(BLOCKER_KEY[reason.code as keyof typeof BLOCKER_KEY]);
  if (reason.source === "readiness_progress") {
    return t(READINESS_PROGRESS_KEY[reason.code] ?? REASON_KEY[reason.code as keyof typeof REASON_KEY]);
  }
  if (reason.source === "readiness_support") return t(REASON_KEY[reason.code as keyof typeof REASON_KEY]);
  return t(STANCE_REASON_KEY[reason.code as StanceReasonCode]);
}
