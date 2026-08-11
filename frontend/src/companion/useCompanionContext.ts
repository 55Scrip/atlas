import { useLocation } from "react-router-dom";

/**
 * Atlas Companion's workspace-context contract (design doc: "Workspace-
 * context contract"). Purely a pathname read -- `useParams()` is
 * deliberately avoided here since Companion mounts in `AppShell.tsx`,
 * outside the `<Outlet/>` that actually matches `investment-case/:caseId`,
 * and relying on a layout-level component receiving a child route's
 * params is unnecessary risk when a plain pathname match is unambiguous.
 *
 * Only two things ever reach the backend: `caseId` (or its absence).
 * `workspace` itself is a frontend-only concept -- it decides whether
 * Companion renders at all and which display subject to show, but is
 * never sent to `/api/discovery/chat` (see the design doc's Backend Gaps
 * section for why: the existing endpoint has no notion of "workspace",
 * only of an optional Case).
 */
export type CompanionWorkspace =
  | "portfolio"
  | "dailyBrief"
  | "discovery"
  | "history"
  | "dashboard"
  | "investmentCase";

export interface CompanionContext {
  workspace: CompanionWorkspace | null;
  caseId: string | null;
}

const INVESTMENT_CASE_ID = /^\/investment-case\/([^/]+)$/;

const WORKSPACE_BY_PATH: Record<string, CompanionWorkspace> = {
  "/portfolio": "portfolio",
  "/daily-brief": "dailyBrief",
  "/discovery": "discovery",
  "/history": "history",
  "/dashboard": "dashboard",
  "/investment-case": "investmentCase",
};

/** Exported separately from the hook so it can be exercised without a
 * Router context -- a pure function of the one input that matters. */
export function resolveCompanionContext(pathname: string): CompanionContext {
  const caseMatch = pathname.match(INVESTMENT_CASE_ID);
  if (caseMatch) {
    return { workspace: "investmentCase", caseId: caseMatch[1]! };
  }
  return { workspace: WORKSPACE_BY_PATH[pathname] ?? null, caseId: null };
}

export function useCompanionContext(): CompanionContext {
  const { pathname } = useLocation();
  return resolveCompanionContext(pathname);
}
