import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { useNavigate, Link as RouterLink } from "react-router-dom";
import { ACCENT_LINK_STYLE, Button, Container, Divider, Heading, Inline, Label, Link, Stack, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import { DiscoveryCandidateCard } from "../discovery/DiscoveryCandidateCard";
import { groupCandidatesByTier } from "../discovery/groupCandidatesByTier";
import { searchSecurities, type SecurityCandidateView } from "../discovery/securityDiscoveryApi";
import {
  getAlphaWatchlistSnapshot,
  removeTickerFromWatchlist,
  setAlphaWatchlistData,
  useAlphaWatchlist,
  type WatchlistEntryView,
} from "../discovery/watchlistActions";
import { useAlphaPortfolio } from "../portfolio/alphaPortfolioData";
import {
  deriveActivity,
  sortActivity,
  formatRelativeTime,
  type DecisionRecord,
  type OutcomeRecord,
  type TradeLogEntry,
  type ActivityEvent,
} from "../activity/deriveActivity";
import { fetchDailyBriefAgenda, type AgendaItemView } from "../dailyBriefAgenda/dailyBriefAgendaApi";
import { FitBadge } from "../portfolioFit/FitBadge";
import {
  fetchPortfolioFitForCandidates,
  fetchPortfolioFitForHoldings,
  type FitRating,
  type PortfolioFitAssessmentView,
} from "../portfolioFit/portfolioFitApi";
import { NO_PRIORITY_RANK, PRIORITY_LEVEL_RANK, type PriorityLevel } from "../status/statusTone";
import { fetchStanceForCandidates, type TickerStanceView } from "../stance/stanceApi";

const FIT_RANK: Record<FitRating, number> = { excellent: 0, good: 1, neutral: 2, weak: 3, poor: 4, unavailable: 5 };
const RECENT_ACTIVITY_COUNT = 4;

/** Cross-Workspace Consistency Cleanup -- same uppercase small-caps
 * workspace-label treatment Portfolio's own `PAGE_TITLE_STYLE`
 * established, so every top-level workspace (Portfolio, Daily Brief,
 * Discovery, History) shares one page-title visual language. */
const PAGE_TITLE_STYLE: CSSProperties = {
  fontFamily: "var(--type-family-prose)",
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.02em",
};

interface HoldingLite {
  ticker: string;
  caseId: string | null;
}
interface PortfolioView {
  exists: boolean;
  holdings: HoldingLite[];
}
type PortfolioStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; view: PortfolioView };
type WatchlistStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; entries: WatchlistEntryView[] };
type CandidateFitStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; assessments: PortfolioFitAssessmentView[] };
type StanceCandidatesStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; entries: TickerStanceView[] };
type SearchStatus =
  | { kind: "idle" }
  | { kind: "searching" }
  | { kind: "error" }
  | { kind: "loaded"; query: string; results: SecurityCandidateView[] };
/** Product Sprint 9 (Discovery Excellence, Deliverable 3) -- the same
 * shared `/api/daily-brief-agenda` fetch Portfolio and Daily Brief
 * itself read, filtered to `group === "watchlist"` (the group the
 * engine assigns to a non-holding ticker's signals -- see
 * `atlas/alpha/daily_brief_agenda/engine.py::_item_for_ticker`). A
 * presentation-only filter: zero priority/relevance logic lives on this
 * page, only a display filter, the exact same pattern Portfolio's own
 * "Attention Required" section established. */
type DailyBriefAgendaFetchStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; items: AgendaItemView[] };
/** Deliverable 2 (hierarchy, position 5) -- reuses `deriveActivity`
 * unfiltered (the same three endpoints Portfolio already fetches this
 * way), then keeps only events whose Case belongs to a current
 * Watchlist entry -- a genuinely different slice from Portfolio's own
 * Recent Activity (holdings-scoped), not a duplicate of it. */
type RecentActivityFetchStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; decisions: DecisionRecord[]; outcomes: OutcomeRecord[]; trades: TradeLogEntry[] };

