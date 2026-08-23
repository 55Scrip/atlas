/**
 * Sprint 13 (Decision Workspace Product Integration): a thin typed
 * client over Sprint 12's Reasoning Workspace API
 * (`atlas/core/infrastructure/api/reasoning_workspace/`). No
 * derivation, no caching, no client-side recomputation of anything
 * the backend already computed -- every function here is a plain
 * fetch wrapper, directly modeled on `history/securityConfirmationApi.ts`
 * and `decisionWorkspace/decisionDraftApi.ts`'s own identical shape.
 *
 * `fetchDecisionDraftEvents`/`fetchAssumptionEvents`/
 * `fetchCaseConditionEvents` call the three existing, per-aggregate
 * `.../events` endpoints (Sprints 9-11) directly -- Sprint 12 never
 * built a merged event endpoint, and this module does not either;
 * merging the three raw histories into one chronological list is done
 * by `buildReasoningTimeline` (`reasoningTimeline.ts`), a pure,
 * presentation-only sort with no new backend concept behind it.
 */

export type DecisionDraftStatus = "active" | "abandoned" | "committed";
export type AssumptionStatus = "supported" | "challenged" | "invalidated" | "superseded" | "retired";
export type CaseConditionStatus = "active" | "satisfied" | "superseded" | "retired";
export type Authorship = "atlas" | "user" | "mixed";
export type CaseConditionRole = "monitoring" | "invalidation";
export type ThresholdOperator = "<" | "<=" | ">" | ">=" | "==" | "!=";

export interface DecisionSummaryView {
  id: string;
  caseId: string;
  userId: string;
  decisionType: string;
  subject: string;
  reason: string;
  confidence: number;
  decidedAt: string;
  recordedAt: string;
  source: string;
  observationId: string | null;
}

export interface DecisionContextView {
  contextId: string;
  decisionId: string;
  situation: string;
  portfolioRelevance: string | null;
  capitalConsiderations: string | null;
  alternativesConsidered: string[];
  uncertainties: string[];
  capturedAt: string;
  recordedAt: string;
}

export interface DecisionDraftView {
  draftId: string;
  caseId: string;
  userId: string;
  status: DecisionDraftStatus;
  decisionType: string | null;
  subject: string | null;
  reason: string | null;
  confidence: number | null;
  decidedAt: string | null;
  source: string | null;
  situation: string | null;
  portfolioRelevance: string | null;
  capitalConsiderations: string | null;
  alternativesConsidered: string[];
  uncertainties: string[];
  committedDecisionId: string | null;
  latestEventId: string;
  createdAt: string;
  updatedAt: string;
}

export interface AssumptionView {
  assumptionId: string;
  decisionId: string;
  caseId: string;
  status: AssumptionStatus;
  isActive: boolean;
  statement: string | null;
  authorship: Authorship | null;
  linkedCaseConditionIds: string[];
  lastChallengeEvidenceId: string | null;
  lastChallengeNote: string | null;
  supersededByAssumptionId: string | null;
  latestEventId: string;
  createdAt: string;
  updatedAt: string;
}

export interface CaseConditionView {
  conditionId: string;
  caseId: string;
  decisionId: string | null;
  status: CaseConditionStatus;
  isActive: boolean;
  predicateText: string | null;
  role: CaseConditionRole | null;
  authorship: Authorship | null;
  structuredKind: "date" | "threshold" | null;
  thresholdDate: string | null;
  thresholdMetric: string | null;
  thresholdOperator: ThresholdOperator | null;
  thresholdValue: number | null;
  lastObservedValue: number | null;
  supersededByConditionId: string | null;
  latestEventId: string;
  createdAt: string;
  updatedAt: string;
}

export interface DecisionReasoningWorkspace {
  decision: DecisionSummaryView;
  decisionContext: DecisionContextView | null;
  originatingDraft: DecisionDraftView | null;
  activeCaseDrafts: DecisionDraftView[];
  assumptions: AssumptionView[];
  caseConditions: CaseConditionView[];
}

