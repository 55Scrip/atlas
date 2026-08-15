/**
 * Sprint 21 (Explicit Security Confirmation -- First Product Flow): a
 * thin typed client over Sprint 19's read-only `GET /security-discovery`
 * and Sprint 20's `GET`/`POST /decisions/{id}/security-confirmation`.
 * No derivation, no caching, no state -- every function here is a plain
 * fetch wrapper; `HistoryPage.tsx`'s own component state owns the
 * per-Decision confirmation/discovery flow.
 *
 * `fetchSecurityConfirmation` treats a 404 as "no confirmation recorded
 * yet" (returns `null`), not an error -- that is Sprint 20's own
 * documented not-found semantics for an unconfirmed Decision, never a
 * failure.
 *
 * Sprint 22 (Correction, Revocation & Historical Integrity) adds
 * `correctSecuritySelection` and `revokeSecurityConfirmation` over the
 * new `POST .../correct` and `POST .../revoke` endpoints. Neither ever
 * implies the earlier confirmation stopped having happened -- see
 * `atlas.alpha.security_confirmation.models.SecurityConfirmationEvent`'s
 * own docstring for the backend ontology this mirrors.
 */

export type SecurityDiscoveryMethod = "ticker_exact" | "title_canonical";

export interface SecurityCandidateView {
  ticker: string;
  displayName: string;
  cik: number | null;
  discoveryMethod: SecurityDiscoveryMethod;
  source: string;
  status: "candidate_only";
}

export interface ConfirmedSecuritySelectionView {
  id: string;
  decisionId: string;
  confirmedTicker: string;
  confirmedDisplayName: string;
  confirmedCik: number | null;
  discoveryMethod: string;
  discoverySource: string;
  confirmedAt: string;
}

export async function fetchSecurityConfirmation(
  decisionId: string,
  signal?: AbortSignal,
): Promise<ConfirmedSecuritySelectionView | null> {
  const response = await fetch(`/api/decisions/${decisionId}/security-confirmation`, { signal: signal ?? null });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as ConfirmedSecuritySelectionView;
}

export async function fetchSecurityDiscoveryCandidates(
  query: string,
  signal?: AbortSignal,
): Promise<SecurityCandidateView[]> {
  const response = await fetch(`/api/security-discovery?query=${encodeURIComponent(query)}`, { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as SecurityCandidateView[];
}

/**
 * First-confirmation only -- a different ticker while one is already
 * active is a 409 conflict, never an implicit correction (unchanged
 * since Sprint 20; use `correctSecuritySelection` for an explicit
 * change). On a 409 (someone already confirmed a different ticker for
 * this Decision -- e.g. a second tab), self-heals by re-reading the
 * real persisted confirmation rather than surfacing a raw conflict
 * error.
 */
export async function confirmSecuritySelection(
  decisionId: string,
  candidate: SecurityCandidateView,
): Promise<ConfirmedSecuritySelectionView> {
  const response = await fetch(`/api/decisions/${decisionId}/security-confirmation`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ticker: candidate.ticker,
      displayName: candidate.displayName,
      cik: candidate.cik,
      discoveryMethod: candidate.discoveryMethod,
      source: candidate.source,
    }),
  });
  if (response.status === 409) {
    const existing = await fetchSecurityConfirmation(decisionId);
    if (existing) return existing;
    throw new Error(`Backend responded with ${response.status}`);
  }
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as ConfirmedSecuritySelectionView;
}

/**
 * Requires a current confirmation to exist -- calling this on an
 * unconfirmed Decision fails with a 404, by design (see
 * `service.correct`'s own docstring: "correct" means "change an
 * existing one," never "create a new one").
 */
export async function correctSecuritySelection(
  decisionId: string,
  candidate: SecurityCandidateView,
): Promise<ConfirmedSecuritySelectionView> {
  const response = await fetch(`/api/decisions/${decisionId}/security-confirmation/correct`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ticker: candidate.ticker,
      displayName: candidate.displayName,
      cik: candidate.cik,
      discoveryMethod: candidate.discoveryMethod,
      source: candidate.source,
    }),
  });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as ConfirmedSecuritySelectionView;
}

/** Idempotent: a 204 is returned whether or not a confirmation was
 * actually active to revoke. */
export async function revokeSecurityConfirmation(decisionId: string): Promise<void> {
  const response = await fetch(`/api/decisions/${decisionId}/security-confirmation/revoke`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
}
