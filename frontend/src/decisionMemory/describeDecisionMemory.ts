import type { StatusTone } from "../foundation";
import type { TranslationKey } from "../i18n";
import { BLOCKER_KEY } from "../decisionReadiness/describeDecisionReadiness";
import type { ChangeDirection } from "./decisionMemoryApi";

/**
 * Language Audit (Deliverable 14) -- this module is the one place
 * `ChangeDirection` (closed, backend-internal name) is turned into
 * plain "recorded decision" / "latest change" language. Every other
 * field on a `DecisionSnapshotView` already has a real, translated
 * vocabulary from an earlier sprint (`ACTION_KEY`, `STATUS_KEY`,
 * `STRENGTH_KEY`/`STABILITY_KEY`, `FINAL_STATE_KEY`,
 * `ALTERNATIVE_KIND_KEY`, `BLOCKER_KEY`) -- reused directly here,
 * never re-derived. No memory/learning/AI/psychology wording anywhere.
 */

export const CHANGE_DIRECTION_KEY: Record<ChangeDirection, TranslationKey> = {
  stronger: "decisionMemory.direction.stronger",
  weaker: "decisionMemory.direction.weaker",
  unchanged: "decisionMemory.direction.unchanged",
};

export const CHANGE_DIRECTION_TONE: Record<ChangeDirection, StatusTone> = {
  stronger: "positive",
  weaker: "caution",
  unchanged: "neutral",
};

export function blockerCodeLabel(code: string, t: (key: TranslationKey) => string): string {
  return t(BLOCKER_KEY[code as keyof typeof BLOCKER_KEY]);
}
