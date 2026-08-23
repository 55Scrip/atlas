import type { StatusTone } from "../foundation";
import type { TranslationKey } from "../i18n";
import type { DecisionBlockerKind, DecisionReadinessReasonKind, DecisionReadinessStatus } from "./decisionReadinessApi";

/**
 * Language Audit (Deliverable 12) -- this module is the one place
 * `DecisionReadinessStatus`/`DecisionBlockerKind`/
 * `DecisionReadinessReasonKind` (closed, backend-internal names) are
 * turned into plain investor language. No AI terminology, no "decision
 * engine" language, no technical readiness jargon anywhere in rendered
 * copy -- see the translation values themselves, never this file's own
 * identifiers.
 */

export const STATUS_KEY: Record<DecisionReadinessStatus, TranslationKey> = {
  ready: "decisionReadiness.status.ready",
  almost_ready: "decisionReadiness.status.almostReady",
  waiting: "decisionReadiness.status.waiting",
  blocked: "decisionReadiness.status.blocked",
  unavailable: "decisionReadiness.status.unavailable",
  unknown: "decisionReadiness.status.unknown",
};

export const STATUS_TONE: Record<DecisionReadinessStatus, StatusTone> = {
  ready: "positive",
  almost_ready: "positive",
  waiting: "neutral",
  blocked: "critical",
  unavailable: "caution",
  unknown: "neutral",
};

export const BLOCKER_KEY: Record<DecisionBlockerKind, TranslationKey> = {
  never_evaluated: "decisionReadiness.blocker.neverEvaluated",
  monitoring_failed: "decisionReadiness.blocker.monitoringFailed",
  no_data_source: "decisionReadiness.blocker.noDataSource",
  conflicting_evidence: "decisionReadiness.blocker.conflictingEvidence",
  critical_dependency_unresolved: "decisionReadiness.blocker.criticalDependencyUnresolved",
  monitoring_pending: "decisionReadiness.blocker.monitoringPending",
  operational_freshness_outdated: "decisionReadiness.blocker.operationalFreshnessOutdated",
  coverage_incomplete: "decisionReadiness.blocker.coverageIncomplete",
  insufficient_evidence: "decisionReadiness.blocker.insufficientEvidence",
  unknown_valuation: "decisionReadiness.blocker.unknownValuation",
  missing_observation: "decisionReadiness.blocker.missingObservation",
  missing_thesis_evidence: "decisionReadiness.blocker.missingThesisEvidence",
  avoid_decision_signal: "decisionReadiness.blocker.avoidDecisionSignal",
};

export const REASON_KEY: Record<DecisionReadinessReasonKind, TranslationKey> = {
  substantial_coverage_reached: "decisionReadiness.reason.substantialCoverageReached",
  confidence_established: "decisionReadiness.reason.confidenceEstablished",
  no_conflicts_found: "decisionReadiness.reason.noConflictsFound",
  monitoring_current: "decisionReadiness.reason.monitoringCurrent",
  decision_support_reached: "decisionReadiness.reason.decisionSupportReached",
  no_critical_dependencies: "decisionReadiness.reason.noCriticalDependencies",
};

const EXPLANATION_LEAD_KEY: Record<DecisionReadinessStatus, TranslationKey> = {
  ready: "decisionReadiness.explanation.ready",
  almost_ready: "decisionReadiness.explanation.almostReady",
  waiting: "decisionReadiness.explanation.waiting",
  blocked: "decisionReadiness.explanation.blocked",
  unavailable: "decisionReadiness.explanation.unavailable",
  unknown: "decisionReadiness.explanation.unknown",
};

/**
 * Deliverable 5 -- "Atlas is ready because...", built entirely from
 * already-derived, real facts: a fixed lead-in sentence per status,
 * plus the primary blocker/reason's own translated text. Never AI-
 * generated, never generic -- `null` reason/blocker falls back to the
 * status's own plain label rather than fabricating detail.
 */
export function explainReadiness(
  status: DecisionReadinessStatus,
  primaryBlockerKind: DecisionBlockerKind | null,
  primaryReasonKind: DecisionReadinessReasonKind | null,
  t: (key: TranslationKey) => string,
): string {
  const lead = t(EXPLANATION_LEAD_KEY[status]);
  if (status === "unknown") return lead;
  const detail =
    primaryBlockerKind !== null
      ? t(BLOCKER_KEY[primaryBlockerKind])
      : primaryReasonKind !== null
        ? t(REASON_KEY[primaryReasonKind])
        : t(STATUS_KEY[status]);
  return `${lead} ${detail}`;
}
