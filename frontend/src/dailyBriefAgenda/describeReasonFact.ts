import type { TranslationKey } from "../i18n";
import { describeFitVerdictCode } from "../portfolioFit/describeFitVerdict";
import { ATTENTION_CATEGORY_KEY, type AttentionCategory } from "../status/statusTone";
import type { ReasonFactView } from "./dailyBriefAgendaApi";

type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

/**
 * Implementation Sprint B1.1 (Backend Language Cleanup) -- the
 * frontend half of the permanent boundary this sprint establishes:
 * the backend sends a `ReasonFact` (a closed code plus real,
 * already-computed values, never a rendered sentence); this module
 * owns turning it into the one canonical Swedish/English phrase for
 * that fact (Phase 6: "the same reason must never appear differently
 * depending on where it is rendered" -- Daily Brief is currently the
 * only renderer, but the contract holds regardless of how many
 * consumers this grows to).
 *
 * Every key map below is a *closed* translation of a *closed* backend
 * enum -- see `atlas.alpha.daily_brief_agenda.reason_facts.ReasonCode`'s
 * own docstring for the exact source each one mirrors. `label` values
 * (a person's name, an investor's own predicate/assumption text) are
 * never looked up here -- they are real free text, rendered verbatim,
 * exactly like a ticker already is.
 */

const MISSING_EVIDENCE_KEY: Record<string, TranslationKey> = {
  no_evidence_recorded: "dailyBriefAgenda.reasonFact.missingEvidence.noEvidenceRecorded",
  observation_without_evidence: "dailyBriefAgenda.reasonFact.missingEvidence.observationWithoutEvidence",
  decision_without_linked_observation: "dailyBriefAgenda.reasonFact.missingEvidence.decisionWithoutLinkedObservation",
};

const CONCENTRATION_KEY: Record<string, TranslationKey> = {
  high_concentration: "dailyBriefAgenda.reasonFact.concentration.highConcentration",
  elevated_concentration: "dailyBriefAgenda.reasonFact.concentration.elevatedConcentration",
};

const MANAGEMENT_CREDIBILITY_KEY: Record<string, TranslationKey> = {
  inconsistent_follow_through: "dailyBriefAgenda.reasonFact.managementCredibility.inconsistentFollowThrough",
  guidance_revised_downward: "dailyBriefAgenda.reasonFact.managementCredibility.guidanceRevisedDownward",
};

const EXECUTIVE_ROLE_KEY: Record<string, TranslationKey> = {
  ceo: "dailyBriefAgenda.reasonFact.executiveChange.role.ceo",
  cfo: "dailyBriefAgenda.reasonFact.executiveChange.role.cfo",
  coo: "dailyBriefAgenda.reasonFact.executiveChange.role.coo",
  chair: "dailyBriefAgenda.reasonFact.executiveChange.role.chair",
  executive_chair: "dailyBriefAgenda.reasonFact.executiveChange.role.executiveChair",
  president: "dailyBriefAgenda.reasonFact.executiveChange.role.president",
  cto: "dailyBriefAgenda.reasonFact.executiveChange.role.cto",
  cio: "dailyBriefAgenda.reasonFact.executiveChange.role.cio",
  general_counsel: "dailyBriefAgenda.reasonFact.executiveChange.role.generalCounsel",
  board_director: "dailyBriefAgenda.reasonFact.executiveChange.role.boardDirector",
  other_executive: "dailyBriefAgenda.reasonFact.executiveChange.role.otherExecutive",
};

const EXECUTIVE_EVENT_KEY: Record<string, TranslationKey> = {
  appointment: "dailyBriefAgenda.reasonFact.executiveChange.event.appointment",
  departure: "dailyBriefAgenda.reasonFact.executiveChange.event.departure",
  resignation: "dailyBriefAgenda.reasonFact.executiveChange.event.resignation",
  retirement: "dailyBriefAgenda.reasonFact.executiveChange.event.retirement",
  termination: "dailyBriefAgenda.reasonFact.executiveChange.event.termination",
  promotion: "dailyBriefAgenda.reasonFact.executiveChange.event.promotion",
  interim_appointment: "dailyBriefAgenda.reasonFact.executiveChange.event.interimAppointment",
  permanent_appointment: "dailyBriefAgenda.reasonFact.executiveChange.event.permanentAppointment",
  board_appointment: "dailyBriefAgenda.reasonFact.executiveChange.event.boardAppointment",
  board_departure: "dailyBriefAgenda.reasonFact.executiveChange.event.boardDeparture",
  role_change: "dailyBriefAgenda.reasonFact.executiveChange.event.roleChange",
};

