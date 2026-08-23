/**
 * Sprint 9 (ADR-DD-001 Production Implementation): a thin typed client
 * over the DecisionDraft REST API. No derivation, no caching, no
 * state -- every function here is a plain fetch wrapper, directly
 * modeled on `history/securityConfirmationApi.ts`'s own shape. The
 * Decision Workspace form owns its own component state; this module
 * only talks to the backend.
 *
 * Conflict handling (`reviseDecisionDraft`) mirrors
 * `confirmSecuritySelection`'s own pattern: on a 409 (another
 * tab/session revised the same draft since this client last read it),
 * this module does not silently retry or overwrite -- it throws a
 * dedicated `DecisionDraftConflictError` so the caller can re-fetch and
 * decide what to show the investor. See
 * `DecisionDraft-Implementation-Design.md` §7.5.
 */

export type DecisionDraftStatus = "active" | "abandoned" | "committed";

export interface DecisionDraftContentInput {
  decisionType?: string | null;
  subject?: string | null;
  reason?: string | null;
  confidence?: number | null;
  decidedAt?: string | null;
  source?: string | null;
  situation?: string | null;
  portfolioRelevance?: string | null;
  capitalConsiderations?: string | null;
  alternativesConsidered?: string[];
  uncertainties?: string[];
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

export interface DecisionDraftSummaryView {
  draftId: string;
  caseId: string;
  subject: string | null;
  createdAt: string;
}

/** Thrown on a 409 from `reviseDecisionDraft` when `expectedLatestEventId`
 * no longer matches the server's own latest event -- see this module's
 * own docstring. */
export class DecisionDraftConflictError extends Error {
  constructor() {
    super("This draft was updated elsewhere; reload to continue editing.");
    this.name = "DecisionDraftConflictError";
  }
}

export async function createDecisionDraft(
  caseId: string,
  userId: string,
  content: DecisionDraftContentInput = {},
): Promise<DecisionDraftView> {
  const response = await fetch(`/api/cases/${caseId}/decision-drafts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ userId, ...content }),
  });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as DecisionDraftView;
}

export async function listActiveDecisionDrafts(
  caseId: string,
  signal?: AbortSignal,
): Promise<DecisionDraftView[]> {
  const response = await fetch(`/api/cases/${caseId}/decision-drafts`, { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as DecisionDraftView[];
}

export async function fetchDecisionDraft(
  draftId: string,
  signal?: AbortSignal,
): Promise<DecisionDraftView | null> {
  const response = await fetch(`/api/decision-drafts/${draftId}`, { signal: signal ?? null });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as DecisionDraftView;
}

/**
 * On a 409 conflict, throws `DecisionDraftConflictError` rather than
 * silently overwriting or retrying -- the caller should re-fetch via
 * `fetchDecisionDraft` and decide how to show the investor the newer
 * state.
 */
export async function reviseDecisionDraft(
  draftId: string,
  content: DecisionDraftContentInput,
  expectedLatestEventId: string,
): Promise<DecisionDraftView> {
  const response = await fetch(`/api/decision-drafts/${draftId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...content, expectedLatestEventId }),
  });
  if (response.status === 409) throw new DecisionDraftConflictError();
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as DecisionDraftView;
}

/** Idempotent: safe to call even if the draft was already abandoned. */
export async function abandonDecisionDraft(draftId: string): Promise<void> {
  const response = await fetch(`/api/decision-drafts/${draftId}/abandon`, { method: "POST" });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
}

// `commitDecisionDraft` (the plain, no-reasoning commit) removed
// (Product Sprint 12, Deliverable 12 -- Cleanup): fully superseded by
// `reasoningWorkspaceApi.commitDraftWithReasoning`, confirmed zero
// callers anywhere in the frontend before removal.

export async function fetchDailyBriefDraftSummary(
  userId: string,
  signal?: AbortSignal,
): Promise<DecisionDraftSummaryView[]> {
  const response = await fetch(
    `/api/decision-drafts/daily-brief-summary?userId=${encodeURIComponent(userId)}`,
    { signal: signal ?? null },
  );
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as DecisionDraftSummaryView[];
}
