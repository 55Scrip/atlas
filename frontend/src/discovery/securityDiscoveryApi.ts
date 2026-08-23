/**
 * Thin typed client for the existing `GET /api/security-discovery`
 * endpoint (`atlas/alpha/security_discovery/api/router.py`) -- Discovery
 * Engine v2's real candidate-search source (Deliverable 2). This
 * endpoint already existed before this sprint; no frontend page called
 * it. Field names mirror `SecurityCandidateView` exactly (camelCase).
 * Deliberately unranked (no `confidence`/`score` field exists on the
 * backend type at all) -- this client adds none either.
 */

export interface SecurityCandidateView {
  ticker: string;
  displayName: string;
  cik: number | null;
  discoveryMethod: "ticker_exact" | "title_canonical";
  source: string;
  status: "candidate_only";
}

export async function searchSecurities(query: string, signal?: AbortSignal): Promise<SecurityCandidateView[]> {
  const trimmed = query.trim();
  if (trimmed === "") return [];
  const response = await fetch(`/api/security-discovery?query=${encodeURIComponent(trimmed)}`, {
    signal: signal ?? null,
  });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as SecurityCandidateView[];
}