const CASE_CONDITION_STATUS_KEY: Record<string, TranslationKey> = {
  satisfied: "decisionWorkspace.caseConditions.status.satisfied",
};

const ASSUMPTION_STATUS_KEY: Record<string, TranslationKey> = {
  invalidated: "decisionWorkspace.assumptions.status.invalidated",
  challenged: "decisionWorkspace.assumptions.status.challenged",
};

// ---- Implementation Sprint B1.2 (Engine Reason Localization
// Contract) -- every map below reuses an existing, already-translated
// key set rather than inventing a second vocabulary for the same
// closed backend enum (Phase 6: "the same reason must never appear
// differently depending on where it is rendered"). ----

const THESIS_IMPACT_KEY: Record<string, TranslationKey> = {
  weakened: "investmentCase.whatChanged.thesisImpact.weakened",
  mixed: "investmentCase.whatChanged.thesisImpact.mixed",
  unchanged: "investmentCase.whatChanged.thesisImpact.unchanged",
  strengthened: "investmentCase.whatChanged.thesisImpact.strengthened",
};

const MONITORING_CATEGORY_KEY: Record<string, TranslationKey> = {
  new_material_evidence: "monitoring.category.newMaterialEvidence",
  material_evidence_strengthened: "evidenceTimeline.sentence.evidenceQualityChanged.positive",
  material_evidence_weakened: "evidenceTimeline.sentence.evidenceQualityChanged.negative",
  evidence_became_stale: "evidenceTimeline.sentence.freshnessChanged.negative",
  evidence_conflict_appeared: "evidenceTimeline.sentence.conflictStatusChanged.negative",
  evidence_conflict_resolved: "evidenceTimeline.sentence.conflictStatusChanged.positive",
  coverage_improved: "evidenceTimeline.sentence.coverageChanged.positive",
  coverage_deteriorated: "evidenceTimeline.sentence.coverageChanged.negative",
  confidence_improved: "evidenceTimeline.sentence.confidenceChanged.positive",
  confidence_deteriorated: "evidenceTimeline.sentence.confidenceChanged.negative",
  stance_strengthened: "evidenceTimeline.sentence.stanceChanged.positive",
  stance_weakened: "evidenceTimeline.sentence.stanceChanged.negative",
  stance_became_uncertain: "evidenceTimeline.sentence.stanceChanged.neutral",
  material_risk_appeared: "monitoring.category.materialRiskAppeared",
  // `case_condition_triggered` deliberately absent -- its own real
  // sentence embeds the investor's predicate text, not on the wire as
  // a separate field yet; falls through to the raw fallback string.
};

const DECISION_READINESS_STATUS_KEY: Record<string, TranslationKey> = {
  ready: "decisionReadiness.status.ready",
  almost_ready: "decisionReadiness.status.almostReady",
  waiting: "decisionReadiness.status.waiting",
  blocked: "decisionReadiness.status.blocked",
  unavailable: "decisionReadiness.status.unavailable",
  unknown: "decisionReadiness.status.unknown",
};

const INVESTMENT_DECISION_ACTION_KEY: Record<string, TranslationKey> = {
  buy: "investmentDecision.action.buy",
  add: "investmentDecision.action.add",
  hold: "investmentDecision.action.hold",
  reduce: "investmentDecision.action.reduce",
  exit: "investmentDecision.action.exit",
  wait: "investmentDecision.action.wait",
  no_decision: "investmentDecision.action.noDecision",
};

