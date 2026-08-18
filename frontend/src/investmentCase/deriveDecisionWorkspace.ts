import type {
  AnalysisHighlightKind,
  AnalysisOpenQuestionOrigin,
  AnalysisRiskCategory,
  AnalysisRiskStatus,
  Translate,
} from "../changeIntelligence/describeChange";
import { OPEN_QUESTION_ORIGIN_KEY, RISK_CATEGORY_KEY } from "../changeIntelligence/describeChange";
import type { ConvictionLevel, DecisionSupportLevel } from "../status/statusTone";
import { CONVICTION_LEVEL_KEY, DECISION_SUPPORT_STATEMENT_KEY } from "../status/statusTone";
import type { TranslationKey } from "../i18n";
import { STRENGTH_SENTENCE_KEY, CHALLENGE_SENTENCE_KEY } from "./HeroCard";

/**
 * Decision Workspace v1 -- Phase 2B classification, carried into runtime.
 *
 * Every one of the five values corresponds exactly to the Phase 2B gate
 * table (see the sprint's own implementation report): what this section's
 * content actually is, not what UX-009 wishes it were. `UNAVAILABLE_
 * WITH_CURRENT_MODEL` sections must render an honest, explicit gap
 * message -- never fabricated content, never silent omission. This module
 * makes zero backend calls and reads zero fields beyond what Investment
 * Case already fetches; it is presentation-and-sequencing only.
 */
export type DecisionWorkspaceClassification =
  | "READ_ONLY_EXISTING_STATE"
  | "EXISTING_DECISION_FIELD"
  | "EXISTING_OUTCOME_OR_TRADE_FIELD"
  | "TRANSIENT_UI_STATE"
  | "UNAVAILABLE_WITH_CURRENT_MODEL";

export interface DecisionWorkspaceItem {
  classification: DecisionWorkspaceClassification;
  text: string;
}

export interface DecisionWorkspaceSection {
  /** UX-009's own fixed 1-13 section numbering -- never reordered. */
  id: number;
  titleKey: TranslationKey;
  /** UX-009 "Section Hierarchy": Sections 1, 2, 3, 12 are never
   * collapsible; everything else adapts to decision significance. This
   * module applies only the binary always/collapsible split UX-009
   * itself fixes -- the full seven-decision-type expansion matrix is
   * presentation-depth detail UX-009 explicitly defers to UX-009A,
   * which UX-009 itself says not to produce yet. */
  alwaysVisible: boolean;
  items: DecisionWorkspaceItem[];
  /** Set when every item in this section is UNAVAILABLE_WITH_CURRENT_MODEL
   * -- lets the renderer show one honest, calm gap line instead of an
   * empty section, matching this codebase's established
   * ValuationSupport/RecommendationWithheld gap-disclosure pattern. */
  fullyUnavailable: boolean;
}

export interface DecisionWorkspaceInput {
  atlasThesis: { posture: string; narrative: string };
  conviction: { level: ConvictionLevel };
  recommendation: { level: DecisionSupportLevel };
  currentAnalysisAt: string;
  strengthKinds: AnalysisHighlightKind[];
  riskKinds: AnalysisHighlightKind[];
  riskFindings: { category: AnalysisRiskCategory; status: AnalysisRiskStatus; contradictingFacts: string[] }[];
  valuationAssumptions: string[];
  keyOpenQuestions: { origin: AnalysisOpenQuestionOrigin; reference: string | null }[];
  holdingWeightPercent: number | null;
}

const UNRESOLVED_RISK_STATUSES: readonly AnalysisRiskStatus[] = ["moderate", "high"];

function item(classification: DecisionWorkspaceClassification, text: string): DecisionWorkspaceItem {
  return { classification, text };
}

function section(
  id: number,
  titleKey: TranslationKey,
  alwaysVisible: boolean,
  items: DecisionWorkspaceItem[],
): DecisionWorkspaceSection {
  return {
    id,
    titleKey,
    alwaysVisible,
    items,
    // Collapsing to one generic gap line only pays for itself when it
    // replaces more than one repeated caveat -- a single-item section
    // (e.g. Section 8's weight-specific consequencesGapWithWeight text)
    // must keep rendering its own, more specific item text instead.
    fullyUnavailable: items.length > 1 && items.every((i) => i.classification === "UNAVAILABLE_WITH_CURRENT_MODEL"),
  };
}

