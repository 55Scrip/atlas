import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { useNavigate, Link as RouterLink } from "react-router-dom";
import { ACCENT_LINK_STYLE, Button, Container, Divider, Heading, Inline, Label, Link, Stack, Text, TextField } from "../foundation";
import { useTranslation } from "../i18n";
import { DiscoveryCandidateCard } from "../discovery/DiscoveryCandidateCard";
import { rankCandidates, type RankedCandidate } from "../discovery/rankCandidates";
import { searchSecurities, type SecurityCandidateView } from "../discovery/securityDiscoveryApi";
import {
  getAlphaWatchlistSnapshot,
  removeTickerFromWatchlist,
  setAlphaWatchlistData,
  useAlphaWatchlist,
  type WatchlistEntryView,
} from "../discovery/watchlistActions";
import { useAlphaPortfolio } from "../portfolio/alphaPortfolioData";
import { fetchDailyBriefAgenda, type AgendaItemView } from "../dailyBriefAgenda/dailyBriefAgendaApi";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import {
  fetchPortfolioFitForCandidates,
  fetchPortfolioFitForHoldings,
  type PortfolioFitAssessmentView,
} from "../portfolioFit/portfolioFitApi";
import type { PriorityLevel } from "../status/statusTone";
import { fetchStanceForCandidates, type TickerStanceView } from "../stance/stanceApi";

/** Cross-Workspace Consistency Cleanup -- same uppercase small-caps
 * workspace-label treatment every top-level workspace shares. */
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
type DailyBriefAgendaFetchStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; items: AgendaItemView[] };