const CONVICTION_STRENGTH_KEY: Record<string, TranslationKey> = {
  very_strong: "recommendationConviction.strength.veryStrong",
  strong: "recommendationConviction.strength.strong",
  moderate: "recommendationConviction.strength.moderate",
  weak: "recommendationConviction.strength.weak",
  very_weak: "recommendationConviction.strength.veryWeak",
  unavailable: "recommendationConviction.strength.unavailable",
};

const DECISION_PATH_STATE_KEY: Record<string, TranslationKey> = {
  already_reached: "decisionPath.finalState.alreadyReached",
  fully_reachable: "decisionPath.finalState.fullyReachable",
  partially_reachable: "decisionPath.finalState.partiallyReachable",
  not_reachable: "decisionPath.finalState.notReachable",
};

const DECISION_RELIABILITY_LEVEL_KEY: Record<string, TranslationKey> = {
  high: "decisionReliability.level.high",
  moderate: "decisionReliability.level.moderate",
  limited: "decisionReliability.level.limited",
  unavailable: "decisionReliability.level.unavailable",
  unknown: "decisionReliability.level.unknown",
};

const PORTFOLIO_DECISION_CATEGORY_KEY: Record<string, TranslationKey> = {
  supports_portfolio: "portfolioDecision.category.supportsPortfolio",
  neutral: "portfolioDecision.category.neutral",
  requires_review: "portfolioDecision.category.requiresReview",
  conflicts_with_portfolio: "portfolioDecision.category.conflictsWithPortfolio",
  operationally_limited: "portfolioDecision.category.operationallyLimited",
  unknown: "portfolioDecision.category.unknown",
};

/** Shared shape for the six "previous -> current" transitions above:
 * look both values up in their own closed key map, then compose via
 * the matching `*.change.line` template (`{{previous}}`/`{{current}}`
 * already-translated text, never the raw enum). `null` when either
 * side isn't recognized -- never a half-translated sentence. */
function describeTransition(
  keyMap: Record<string, TranslationKey>,
  lineKey: TranslationKey,
  current: string | null,
  previous: string | null,
  t: Translate,
): string | null {
  if (!current || !previous) return null;
  const currentKey = keyMap[current];
  const previousKey = keyMap[previous];
  if (!currentKey || !previousKey) return null;
  return t(lineKey, { current: t(currentKey), previous: t(previousKey) });
}

/**
 * The translated fragment for one fact -- never ticker-prefixed;
 * `describeReasonLine` below combines it with `fact.entity` itself,
 * matching the shape the raw text it replaces already had. `null`
 * when the fact's own `value`/`label` isn't one this function
 * recognizes (defensive only -- every real backend fact carries a
 * value from the same closed enum these maps mirror).
 */
