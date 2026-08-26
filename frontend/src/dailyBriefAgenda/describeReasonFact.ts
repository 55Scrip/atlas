import type { TranslationKey } from "../i18n";
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
    default:
      return null;
  }
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