/**
 * Discovery Engine v2 (Product Sprint 5) -- rebuilt around this
 * sprint's own mission: "what should I look at next, given what I
 * already own?" not "what stocks exist?"
 *
 * Deliverable 9's suggested sections, implemented as real, independent
 * data sources, none duplicating another:
 * 1. Candidates for Your Portfolio -- the one canonical candidate
 *    presentation (Atlas UX Phase 7B, Phase 2), tiered by Portfolio Fit
 *    (`/api/portfolio-fit/candidates` + `/api/portfolio-fit/holdings`
 *    for Watchlist entries that are also held). Previously two separate
 *    sections -- these same tiered cards, plus a second compact table
 *    below reusing the full `/api/alpha-watchlist` roster -- rendered
 *    the same ~11 tickers twice on one page (confirmed live). The full
 *    roster is now folded into this one list: every Watchlist entry
 *    appears exactly once, tiered when a real Fit assessment exists,
 *    or listed afterward via the card's own honest "fit pending"/"no
 *    Case yet" state when it doesn't.
 * 2. Compare -- an entry point into `/discovery/compare`
 *    (Deliverable 5/6).
 * 3. Search / Review a Company -- `atlas.alpha.security_discovery`
 *    (Deliverable 2), the one real candidate-search capability in this
 *    codebase.
 * 4. Recent Activity -- Decision/Outcome/Trade events scoped to
 *    Watchlist Cases (Deliverable 2).
 *
 * "What Atlas Found" (the old Daily-Brief-re-slice of *existing
 * holdings'* changes) is deliberately removed: that fact already has a
 * home (Daily Brief itself) and does not answer this page's own
 * candidate-discovery mission -- keeping it here would have been
 * exactly the "unnecessary section merely because data exists"
 * Deliverable 9 warns against. A link to Daily Brief replaces it so
 * that fact stays reachable, not lost.
 */