export interface RawEvent {
  id: string;
  eventType: string;
  recordedAt: string;
}

export interface DecisionDraftEventRow extends RawEvent {
  committedDecisionId: string | null;
}

export interface AssumptionEventRow extends RawEvent {
  severity: "challenged" | "invalidated" | null;
  supersededByAssumptionId: string | null;
}

export interface CaseConditionEventRow extends RawEvent {
  observedValue: number | null;
  supersededByConditionId: string | null;
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function fetchDecisionReasoningWorkspace(
  decisionId: string,
  signal?: AbortSignal,
): Promise<DecisionReasoningWorkspace> {
  return getJson(`/api/decisions/${decisionId}/reasoning-workspace`, signal);
}

export function fetchDecisionDraftEvents(
  draftId: string,
  signal?: AbortSignal,
): Promise<DecisionDraftEventRow[]> {
  return getJson(`/api/decision-drafts/${draftId}/events`, signal);
}

export function fetchAssumptionEvents(
  assumptionId: string,
  signal?: AbortSignal,
): Promise<AssumptionEventRow[]> {
  return getJson(`/api/assumptions/${assumptionId}/events`, signal);
}

export function fetchCaseConditionEvents(
  conditionId: string,
  signal?: AbortSignal,
): Promise<CaseConditionEventRow[]> {
  return getJson(`/api/case-conditions/${conditionId}/events`, signal);
}

export interface LinkedCaseConditionInput {
  predicateText?: string | null;
  role?: CaseConditionRole | null;
  authorship?: Authorship | null;
  structuredKind?: "date" | "threshold" | null;
  thresholdDate?: string | null;
  thresholdMetric?: string | null;
  thresholdOperator?: ThresholdOperator | null;
  thresholdValue?: number | null;
}

export interface AssumptionWithLinkedConditionsInput {
  statement?: string | null;
  authorship?: Authorship | null;
  linkedConditions?: LinkedCaseConditionInput[];
}

export interface CommitDraftWithReasoningResult {
  decision: DecisionSummaryView;
  decisionContext: DecisionContextView | null;
  draft: DecisionDraftView;
  assumptions: AssumptionView[];
  caseConditions: CaseConditionView[];
}

export async function commitDraftWithReasoning(
  draftId: string,
  input: {
    assumptions?: AssumptionWithLinkedConditionsInput[];
    standaloneCaseConditions?: LinkedCaseConditionInput[];
  } = {},
): Promise<CommitDraftWithReasoningResult> {
  const response = await fetch(`/api/decision-drafts/${draftId}/commit-with-reasoning`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      assumptions: input.assumptions ?? [],
      standaloneCaseConditions: input.standaloneCaseConditions ?? [],
    }),
  });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as CommitDraftWithReasoningResult;
}

export interface ActiveAssumptionRow {
  assumptionId: string;
  decisionId: string;
  caseId: string;
  statement: string | null;
  status: AssumptionStatus;
}

export interface ActiveCaseConditionRow {
  conditionId: string;
  caseId: string;
  decisionId: string | null;
  predicateText: string | null;
  role: CaseConditionRole | null;
  status: CaseConditionStatus;
}

export interface OpenDecisionDraftRow {
  draftId: string;
  caseId: string;
  subject: string | null;
  createdAt: string;
}

export function fetchActiveAssumptions(
  caseId: string,
  signal?: AbortSignal,
): Promise<ActiveAssumptionRow[]> {
  return getJson(`/api/cases/${caseId}/reasoning/active-assumptions`, signal);
}

export function fetchActiveCaseConditions(
  caseId: string,
  signal?: AbortSignal,
): Promise<ActiveCaseConditionRow[]> {
  return getJson(`/api/cases/${caseId}/reasoning/active-case-conditions`, signal);
}

export function fetchOpenDecisionDrafts(
  userId: string,
  signal?: AbortSignal,
): Promise<OpenDecisionDraftRow[]> {
  return getJson(`/api/reasoning/open-decision-drafts?userId=${encodeURIComponent(userId)}`, signal);
}
