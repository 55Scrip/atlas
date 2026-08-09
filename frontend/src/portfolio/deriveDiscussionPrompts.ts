/**
 * Portfolio Workspace v3 (Sprint 1): a pure, side-effect-free derivation
 * over data `PortfolioPage.tsx` already fetches — the same discipline
 * `derivePortfolioActions.ts` established for Today's Priorities. This
 * module produces "Today's Discussions" conversation starters: short,
 * specific questions Atlas can ask the investor about their own
 * portfolio, each one traceable to a real, already-computed fact
 * (a `KeyFinding`, the portfolio's own `concentrationLevel`, or the
 * single highest-priority `PortfolioAction`) — never a generic or
 * fabricated example. No new backend call, no new domain concept.
 *
 * Per this sprint's explicit instruction, this only builds the
 * placeholder *generation* of discussion prompts — not the
 * conversational engine itself. Each prompt is a static question string
 * plus enough identity (`kind`, `ticker`) for a future engine to use as
 * a starting context; today, "Discuss" only pre-fills the free-text
 * input `PortfolioPage.tsx` renders beneath these prompts.
 */

export type DiscussionPromptKind =
  | "priority_holding"
  | "diversification"
  | "concentration"
  | "unallocated"
  | "evidence_gaps"
  | "stale_cases"
  | "missing_cases";

export interface DiscussionPrompt {
  id: string;
  kind: DiscussionPromptKind;
  text: string;
  ticker: string | null;
}

export interface KeyFindingLite {
  kind:
    | "high_concentration"
    | "elevated_concentration"
    | "large_unallocated"
    | "multiple_missing_cases"
    | "multiple_stale_cases"
    | "multiple_evidence_gaps";
  count: number;
  tickers: string[];
}

export interface TopActionLite {
  ticker: string | null;
}

const MAX_DISCUSSION_PROMPTS = 3;

/**
 * `t` is passed in (rather than translating internally) so this module
 * stays a plain data transform, consistent with `derivePortfolioActions`
 * returning untranslated data for the component layer to render — here
 * the "translated" value is the finished prompt text itself, produced by
 * calling the same `t()` the caller already has, once per candidate.
 */
export function deriveDiscussionPrompts(
  unallocatedPercent: number | null,
  concentrationLevel: string | null,
  holdingsCount: number,
  keyFindings: KeyFindingLite[],
  topAction: TopActionLite | null,
  t: (key: string, params?: Record<string, string | number>) => string,
): DiscussionPrompt[] {
  const candidates: DiscussionPrompt[] = [];

  if (topAction?.ticker) {
    candidates.push({
      id: `priority_holding:${topAction.ticker}`,
      kind: "priority_holding",
      text: t("portfolio.discussions.prompt.priorityHolding", { ticker: topAction.ticker }),
      ticker: topAction.ticker,
    });
  }

  const concentrationFinding = keyFindings.find(
    (finding) => finding.kind === "high_concentration" || finding.kind === "elevated_concentration",
  );
  if (concentrationFinding && concentrationFinding.tickers[0]) {
    candidates.push({
      id: `concentration:${concentrationFinding.tickers[0]}`,
      kind: "concentration",
      text: t("portfolio.discussions.prompt.concentration", { ticker: concentrationFinding.tickers[0] }),
      ticker: concentrationFinding.tickers[0],
    });
  } else if (concentrationLevel === "Low" && holdingsCount > 0) {
    candidates.push({
      id: "diversification",
      kind: "diversification",
      text: t("portfolio.discussions.prompt.diversification", { count: holdingsCount }),
      ticker: null,
    });
  }

  const unallocatedFinding = keyFindings.find((finding) => finding.kind === "large_unallocated");
  if (unallocatedFinding && unallocatedPercent !== null) {
    candidates.push({
      id: "unallocated",
      kind: "unallocated",
      text: t("portfolio.discussions.prompt.unallocated", { percent: unallocatedPercent }),
      ticker: null,
    });
  }

  const evidenceGapsFinding = keyFindings.find((finding) => finding.kind === "multiple_evidence_gaps");
  if (evidenceGapsFinding) {
    candidates.push({
      id: "evidence_gaps",
      kind: "evidence_gaps",
      text: t("portfolio.discussions.prompt.evidenceGaps", { count: evidenceGapsFinding.count }),
      ticker: null,
    });
  }

  const staleCasesFinding = keyFindings.find((finding) => finding.kind === "multiple_stale_cases");
  if (staleCasesFinding) {
    candidates.push({
      id: "stale_cases",
      kind: "stale_cases",
      text: t("portfolio.discussions.prompt.staleCases", { count: staleCasesFinding.count }),
      ticker: null,
    });
  }

  const missingCasesFinding = keyFindings.find((finding) => finding.kind === "multiple_missing_cases");
  if (missingCasesFinding) {
    candidates.push({
      id: "missing_cases",
      kind: "missing_cases",
      text: t("portfolio.discussions.prompt.missingCases", { count: missingCasesFinding.count }),
      ticker: null,
    });
  }

  return candidates.slice(0, MAX_DISCUSSION_PROMPTS);
}
