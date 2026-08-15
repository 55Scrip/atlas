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
 * On a 409 (someone already confirmed a different ticker for this
 * Decision -- e.g. a second tab), self-heals by re-reading the real
 * persisted confirmation rather than surfacing a raw conflict error;
 * Sprint 21 deliberately has no correction/revocation UI, so the only
 * honest response to a conflict is to show whatever is actually
 * recorded.
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