export function describeReasonFact(fact: ReasonFactView, t: Translate): string | null {
  switch (fact.code) {
    case "workflow_gap":
      if (!fact.value || fact.count == null) return null;
      return t(ATTENTION_CATEGORY_KEY[fact.value as AttentionCategory], { count: fact.count });
    case "missing_evidence":
      return fact.value ? t(MISSING_EVIDENCE_KEY[fact.value] ?? MISSING_EVIDENCE_KEY.no_evidence_recorded!) : null;
    case "concentration":
      return fact.value ? (CONCENTRATION_KEY[fact.value] ? t(CONCENTRATION_KEY[fact.value]!) : null) : null;
    case "large_unallocated_capital":
      if (fact.count == null) return null;
      return t(fact.count === 1 ? "dailyBriefAgenda.reasonFact.largeUnallocatedCapitalOne" : "dailyBriefAgenda.reasonFact.largeUnallocatedCapitalOther", {
        count: fact.count,
      });
    case "executive_change": {
      if (!fact.value || !fact.secondaryValue || !fact.label) return null;
      const roleKey = EXECUTIVE_ROLE_KEY[fact.secondaryValue];
      const eventKey = EXECUTIVE_EVENT_KEY[fact.value];
      if (!roleKey || !eventKey) return null;
      return `${fact.label} (${t(roleKey)}) ${t(eventKey)}`;
    }
    case "management_credibility":
      return fact.value ? (MANAGEMENT_CREDIBILITY_KEY[fact.value] ? t(MANAGEMENT_CREDIBILITY_KEY[fact.value]!) : null) : null;
    case "business_quality":
      return t("dailyBriefAgenda.reasonFact.businessQuality.weakeningBusiness");
    case "case_condition_status": {
      if (!fact.value || !fact.label) return null;
      const statusKey = CASE_CONDITION_STATUS_KEY[fact.value];
      return statusKey ? `${fact.label} (${t(statusKey)})` : null;
    }
    case "assumption_status": {
      if (!fact.value || !fact.label) return null;
      const statusKey = ASSUMPTION_STATUS_KEY[fact.value];
      return statusKey ? `${fact.label} (${t(statusKey)})` : null;
    }
    case "change_intelligence_thesis_impact": {
      if (!fact.value) return null;
      const impactKey = THESIS_IMPACT_KEY[fact.value];
      if (!impactKey) return null;
      const sentence = t(impactKey);
      return fact.count ? `${sentence} ${t("evidenceGraph.section.impact", { count: fact.count })}` : sentence;
    }
    case "portfolio_fit_verdict":
      return fact.value ? describeFitVerdictCode(fact.value, fact.count, t) : null;
    case "monitoring_change": {
      if (!fact.value) return null;
      const categoryKey = MONITORING_CATEGORY_KEY[fact.value];
      return categoryKey ? t(categoryKey) : null;
    }
    case "decision_readiness_transition":
      return describeTransition(DECISION_READINESS_STATUS_KEY, "decisionReadiness.change.line", fact.value, fact.secondaryValue, t);
    case "investment_decision_transition":
      return describeTransition(INVESTMENT_DECISION_ACTION_KEY, "investmentDecision.change.line", fact.value, fact.secondaryValue, t);
    case "recommendation_conviction_transition":
      return describeTransition(
        CONVICTION_STRENGTH_KEY,
        "recommendationConviction.change.line",
        fact.value,
        fact.secondaryValue,
        t,
      );
    case "decision_path_transition":
      return describeTransition(DECISION_PATH_STATE_KEY, "decisionPath.change.line", fact.value, fact.secondaryValue, t);
    case "decision_reliability_transition":
      return describeTransition(
        DECISION_RELIABILITY_LEVEL_KEY,
        "decisionReliability.change.line",
        fact.value,
        fact.secondaryValue,
        t,
      );
    case "portfolio_decision_transition":
      return describeTransition(
        PORTFOLIO_DECISION_CATEGORY_KEY,
        "portfolioDecision.change.line",
        fact.value,
        fact.secondaryValue,
        t,
      );
    default:
      return null;
  }
}

/**
 * Implementation Sprint B1.2 -- the same `MONITORING_CATEGORY_KEY` map
 * `describeReasonFact`'s own `"monitoring_change"` case reads, exported
 * directly for `monitoring/MonitoringChangeFeed.tsx` (a real Monitoring
 * change reads `category` straight off `MonitoringChangeView`, with no
 * `ReasonFact` wrapper of its own -- Monitoring's dedicated feed is a
 * different consumer of the identical closed backend enum). One
 * canonical vocabulary, two call sites, never two maps that could
 * drift apart. `null` falls back to the raw `reason` string, same
 * contract as `describeReasonFact` itself.
 */
export function describeMonitoringCategory(category: string, t: Translate): string | null {
  const key = MONITORING_CATEGORY_KEY[category];
  return key ? t(key) : null;
}

/**
 * A full reason line -- `"{{ticker}}: {{fragment}}"`, matching every
 * raw `reason` string's own existing shape, except
 * `large_unallocated_capital` (portfolio-level, no ticker to prefix,
 * mirroring the raw text it replaces having none either). Falls back
 * to `rawText` unchanged whenever `fact` is absent or its own code/
 * value isn't recognized -- never a blank line, never a partially
 * translated one.
 */
export function describeReasonLine(rawText: string, fact: ReasonFactView | null, t: Translate): string {
  if (!fact) return rawText;
  const fragment = describeReasonFact(fact, t);
  if (fragment === null) return rawText;
  if (fact.code === "large_unallocated_capital") return fragment;
  return `${fact.entity}: ${fragment}`;
}
