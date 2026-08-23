import { STANCE_REASON_KEY, type StanceReasonCode } from "../status/statusTone";
import type { Translate } from "../changeIntelligence/describeChange";
import type { StanceReasonView, StanceView } from "./stanceApi";

/**
 * Atlas Intelligence Sprint 2 (Recommendation Quality & Actionability,
 * Deliverable 10 -- Recommendation Language). Every sentence here is
 * calm, present-tense, and non-imperative -- "Atlas currently supports
 * maintaining this position because..." never "You should...". Reuses
 * `STANCE_REASON_KEY` verbatim; no free text is written here beyond
 * picking which already-translated reason to show.
 */

export function stanceReasonSentence(reason: StanceReasonView, t: Translate): string {
  return t(STANCE_REASON_KEY[reason.code]);
}

/** The one reason that most directly explains `stance.level` -- always
 * `reasoning[0]` (the engine's own ordered decision trail names the
 * deciding fact first), falling back to `null` only if `reasoning` is
 * somehow empty (never true in practice; every branch names at least
 * one reason). */
export function primaryStanceReason(stance: StanceView): StanceReasonView | null {
  return stance.reasoning[0] ?? null;
}

/** A real limiting signal worth surfacing as "...while remaining
 * cautious because..." -- only when a directional stance was reached
 * despite it (Deliverable 5's own worked example). Excludes whichever
 * reason already appears as the primary one, so the two sentences
 * never repeat each other. */
export function cautionaryStanceReason(stance: StanceView): StanceReasonView | null {
  const primary = primaryStanceReason(stance);
  const candidate = stance.limitingSignals.find((r) => r.code !== primary?.code);
  return candidate ?? null;
}

/** Reason codes that only ever appear when the engine itself could not
 * reach a confident directional stance (the gate fired) -- for these,
 * the "primary reason" already fully explains `level`, so a second
 * "while remaining cautious" sentence would only repeat it. */
const _GATE_REASON_CODES: ReadonlySet<StanceReasonCode> = new Set([
  "no_company_data",
  "contradicting_evidence_present",
  "conviction_insufficient",
  "confidence_very_limited",
  "confidence_limited",
  "confidence_moderate",
]);

export function showsCautionarySentence(stance: StanceView): boolean {
  const primary = primaryStanceReason(stance);
  if (primary !== null && _GATE_REASON_CODES.has(primary.code)) return false;
  return cautionaryStanceReason(stance) !== null;
}