/**
 * Discover Doctrine (2026-08-27) -- Discover's single, locked purpose:
 * "Help the investor decide which watchlist companies deserve attention
 * first." Not a news feed, not a watchlist dump, not a research
 * workspace. Atlas's editorial layer.
 *
 * Three sections, in strict priority order (Phase 12):
 * 1. Highest opportunity -- a small number of large, primary-action
 *    cards (Phase 2's own "3-5 primary candidates" target), ranked
 *    from three real, already-computed categorical signals (Portfolio
 *    Fit, Stance, Agenda priority) via `rankCandidates.ts` -- no new
 *    ranking engine, no numeric score invented anywhere.
 * 2. Worth reviewing -- compact, low-visual-weight rows: ticker,
 *    rating, one line, Open Investment Case. Nothing more.
 * 3. Everything else -- the remainder, collapsed behind one
 *    disclosure, never dropped.
 *
 * Held companies are excluded from every tier (Phase 6): current
 * portfolio state already belongs to Portfolio; Discover is for future
 * decisions. Compare and Search are demoted to secondary/tertiary
 * (Phase 7/8) -- neither competes with the ranked candidates for the
 * page's own primary attention. "Recent Watchlist Activity" is removed
 * entirely (Phase 9): it was retrospective bookkeeping with no real
 * discovery signal, and no backend concept behind it at all.
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
  /** Only used to pre-fill Compare's "against your weakest holding"
   * quick pick (Phase 7) -- never merged into the candidate list
   * itself. A held ticker is not a Discover candidate (Phase 6). */
  const [holdingsFitStatus, setHoldingsFitStatus] = useState<CandidateFitStatus>({ kind: "loading" });
  const [stanceCandidatesStatus, setStanceCandidatesStatus] = useState<StanceCandidatesStatus>({ kind: "loading" });
  const [dailyBriefAgenda, setDailyBriefAgenda] = useState<DailyBriefAgendaFetchStatus>({ kind: "loading" });
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

  /** Only the categorical `priority` level feeds ranking (Agenda
   * priority is one of the three real signals `rankCandidates` uses).
   * The raw `headline` text on each item is never read here (Phase 5)
   * -- a candidate's own sentence is always its synthesized Portfolio
   * Fit reasoning, never a raw event announcement. */
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
  const stanceByTicker = new Map(
    stanceCandidatesStatus.kind === "loaded" ? stanceCandidatesStatus.entries.map((e) => [e.ticker, e.stance.level]) : [],
  );
  const priorityByTicker = new Map<string, PriorityLevel>();
  if (dailyBriefAgenda.kind === "loaded") {
    for (const item of dailyBriefAgenda.items) {
      if (item.ticker) priorityByTicker.set(item.ticker, item.priority);
    }
  }

  /** Phase 6 -- a security already held is not a candidate to consider
   * buying; it already is one, and Portfolio already shows its current
   * state. Excluded here, before ranking, rather than ranked and then
   * hidden -- so it never occupies a "highest opportunity" slot a real
   * candidate could have used. */
  const nonHeldWatchlistEntries = watchlistStatus.kind === "loaded" ? watchlistStatus.entries.filter((e) => !heldTickers.has(e.ticker)) : [];
  const rankedCandidateInputs: RankedCandidate[] = nonHeldWatchlistEntries.map((entry) => ({
    ticker: entry.ticker,
    caseId: entry.caseId,
    assessment: candidateFitByTicker.get(entry.ticker) ?? null,
    stance: stanceByTicker.get(entry.ticker) ?? null,
    priority: priorityByTicker.get(entry.ticker) ?? null,
  }));
  const ranked = rankCandidates(rankedCandidateInputs);
  const isFitDataLoading = candidateFitStatus.kind === "loading" || watchlistStatus.kind === "loading";

  const evaluatedHoldings =
    holdingsFitStatus.kind === "loaded" ? holdingsFitStatus.assessments.filter((a) => a.overall !== "unavailable") : [];
  const weakestHoldingTicker = evaluatedHoldings.length > 0 ? evaluatedHoldings[evaluatedHoldings.length - 1]!.ticker : null;

  function compareHref(ticker: string): string {
    const params = new URLSearchParams({ a: ticker });
    if (weakestHoldingTicker && weakestHoldingTicker !== ticker) params.set("b", weakestHoldingTicker);
    return `/discovery/compare?${params.toString()}`;
  }

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

        {isFitDataLoading && (
          <Text role="status" aria-live="polite">
            {t("portfolioFit.section.loading")}
          </Text>
        )}
        {candidateFitStatus.kind === "error" && (
          <Text color="tertiary" role="alert">
            {t("discovery.candidates.loadError")}
          </Text>
        )}
        {watchlistStatus.kind === "loaded" && watchlistStatus.entries.length === 0 && (
          <Text color="tertiary">{t("discovery.watchlistCandidates.empty")}</Text>
        )}

        {!isFitDataLoading && watchlistStatus.kind === "loaded" && watchlistStatus.entries.length > 0 && (
          <>
            {/* 1. Highest opportunity -- the page's entire reason to
                exist (Phase 2/13). */}
            <Stack gap="metadata">
              <Label>{t("discovery.highestOpportunity.heading")}</Label>
              {ranked.highest.length === 0 ? (
                <Text color="tertiary">{t("discovery.highestOpportunity.empty")}</Text>
              ) : (
                <Stack gap="inter-section">
                  {ranked.highest.map((candidate) => (
                    <DiscoveryCandidateCard
                      key={candidate.caseId ?? candidate.ticker}
                      ticker={candidate.ticker}
                      assessment={candidate.assessment}
                      stance={candidate.stance}
                      variant="primary"
                      onOpenCase={() =>
                        navigate(`/investment-case/${candidate.caseId}`, { state: { origin: "discovery", ticker: candidate.ticker } })
                      }
                      onRemoveFromWatchlist={() => removeFromWatchlist(candidate.ticker)}
                      onCompare={() => navigate(compareHref(candidate.ticker))}
                    />
                  ))}
                </Stack>
              )}
            </Stack>

            <Divider tone="hairline" />

            {/* 2. Worth reviewing -- compact rows, low visual weight. */}
            {ranked.worthReviewing.length > 0 && (
              <>
                <Stack gap="metadata">
                  <Label>{t("discovery.worthReviewing.heading")}</Label>
                  <Stack gap="row">
                    {ranked.worthReviewing.map((candidate) => (
                      <DiscoveryCandidateCard
                        key={candidate.caseId ?? candidate.ticker}
                        ticker={candidate.ticker}
                        assessment={candidate.assessment}
                        variant="secondary"
                        onOpenCase={() =>
                          navigate(`/investment-case/${candidate.caseId}`, { state: { origin: "discovery", ticker: candidate.ticker } })
                        }
                      />
                    ))}
                  </Stack>
                </Stack>
                <Divider tone="hairline" />
              </>
            )}

            {/* 3. Everything else -- never dropped, always reachable,
                never shown with the same visual weight as a real
                candidate signal. */}
            {ranked.everythingElse.length > 0 && (
              <>
                <ExpandableDetail
                  summaryLabel={t(
                    ranked.everythingElse.length === 1 ? "discovery.everythingElse.headingOne" : "discovery.everythingElse.headingOther",
                    { count: ranked.everythingElse.length },
                  )}
                >
                  <Stack gap="row">
                    {ranked.everythingElse.map((candidate) => (
                      <DiscoveryCandidateCard
                        key={candidate.caseId ?? candidate.ticker}
                        ticker={candidate.ticker}
                        assessment={candidate.assessment}
                        variant="secondary"
                        onOpenCase={() =>
                          navigate(`/investment-case/${candidate.caseId}`, { state: { origin: "discovery", ticker: candidate.ticker } })
                        }
                      />
                    ))}
                  </Stack>
                </ExpandableDetail>
                <Divider tone="hairline" />
              </>
            )}
          </>
        )}

        {/* Search -- a utility (Phase 8), deliberately the lowest-
            weight text on the page: no section label, no explanatory
            paragraph, never competing with the ranked candidates
            above it. */}
        <Inline gap="row" align="center">
          <TextField
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
        {searchStatus.kind === "loaded" && searchStatus.results.length > 0 && (
          <Stack gap="row">
            {searchStatus.results.map((result) => {
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
                  style={{ color: "var(--color-text-secondary)", display: "block" }}
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
        )}
      </Stack>
    </Container>
  );
}
