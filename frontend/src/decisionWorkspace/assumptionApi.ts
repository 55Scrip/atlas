/**
 * Sprint 13: a thin typed client over Sprint 11's Assumption API
 * (`atlas/core/infrastructure/api/assumption/`). Covers exactly the
 * four actions Sprint 13 §3 names for the UI (create, revise,
 * challenge, retire) -- `supersede`/`attach`/`detach` exist on the
 * backend but have no UI surface this sprint, so no client function
 * for them is added here (adding an unused function would be dead
 * code, not "reuse").
 */
import type { Authorship, AssumptionView } from "./reasoningWorkspaceApi";

async function requestJson<T>(
  path: string,
  init: RequestInit,
): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as T;
}

export function createAssumption(
  decisionId: string,
  content: { statement?: string | null; authorship?: Authorship | null },
): Promise<AssumptionView> {
  return requestJson(`/api/decisions/${decisionId}/assumptions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(content),
  });
}

export function reviseAssumption(
  assumptionId: string,
  content: { statement?: string | null; authorship?: Authorship | null },
): Promise<AssumptionView> {
  return requestJson(`/api/assumptions/${assumptionId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(content),
  });
}

export function challengeAssumption(
  assumptionId: string,
  input: { evidenceId?: string | null; note?: string | null; severity?: "challenged" | "invalidated" },
): Promise<AssumptionView> {
  return requestJson(`/api/assumptions/${assumptionId}/challenge`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

/** Idempotent: safe to call even if the assumption was already retired. */
export async function retireAssumption(assumptionId: string): Promise<void> {
  const response = await fetch(`/api/assumptions/${assumptionId}/retire`, { method: "POST" });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
}
