import type { StatusTone } from "../foundation";
import type { TranslationKey } from "../i18n";
import { BLOCKER_KEY, REASON_KEY } from "../decisionReadiness/describeDecisionReadiness";
import { NODE_KIND_KEY, WEAKNESS_KEY } from "../evidenceGraph/describeEvidenceGraph";
import type { WeaknessKind } from "../evidenceGraph/evidenceGraphApi";
import { CONVICTION_REASON_KEY, STANCE_REASON_KEY, type ConvictionReasonCode, type StanceReasonCode } from "../status/statusTone";
import type { ChangeDirection, ExplanationLayer, ExplanationReferenceView, ExplanationSectionView } from "./decisionExplanationApi";

/**
 * Language Audit (Deliverable 14) -- this module is the one place
 * `ExplanationReferenceView`/`ExplanationLayer`/`ExplanationSectionView`
 * (closed, backend-internal names) are turned into plain investor
 * language. No AI wording, no guessing, no prediction/psychology
 * wording anywhere in rendered copy -- every `reason_code` reference
 * routes through one of the five already-translated closed
 * vocabularies this codebase already established
 * (`BLOCKER_KEY`/`REASON_KEY`/`STANCE_REASON_KEY`/
 * `CONVICTION_REASON_KEY`/`WEAKNESS_KEY`), the exact same set
 * `investmentDecision/describeInvestmentDecision.ts`'s own `codeLabel`
 * and `recommendationConviction/describeRecommendationConviction.ts`'s
 * own `reasonLabel` already try -- never a sixth, newly invented one.
 * `ExplanationReference` deliberately carries no `source` tag of its
 * own (see `models.py`'s own docstring), so this resolver tries each
 * vocabulary in turn rather than dispatching on one, falling back to
 * the raw code only if genuinely unmatched by any of the five.
 */

export const LAYER_KEY: Record<ExplanationLayer, TranslationKey> = {
  investment_decision: "decisionExplanation.layer.investmentDecision",
  recommendation_conviction: "decisionExplanation.layer.recommendationConviction",
  decision_readiness: "decisionExplanation.layer.decisionReadiness",
  decision_path: "decisionExplanation.layer.decisionPath",
  evidence_graph: "decisionExplanation.layer.evidenceGraph",
};

export const SECTION_KEY: Record<ExplanationSectionView["kind"], TranslationKey> = {
  supporting: "decisionExplanation.section.supportingHeading",
  blocking: "decisionExplanation.section.blockingHeading",
  dependency: "decisionExplanation.section.dependencyHeading",
  historical: "decisionExplanation.section.historicalHeading",
};

export const CHANGE_DIRECTION_KEY: Record<ChangeDirection, TranslationKey> = {
  stronger: "decisionExplanation.direction.stronger",
  weaker: "decisionExplanation.direction.weaker",
  unchanged: "decisionExplanation.direction.unchanged",
};

export const CHANGE_DIRECTION_TONE: Record<ChangeDirection, StatusTone> = {
  stronger: "positive",
  weaker: "caution",
  unchanged: "neutral",
};

/**
 * One real, already-translated label for a reference, never a raw
 * technical id shown as if it were prose. `FINDING`/`OBSERVATION`
 * references show the Evidence Graph's own node-kind label (the
 * specific real id stays available to the caller for a "view
 * evidence" link, never hidden, just not spelled out inline here).
 * `REASON_CODE` tries the five closed vocabularies in a fixed order.
 * `DECISION_SNAPSHOT` names the fact plainly: a real recorded change
 * exists.
 */
export function referenceLabel(reference: ExplanationReferenceView, t: (key: TranslationKey) => string): string {
  if (reference.kind === "finding") return t(NODE_KIND_KEY.finding);
  if (reference.kind === "observation") return t(NODE_KIND_KEY.observation);
  if (reference.kind === "decision_snapshot") return t("decisionExplanation.reference.decisionSnapshot");

  const code = reference.id;
  if (code in BLOCKER_KEY) return t(BLOCKER_KEY[code as keyof typeof BLOCKER_KEY]);
  if (code in REASON_KEY) return t(REASON_KEY[code as keyof typeof REASON_KEY]);
  if (code in STANCE_REASON_KEY) return t(STANCE_REASON_KEY[code as StanceReasonCode]);
  if (code in CONVICTION_REASON_KEY) return t(CONVICTION_REASON_KEY[code as ConvictionReasonCode]);
  if (code in WEAKNESS_KEY) return t(WEAKNESS_KEY[code as WeaknessKind]);
  return code;
}
