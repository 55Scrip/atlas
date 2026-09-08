import type { AnalysisCoverageLevel, DecisionSupportLevel, StanceLevel } from "../status/statusTone";
import type { FitRating } from "../portfolioFit/portfolioFitApi";

/**
 * The Discovery candidate universe
 * (`GET /api/discovery-candidates`) and direct Case entry
 * (`POST /api/case-identity/ensure`).
 *
 * Discovery used to build its candidates from the Watchlist minus
 * Portfolio holdings, so the only ideas it could show were ones the
 * investor had already found and added. The backend now answers the
 * question from the other side: securities Atlas has analysed that the
 * investor is *not* already following.
 *
 * Canonical enum values on the wire, never rendered text. `fitRating`
 * and `stanceLevel` are nullable because "the engine could not
 * evaluate this" is a real answer, not a middling one.
 */
export interface DiscoveryCandidateView {
  ticker: string;
  caseId: string;
  companyName: string | null;
  decisionSupportLevel: DecisionSupportLevel;
  analysisCoverageLevel: AnalysisCoverageLevel;
  fitRating: FitRating | null;
  stanceLevel: StanceLevel | null;
}

export async function fetchDiscoveryCandidates(signal?: AbortSignal): Promise<DiscoveryCandidateView[]> {
  const response = await fetch("/api/discovery-candidates", { signal: signal ?? null });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  return (await response.json()) as DiscoveryCandidateView[];
}

/**
 * Resolve the Investment Case for a security, creating it if Atlas has
 * none yet. Reuses an existing Case, so repeated opens never
 * duplicate, and creates no Watchlist membership, no Portfolio
 * holding and no Decision Memory event -- opening a Case is now just
 * opening a Case.
 */
export async function ensureCaseForTicker(ticker: string, signal?: AbortSignal): Promise<string> {
  const response = await fetch("/api/case-identity/ensure", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker }),
    signal: signal ?? null,
  });
  if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
  const body = (await response.json()) as { caseId: string };
  return body.caseId;
}