export function DiscoveryPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const portfolioResource = useAlphaPortfolio();
  const portfolioStatus: PortfolioStatus =
    portfolioResource.kind === "loaded" ? { kind: "loaded", view: portfolioResource.data as PortfolioView } : portfolioResource;
  const watchlistResource = useAlphaWatchlist();
  const watchlistStatus: WatchlistStatus = watchlistResource;
  const [candidateFitStatus, setCandidateFitStatus] = useState<CandidateFitStatus>({ kind: "loading" });
  /** Live-verification finding (Deliverable 14): a Watchlist entry that
   * is *also* a Portfolio holding (e.g. AAPL, MSFT) never appears in
   * `/api/portfolio-fit/candidates` (that endpoint deliberately excludes
   * held tickers -- "a candidate is not interesting merely because it's
   * a good company," it's already owned). Its real Fit still exists via
   * `/api/portfolio-fit/holdings` -- fetched here too so the Watchlist
   * Candidates section's badge is accurate for every entry, not just
   * the watchlist-only ones. */
  const [holdingsFitStatus, setHoldingsFitStatus] = useState<CandidateFitStatus>({ kind: "loading" });
  /** Atlas Intelligence Sprint 2 (Recommendation Quality &
   * Actionability, Deliverable 7). */
  const [stanceCandidatesStatus, setStanceCandidatesStatus] = useState<StanceCandidatesStatus>({ kind: "loading" });
  const [dailyBriefAgenda, setDailyBriefAgenda] = useState<DailyBriefAgendaFetchStatus>({ kind: "loading" });
  const [recentActivity, setRecentActivity] = useState<RecentActivityFetchStatus>({ kind: "loading" });
  const [searchQuery, setSearchQuery] = useState("");
  const [searchStatus, setSearchStatus] = useState<SearchStatus>({ kind: "idle" });

  useEffect(() => {
    const controller = new AbortController();
    fetchPortfolioFitForCandidates(controller.signal)
      .then((assessments) => setCandidateFitStatus({ kind: "loaded", assessments }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setCandidateFitStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchStanceForCandidates(controller.signal)
      .then((entries) => setStanceCandidatesStatus({ kind: "loaded", entries }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStanceCandidatesStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchPortfolioFitForHoldings(controller.signal)
      .then((assessments) => setHoldingsFitStatus({ kind: "loaded", assessments }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setHoldingsFitStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchDailyBriefAgenda(controller.signal)
      .then((agenda) => setDailyBriefAgenda({ kind: "loaded", items: agenda.items.filter((item) => item.group === "watchlist") }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDailyBriefAgenda({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      fetch("/api/decisions", { signal: controller.signal }).then((r) => {
        if (!r.ok) throw new Error(`Backend responded with ${r.status}`);
        return r.json() as Promise<DecisionRecord[]>;
      }),
      fetch("/api/outcomes", { signal: controller.signal }).then((r) => {
        if (!r.ok) throw new Error(`Backend responded with ${r.status}`);
        return r.json() as Promise<OutcomeRecord[]>;
      }),
      fetch("/api/alpha-portfolio/trade-log", { signal: controller.signal }).then((r) => {
        if (!r.ok) throw new Error(`Backend responded with ${r.status}`);
        return r.json() as Promise<TradeLogEntry[]>;
      }),
    ])
      .then(([decisions, outcomes, trades]) => setRecentActivity({ kind: "loaded", decisions, outcomes, trades }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setRecentActivity({ kind: "error" });
      });
    return () => controller.abort();
  }, []);

  function submitSearch() {
    const query = searchQuery.trim();
    if (query === "") return;
    setSearchStatus({ kind: "searching" });
    searchSecurities(query)
      .then((results) => setSearchStatus({ kind: "loaded", query, results }))
      .catch(() => setSearchStatus({ kind: "error" }));
  }

  function openCandidate(ticker: string) {
    navigate(`/discovery/candidate/${encodeURIComponent(ticker)}`);
  }

  function removeFromWatchlist(ticker: string) {
    if (watchlistStatus.kind !== "loaded") return;
    const removedEntry = watchlistStatus.entries.find((e) => e.ticker === ticker);
    if (!removedEntry) return;
    // Product Sprint 9 (Discovery Excellence): reuses the same
    // `removeTickerFromWatchlist` helper `CandidateDetailPage.tsx`
    // already uses (`watchlistActions.ts`) instead of a second,
    // separately-implemented DELETE call -- the prior version here had
    // a real bug where its own "revert on failure" spread the already-
    // filtered array back into state instead of restoring the removed
    // entry, silently leaving the UI showing a ticker as removed even
    // when the backend DELETE had failed.
    //
    // Internal Alpha Stabilization 1 (navigation/cache fix): the
    // optimistic update now writes through the shared cache
    // (`setAlphaWatchlistData`), not local state, so every other open
    // consumer of the Watchlist (e.g. `WatchlistPage` in another tab
    // navigation) sees the same instant removal, not just this page.
    setAlphaWatchlistData(watchlistStatus.entries.filter((e) => e.ticker !== ticker));
    removeTickerFromWatchlist(ticker).then((ok) => {
      if (ok) return;
      const current = getAlphaWatchlistSnapshot();
      if (current.kind === "loaded" && !current.entries.some((e) => e.ticker === ticker)) {
        setAlphaWatchlistData([...current.entries, removedEntry]);
      }
    });
  }

  const heldTickers = new Set(portfolioStatus.kind === "loaded" ? portfolioStatus.view.holdings.map((h) => h.ticker) : []);
  const watchlistTickers = new Set(watchlistStatus.kind === "loaded" ? watchlistStatus.entries.map((e) => e.ticker) : []);
  const candidateFitByTicker = new Map(
    candidateFitStatus.kind === "loaded" ? candidateFitStatus.assessments.map((a) => [a.ticker, a]) : [],
  );
  // Watchlist Candidates' own fit lookup: candidates (watchlist-only)
  // plus holdings (watchlist entries that are also held) -- see
  // `holdingsFitStatus`'s own comment for why both are needed.
  const anyFitByTicker = new Map([
    ...candidateFitByTicker,
    ...(holdingsFitStatus.kind === "loaded" ? holdingsFitStatus.assessments.map((a): [string, PortfolioFitAssessmentView] => [a.ticker, a]) : []),
  ]);
  /** Deliverable 3 -- ticker -> the one real Agenda item explaining why
   * this exact candidate currently matters, sourced from the shared
   * Daily Brief Agenda (already filtered to `group === "watchlist"`). */
  const agendaByTicker = new Map<string, AgendaItemView>();
  if (dailyBriefAgenda.kind === "loaded") {
    for (const item of dailyBriefAgenda.items) {
      if (item.ticker) agendaByTicker.set(item.ticker, item);
    }
  }
  const priorityByTicker = new Map<string, PriorityLevel>();
  for (const [ticker, item] of agendaByTicker) {
    priorityByTicker.set(ticker, item.priority);
  }
  /** Atlas Intelligence Sprint 2 (Recommendation Quality &
   * Actionability, Deliverable 7). */
  const stanceByTicker = new Map(
    stanceCandidatesStatus.kind === "loaded" ? stanceCandidatesStatus.entries.map((e) => [e.ticker, e.stance]) : [],
  );
  /** Deliverable 9 -- the candidate list's own real ordering signals:
   * Agenda priority first, then Fit rating, then ticker -- never a
   * numeric score, and two candidates with neither signal remain a tie
   * broken only alphabetically. */
  const orderedWatchlistEntries =
    watchlistStatus.kind === "loaded"
      ? [...watchlistStatus.entries].sort((a, b) => {
          const priorityRank = (t: string) => {
            const p = priorityByTicker.get(t);
            return p ? PRIORITY_LEVEL_RANK[p] : NO_PRIORITY_RANK;
          };
          const rankDiff = priorityRank(b.ticker) - priorityRank(a.ticker);
          if (rankDiff !== 0) return rankDiff;
          const fitRank = (t: string) => {
            const fit = anyFitByTicker.get(t)?.overall;
            return fit ? FIT_RANK[fit] : 6;
          };
          const fitDiff = fitRank(a.ticker) - fitRank(b.ticker);
          if (fitDiff !== 0) return fitDiff;
          return a.ticker.localeCompare(b.ticker);
        })
      : [];

  /** Atlas UX Phase 7B, Phase 2 -- previously two independent sections
   * rendered the same watchlist roster twice: full cards here (sourced
   * only from `/api/portfolio-fit/candidates`, which excludes held
   * tickers) and a second, compact table below (the full
   * `/api/alpha-watchlist` roster). Confirmed live: the same ~11
   * tickers appeared in both. This is now the one canonical
   * presentation, tiered by Fit exactly as before, but built from
   * `anyFitByTicker` (candidates + held watchlist entries together --
   * the same union the old compact table's own badge lookup already
   * used) so no entry is lost. A watchlist entry with no Fit assessment
   * at all yet (freshly added, still evaluating) is neither dropped nor
   * given a fabricated tier -- it renders after the tiers via the
   * card's own real "fit pending"/"no Case yet" state. */
  const allAssessments = Array.from(anyFitByTicker.values()).filter((a) => watchlistTickers.has(a.ticker));
  const tiers = groupCandidatesByTier(allAssessments, priorityByTicker);
  const assessedTickers = new Set(allAssessments.map((a) => a.ticker));
  const unassessedWatchlistEntries = orderedWatchlistEntries.filter((entry) => !assessedTickers.has(entry.ticker));

  /** Deliverable 6 (Portfolio Context) -- "which holding is most
   * relevant to compare against?" The same already-computed fact
   * `CompareCandidatesPage.tsx`'s own "vs weakest holding" quick pick
   * uses (`/api/portfolio-fit/holdings` is already sorted best-first
   * server-side, so the last evaluated entry is the weakest) -- reused
   * here to pre-fill Compare's `b` param rather than recomputed. */
  const evaluatedHoldings =
    holdingsFitStatus.kind === "loaded" ? holdingsFitStatus.assessments.filter((a) => a.overall !== "unavailable") : [];
  const weakestHoldingTicker = evaluatedHoldings.length > 0 ? evaluatedHoldings[evaluatedHoldings.length - 1]!.ticker : null;

  function compareHref(ticker: string): string {
    const params = new URLSearchParams({ a: ticker });
    if (weakestHoldingTicker && weakestHoldingTicker !== ticker) params.set("b", weakestHoldingTicker);
    return `/discovery/compare?${params.toString()}`;
  }

  const watchlistCaseIds = new Set(watchlistStatus.kind === "loaded" ? watchlistStatus.entries.map((e) => e.caseId) : []);
  const watchlistActivity =
    recentActivity.kind === "loaded"
      ? sortActivity(
          deriveActivity(
            recentActivity.decisions,
            recentActivity.outcomes,
            recentActivity.trades,
            watchlistStatus.kind === "loaded"
              ? watchlistStatus.entries.map((e) => ({ ticker: e.ticker, caseId: e.caseId, reconciliationStatus: "NONE" as const }))
              : [],
          ).filter((event) => event.caseId !== null && watchlistCaseIds.has(event.caseId)),
          "newest",
        ).slice(0, RECENT_ACTIVITY_COUNT)
      : [];

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        <Heading level={3} style={PAGE_TITLE_STYLE}>
          {t("discovery.title")}
        </Heading>
        <Text color="secondary">{t("discovery.workingOnBehalf")}</Text>
        <Text color="tertiary" as="p">
          {t("discovery.dailyBriefPointer")}{" "}
          <RouterLink to="/daily-brief" style={ACCENT_LINK_STYLE}>
            {t("discovery.dailyBriefPointerLink")}
          </RouterLink>
        </Text>

        <Divider tone="hairline" />

        {/* Product Sprint 9 (Discovery Excellence, Deliverable 2):
            reordered to lead with the highest-value opportunities --
            "what should I investigate?" is this page's first question,
            and a utility like Search answers a narrower one ("does
            Atlas already know about ticker X?"), so it now sits after
            the three real discovery surfaces rather than before them. */}

        {/* 1. Candidates for Your Portfolio -- ranked by Portfolio Fit,
            grouped by tier (Deliverable 3: ties shown as ties), with
            Agenda-flagged candidates surfaced first within a tier
            (Deliverable 9). Atlas UX Phase 7B, Phase 2: this is now the
            one canonical candidate presentation -- the entries formerly
            duplicated in a second "Watchlist Candidates" table below
            are shown here once, and once only. */}
        <Stack gap="metadata">
          <Label>{t("discovery.candidatesForPortfolio.heading")}</Label>
          {/* Internal Alpha Stabilization: this section previously
              rendered nothing at all while loading -- visually
              indistinguishable from "genuinely empty" until the fetch
              resolved. Reuses the same loading copy Portfolio Fit
              already uses everywhere else in the app. */}
          {(candidateFitStatus.kind === "loading" || watchlistStatus.kind === "loading") && (
            <Text role="status" aria-live="polite">
              {t("portfolioFit.section.loading")}
            </Text>
          )}
          {candidateFitStatus.kind === "error" && (
            <Text color="tertiary" role="alert">
              {t("discovery.candidatesForPortfolio.loadError")}
            </Text>
          )}
          {watchlistStatus.kind === "loaded" && watchlistStatus.entries.length === 0 && (
            <Text color="tertiary">{t("discovery.watchlistCandidates.empty")}</Text>
          )}
          {tiers.map((tier) => (
            <Stack key={tier.rating} gap="metadata">
              <Inline gap="row" align="center">
                <FitBadge rating={tier.rating} />
                <Text color="tertiary" as="span">
                  {t(
                    tier.candidates.length === 1
                      ? "discovery.candidatesForPortfolio.tierCountOne"
                      : "discovery.candidatesForPortfolio.tierCountOther",
                    { count: tier.candidates.length },
                  )}
                </Text>
              </Inline>
              {tier.candidates.map((assessment) => {
                const isHolding = heldTickers.has(assessment.ticker);
                return (
                  <DiscoveryCandidateCard
                    key={assessment.caseId}
                    ticker={assessment.ticker}
                    reasonKey={isHolding ? "discovery.card.reason.holding" : "discovery.card.reason.watchlist"}
                    agendaHeadline={agendaByTicker.get(assessment.ticker)?.headline ?? null}
                    assessment={assessment}
                    stance={stanceByTicker.get(assessment.ticker) ?? null}
                    isOnWatchlist={true}
                    isHolding={isHolding}
                    variant="compact"
                    onOpenCase={() =>
                      navigate(`/investment-case/${assessment.caseId}`, { state: { origin: "discovery", ticker: assessment.ticker } })
                    }
                    onRemoveFromWatchlist={() => removeFromWatchlist(assessment.ticker)}
                    onCompare={() => navigate(compareHref(assessment.ticker))}
                  />
                );
              })}
            </Stack>
          ))}
          {unassessedWatchlistEntries.length > 0 && (
            <Stack gap="metadata">
              {unassessedWatchlistEntries.map((entry) => (
                <DiscoveryCandidateCard
                  key={entry.ticker}
                  ticker={entry.ticker}
                  reasonKey={heldTickers.has(entry.ticker) ? "discovery.card.reason.holding" : "discovery.card.reason.watchlist"}
                  agendaHeadline={agendaByTicker.get(entry.ticker)?.headline ?? null}
                  assessment={null}
                  stance={stanceByTicker.get(entry.ticker) ?? null}
                  isOnWatchlist={true}
                  isHolding={heldTickers.has(entry.ticker)}
                  variant="compact"
                  onOpenCase={() => navigate(`/investment-case/${entry.caseId}`, { state: { origin: "discovery", ticker: entry.ticker } })}
                  onRemoveFromWatchlist={() => removeFromWatchlist(entry.ticker)}
                  onCompare={() => navigate(compareHref(entry.ticker))}
                />
              ))}
            </Stack>
          )}
        </Stack>

        <Divider tone="hairline" />

        {/* 2. Compare -- entry point into `/discovery/compare`
            (Deliverable 5/6); the page itself discloses "no candidate
            selected" honestly when reached with no `?a=`. */}
        <Stack gap="metadata">
          <Label>{t("discovery.compareSection.heading")}</Label>
          <Text color="tertiary" as="p">
            {t("discovery.compareSection.explanation")}
          </Text>
          <RouterLink to="/discovery/compare" style={ACCENT_LINK_STYLE}>
            {t("discovery.compareSection.openButton")}
          </RouterLink>
        </Stack>

        <Divider tone="hairline" />

        {/* 3. Search / Review a Company -- real `security_discovery`
            search. Deliverable 7: every result's membership state is
            shown before the click, never only after navigating in. */}
        <Stack gap="metadata">
          <Label>{t("discovery.search.heading")}</Label>
          <Inline gap="row" align="center">
            <input
              value={searchQuery}
              placeholder={t("discovery.search.placeholder")}
              onChange={(event) => setSearchQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") submitSearch();
              }}
            />
            <Button variant="tertiary" onClick={submitSearch} disabled={searchStatus.kind === "searching" || searchQuery.trim() === ""}>
              {searchStatus.kind === "searching" ? t("common.submitting") : t("discovery.search.button")}
            </Button>
          </Inline>

          {searchStatus.kind === "error" && (
            <Text color="tertiary" role="alert">
              {t("discovery.search.error")}
            </Text>
          )}
          {searchStatus.kind === "loaded" && searchStatus.results.length === 0 && (
            <Text color="tertiary">{t("discovery.search.noResults", { query: searchStatus.query })}</Text>
          )}
          {searchStatus.kind === "loaded" &&
            searchStatus.results.map((result) => {
              const isHeld = heldTickers.has(result.ticker);
              const isWatchlisted = watchlistTickers.has(result.ticker);
              const stateKey = isHeld
                ? "discovery.card.reason.holding"
                : isWatchlisted
                  ? "discovery.card.reason.watchlist"
                  : "discovery.search.newCandidate";
              return (
                <Link
                  key={result.ticker}
                  href="#"
                  style={{ ...ACCENT_LINK_STYLE, color: "var(--color-text-primary)", display: "block" }}
                  onClick={(event) => {
                    event.preventDefault();
                    openCandidate(result.ticker);
                  }}
                >
                  <Inline gap="row" align="baseline" wrap style={{ justifyContent: "space-between" }}>
                    <Text as="span">
                      <Text as="span" color="secondary">
                        {result.ticker} —{" "}
                      </Text>
                      {result.displayName}
                    </Text>
                    <Inline gap="row" align="center">
                      <Text color="tertiary">{t(stateKey)}</Text>
                      <Text as="span" color="tertiary">→</Text>
                    </Inline>
                  </Inline>
                </Link>
              );
            })}
        </Stack>

        <Divider tone="hairline" />

        {/* 4. Recent Activity -- Decision/Outcome/Trade events scoped to
            Watchlist Cases only, a genuinely different slice from
            Portfolio's own (holdings-scoped) Recent Activity, reusing
            the exact same `deriveActivity` cross-reference. */}
        <Stack gap="metadata">
          <Label>{t("discovery.recentActivity.heading")}</Label>
          {recentActivity.kind === "loading" && (
            <Text role="status" aria-live="polite">
              {t("common.loading")}
            </Text>
          )}
          {recentActivity.kind === "error" && (
            <Text color="tertiary" role="alert">
              {t("discovery.recentActivity.loadError")}
            </Text>
          )}
          {recentActivity.kind === "loaded" && watchlistActivity.length === 0 && (
            <Text color="tertiary">{t("discovery.recentActivity.empty")}</Text>
          )}
          <Stack gap="row">
            {watchlistActivity.map((event) => (
              <RecentActivityRow key={`${event.kind}-${event.id}`} event={event} navigate={navigate} t={t} />
            ))}
          </Stack>
        </Stack>
      </Stack>
    </Container>
  );
}

function RecentActivityRow({
  event,
  navigate,
  t,
}: {
  event: ActivityEvent;
  navigate: ReturnType<typeof useNavigate>;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <Link
      href="#"
      style={{ color: "var(--color-text-secondary)", textDecoration: "none" }}
      onClick={(clickEvent) => {
        clickEvent.preventDefault();
        if (event.caseId) navigate(`/investment-case/${event.caseId}`, { state: { origin: "discovery", ticker: event.security } });
      }}
    >
      {event.security} — {event.summary} · {formatRelativeTime(event.date, t)}
    </Link>
  );
}