/**
 * Builds the 13 `UX-009` sections in their fixed order, from data
 * Investment Case already fetches (see `DecisionWorkspaceInput` --
 * every field maps to a real, already-rendered part of this page) plus
 * the investor's own in-progress action choice. No network call, no
 * persistence, no new domain concept -- see the Phase 2B classification
 * table this function's own comments realize in code.
 */
export function buildDecisionWorkspaceSections(
  input: DecisionWorkspaceInput,
  t: Translate,
): DecisionWorkspaceSection[] {
  const contradictingRiskFacts = input.riskFindings
    .filter((f) => UNRESOLVED_RISK_STATUSES.includes(f.status))
    .flatMap((f) => f.contradictingFacts.map((fact) => `${t(RISK_CATEGORY_KEY[f.category])}: ${fact}`));

  const openQuestionLines = input.keyOpenQuestions.map((q) =>
    q.reference ? `${t(OPEN_QUESTION_ORIGIN_KEY[q.origin])} (${q.reference})` : t(OPEN_QUESTION_ORIGIN_KEY[q.origin]),
  );

  return [
    // Section 1 -- Current Conclusion. READ_ONLY_EXISTING_STATE:
    // AtlasThesisView (posture + narrative), already computed and
    // already rendered elsewhere on this page (Hero/Reasoning).
    section(1, "investmentCase.decisionWorkspace.section1.title", true, [
      item("READ_ONLY_EXISTING_STATE", input.atlasThesis.narrative),
      item(
        "READ_ONLY_EXISTING_STATE",
        `${t("investmentCase.decisionWorkspace.section1.confidenceLabel")}: ${t(CONVICTION_LEVEL_KEY[input.conviction.level])}`,
      ),
      item(
        "READ_ONLY_EXISTING_STATE",
        `${t("investmentCase.decisionWorkspace.section1.sourceLabel")}: ${input.currentAnalysisAt}`,
      ),
    ]),

    // Section 2 -- Why a Decision Is Required. TRANSIENT_UI_STATE:
    // every current entry point is the investor's own click -- no
    // Daily Brief nudge, review-mode re-entry, or invalidation-signal
    // trigger exists yet, so "User-initiated" (one of UX-009's own
    // eight named trigger values) is the accurate value today, not a
    // downgrade.
    section(2, "investmentCase.decisionWorkspace.section2.title", true, [
      item("TRANSIENT_UI_STATE", t("investmentCase.decisionWorkspace.section2.userInitiated")),
    ]),

    // Section 4 (rationale summary shown ahead of the reason field) --
    // READ_ONLY_EXISTING_STATE supporting conclusions + assumptions +
    // material risks. The primary-reason field itself is
    // EXISTING_DECISION_FIELD and stays exactly where it already is in
    // the flow (Decision.investment_case.reason) -- not duplicated here.
    section(4, "investmentCase.decisionWorkspace.section4.title", false, [
      item("READ_ONLY_EXISTING_STATE", t(DECISION_SUPPORT_STATEMENT_KEY[input.recommendation.level])),
      ...input.valuationAssumptions.map((a) => item("READ_ONLY_EXISTING_STATE" as const, a)),
      ...contradictingRiskFacts.map((f) => item("READ_ONLY_EXISTING_STATE" as const, f)),
    ]),

    // Section 5 -- Supporting Factors. READ_ONLY_EXISTING_STATE: the
    // same strengthKinds this page's own Investment Argument section
    // already renders, reused verbatim through the same translation
    // bank -- never a second, divergent copy.
    section(
      5,
      "investmentCase.decisionWorkspace.section5.title",
      false,
      input.strengthKinds.length > 0
        ? input.strengthKinds.map((k) => item("READ_ONLY_EXISTING_STATE" as const, t(STRENGTH_SENTENCE_KEY[k])))
        : [item("READ_ONLY_EXISTING_STATE", t("investmentCase.argument.supportsEmpty"))],
    ),

    // Section 6 -- Challenges. READ_ONLY_EXISTING_STATE content (same
    // riskKinds/open-questions this page already surfaces);
    // UNAVAILABLE_WITH_CURRENT_MODEL for behavioral context (no such
    // detection exists) and for persisted acknowledgment (Decision has
    // no field to hold it -- see this sprint's Phase 2B table).
    section(6, "investmentCase.decisionWorkspace.section6.title", false, [
      ...(input.riskKinds.length > 0
        ? input.riskKinds.map((k) => item("READ_ONLY_EXISTING_STATE" as const, t(CHALLENGE_SENTENCE_KEY[k])))
        : [item("READ_ONLY_EXISTING_STATE" as const, t("investmentCase.argument.challengesEmpty"))]),
      ...openQuestionLines.map((line) => item("READ_ONLY_EXISTING_STATE" as const, line)),
      item("UNAVAILABLE_WITH_CURRENT_MODEL", t("investmentCase.decisionWorkspace.section6.behavioralContextGap")),
      item("UNAVAILABLE_WITH_CURRENT_MODEL", t("investmentCase.decisionWorkspace.section6.acknowledgmentGap")),
    ]),

    // Section 7 -- Opportunity Cost. The Maintain/No-Action fallback
    // line is TRANSIENT_UI_STATE (a static string, no data dependency);
    // real cross-position alternative ranking is
    // UNAVAILABLE_WITH_CURRENT_MODEL -- no such comparison engine
    // exists anywhere in this codebase.
    section(7, "investmentCase.decisionWorkspace.section7.title", false, [
      item("UNAVAILABLE_WITH_CURRENT_MODEL", t("investmentCase.decisionWorkspace.section7.alternativesGap")),
    ]),

    // Section 8 -- Portfolio Consequences. UNAVAILABLE_WITH_CURRENT_MODEL
    // in full: every sub-item requires a post-decision portfolio
    // *simulation* (hypothetical weight after this decision, exposure
    // deltas), which DE-006 §8 explicitly, doctrinally excludes from
    // this codebase's scope -- an architectural boundary, not an
    // oversight this sprint can or should close.
    section(8, "investmentCase.decisionWorkspace.section8.title", false, [
      item(
        "UNAVAILABLE_WITH_CURRENT_MODEL",
        input.holdingWeightPercent !== null
          ? t("investmentCase.decisionWorkspace.section8.consequencesGapWithWeight", {
              weight: input.holdingWeightPercent.toFixed(2),
            })
          : t("investmentCase.decisionWorkspace.section8.consequencesGap"),
      ),
    ]),

    // Section 9 -- Assumptions, Monitoring and Invalidation. Supporting
    // Assumptions reuse the same read-only source as Section 4;
    // Monitoring/Invalidation Conditions are
    // UNAVAILABLE_WITH_CURRENT_MODEL -- no persisted
    // scheduling/observation-registration concept exists on Decision.
    section(9, "investmentCase.decisionWorkspace.section9.title", false, [
      ...input.valuationAssumptions.map((a) => item("READ_ONLY_EXISTING_STATE" as const, a)),
      item("UNAVAILABLE_WITH_CURRENT_MODEL", t("investmentCase.decisionWorkspace.section9.monitoringGap")),
      item("UNAVAILABLE_WITH_CURRENT_MODEL", t("investmentCase.decisionWorkspace.section9.invalidationGap")),
    ]),

    // Section 10 -- Implementation Plan. The type selector (Immediate/
    // Gradual/Conditional/Deferred/No action) and a trackable status
    // are UNAVAILABLE_WITH_CURRENT_MODEL; the eventual real trade
    // report, once made, is EXISTING_OUTCOME_OR_TRADE_FIELD and is left
    // exactly where the existing "Report Transaction" flow already
    // captures it -- not duplicated here.
    section(10, "investmentCase.decisionWorkspace.section10.title", false, [
      item("UNAVAILABLE_WITH_CURRENT_MODEL", t("investmentCase.decisionWorkspace.section10.typeGap")),
      item("EXISTING_OUTCOME_OR_TRADE_FIELD", t("investmentCase.decisionWorkspace.section10.tradeNote")),
    ]),

    // Section 11 -- Review Plan. UNAVAILABLE_WITH_CURRENT_MODEL: no
    // scheduling/trigger persistence exists on Decision at all.
    section(11, "investmentCase.decisionWorkspace.section11.title", false, [
      item("UNAVAILABLE_WITH_CURRENT_MODEL", t("investmentCase.decisionWorkspace.section11.reviewPlanGap")),
    ]),
  ];
}
