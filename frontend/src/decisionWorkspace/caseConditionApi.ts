/**
 * Sprint 13: a thin typed client over Sprint 10's CaseCondition API
 * (`atlas/core/infrastructure/api/case_condition/`). Covers exactly
 * the four actions Sprint 13 §4 names for the UI (create, revise,
 * evaluate, retire) -- `supersede` exists on the backend but has no UI
 * surface this sprint, so no client function for it is added here.
 */
import type {
  Authorship,
  CaseConditionRole,
  CaseConditionView,
  ThresholdOperator,
} from "./reasoningWorkspaceApi";

async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export interface CaseConditionContentInput {
  predicateText?: string | null;
  role?: CaseConditionRole | null;
  authorship?: Authorship | null;
  structuredKind?: "date" | "threshold" | null;
  thresholdDate?: string | null;
  thresholdMetric?: string | null;
  thresholdOperator?: ThresholdOperator | null;
  thresholdValue?: number | null;
}

export function createCaseCondition(
  caseId: string,
  content: CaseConditionContentInput & { decisionId?: string | null },
): Promise<CaseConditionView> {
  return requestJson(`/api/cases/${caseId}/case-conditions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(content),
  });
}

export function reviseCaseCondition(
  conditionId: string,
  content: CaseConditionContentInput,
): Promise<CaseConditionView> {
  return requestJson(`/api/case-conditions/${conditionId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(content),
  });
}

export interface EvaluateCaseConditionResult {
  satisfied: boolean;
  transitioned: boolean;
  condition: CaseConditionView;
}

export function evaluateCaseCondition(
  conditionId: string,
  input: {
    evaluatedAt?: string | null;
    observedValue?: number | null;
    humanAssertedSatisfied?: boolean | null;
  } = {},
): Promise<EvaluateCaseConditionResult> {
  return requestJson(`/api/case-conditions/${conditionId}/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

/** Idempotent: safe to call even if the condition was already retired. */
export async function retireCaseCondition(conditionId: string): Promise<void> {
  const response = await fetch(`/api/case-conditions/${conditionId}/retire`, { method: "POST" });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
}
