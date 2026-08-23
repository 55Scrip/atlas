import { useLocation } from "react-router-dom";

/**
 * Atlas Companion's workspace-context contract (design doc: "Workspace-
 * context contract"; extended by Product Sprint 3, "Companion Coverage
 * Completion", to cover the three Tier 1 routes added after Companion's
 * original design). Purely a pathname read -- `useParams()` is
 * deliberately avoided here since Companion mounts in `AppShell.tsx`,
 * outside the `<Outlet/>` that actually matches routes like
 * `investment-case/:caseId`, and relying on a layout-level component
 * receiving a child route's params is unnecessary risk when a plain
 * pathname match is unambiguous.
 *
 * `workspace` itself is a frontend-only concept -- it decides whether
 * Companion renders at all and which display subject to show, but is
 * never sent to `/api/discovery/chat` (see the design doc's Backend Gaps
 * section for why: the existing endpoint has no notion of "workspace",
 * only of an optional Case).
 *
 * Two route shapes carry an entity identifier: `/investment-case/:caseId`
 * already carries the real backend Case ID directly, so it is exposed as
 * `caseId`. `/portfolio/holding/:ticker` and `/company/:ticker` carry only
 * a ticker -- Case IDs are not derivable from the URL alone for those
 * routes -- so it is exposed as `ticker`, and it is `CompanionPanel`
 * (which already fetches `/api/alpha-portfolio` for the existing
 * caseId-to-ticker display map) that resolves it to a real `caseId`
 * before sending anything to the backend. This hook never fetches --
 * it stays a pure, synchronous function of the pathname alone.
 */
export type CompanionWorkspace =
  | "portfolio"
  | "dailyBrief"
  | "discovery"
  | "history"
  | "dashboard"
  | "investmentCase"
  | "company"
  | "watchlist";

export interface CompanionContext {
  workspace: CompanionWorkspace | null;
  /** Real backend Case ID, known directly from the URL. Only ever set for
   * `investmentCase`. */
  caseId: string | null;
  /** Ticker known directly from the URL, for routes that identify a
   * company but not its Case ID. Only ever set for `portfolio` (the
   * holding-detail route) and `company`. */
  ticker: string | null;
}

const INVESTMENT_CASE_ID = /^\/investment-case\/([^/]+)$/;
const PORTFOLIO_HOLDING_TICKER = /^\/portfolio\/holding\/([^/]+)$/;
const COMPANY_TICKER = /^\/company\/([^/]+)$/;
/** Product Sprint 5 (Discovery Engine v2) -- a candidate detail view is
 * the same kind of context as `/company/:ticker` (a single, ticker-
 * scoped discussion), so it reuses the existing `"company"` workspace
 * rather than a new one. `/discovery/compare` is deliberately NOT given
 * its own match: `CompanionContext` only ever carries one ticker/caseId,
 * so a two-candidate comparison has no honest single-entity value to
 * report -- it falls through to the bare `/discovery` entry below
 * (portfolio-wide), rather than fabricating one candidate as "the"
 * subject. */
const DISCOVERY_CANDIDATE_TICKER = /^\/discovery\/candidate\/([^/]+)$/;

/** Product Sprint 10 (Navigation & Workflow Excellence): `/decisions
 * /:decisionId/workspace` and `/decision-drafts/:draftId/commit` fall
 * through to `workspace: null` below (Companion doesn't render) -- a
 * deliberate gap, not an oversight, so it's named explicitly here
 * rather than silently missing from `WORKSPACE_BY_PATH` the way it was
 * before this sprint. Both routes carry only an opaque `decisionId`/
 * `draftId` in the URL; resolving either to the real Investment Case
 * `caseId` it belongs to needs a lookup this hook cannot make (it
 * fetches nothing, by design -- see the module docstring), and
 * `CompanionPanel`'s own existing ticker->caseId resolution map has no
 * equivalent for decisions. Building one would be a new capability,
 * which this sprint's own rules put out of scope ("prefer improving
 * existing navigation over building anything new"). Both pages now
 * link back to their real Investment Case (Deliverable 3), so the
 * investor is never more than one click from a page where Companion
 * does have real context. */

const WORKSPACE_BY_PATH: Record<string, CompanionWorkspace> = {
  "/portfolio": "portfolio",
  "/daily-brief": "dailyBrief",
  "/discovery": "discovery",
  "/history": "history",
  "/dashboard": "dashboard",
  "/investment-case": "investmentCase",
  "/watchlist": "watchlist",
};

const NO_ENTITY = { caseId: null, ticker: null } as const;

/** Exported separately from the hook so it can be exercised without a
 * Router context -- a pure function of the one input that matters. */
export function resolveCompanionContext(pathname: string): CompanionContext {
  const caseMatch = pathname.match(INVESTMENT_CASE_ID);
  if (caseMatch) {
    return { workspace: "investmentCase", caseId: caseMatch[1]!, ticker: null };
  }
  const holdingMatch = pathname.match(PORTFOLIO_HOLDING_TICKER);
  if (holdingMatch) {
    return { workspace: "portfolio", caseId: null, ticker: holdingMatch[1]! };
  }
  const companyMatch = pathname.match(COMPANY_TICKER);
  if (companyMatch) {
    return { workspace: "company", caseId: null, ticker: companyMatch[1]! };
  }
  const discoveryCandidateMatch = pathname.match(DISCOVERY_CANDIDATE_TICKER);
  if (discoveryCandidateMatch) {
    return { workspace: "company", caseId: null, ticker: discoveryCandidateMatch[1]! };
  }
  if (pathname === "/discovery/compare") {
    return { workspace: "discovery", ...NO_ENTITY };
  }
  return { workspace: WORKSPACE_BY_PATH[pathname] ?? null, ...NO_ENTITY };
}

export function useCompanionContext(): CompanionContext {
  const { pathname } = useLocation();
  return resolveCompanionContext(pathname);
}
