import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { useNavigate, Link as RouterLink } from "react-router-dom";
import { ACCENT_LINK_STYLE, Button, Container, Divider, Heading, Inline, Label, Link, Stack, Text, TextField } from "../foundation";
import { useTranslation } from "../i18n";
import { DiscoveryCandidateCard } from "../discovery/DiscoveryCandidateCard";
import { DiscoveryCandidateTable } from "../discovery/DiscoveryCandidateTable";
import { rankCandidates, type RankedCandidate } from "../discovery/rankCandidates";
import { searchSecurities, type SecurityCandidateView } from "../discovery/securityDiscoveryApi";
import {
  ensureCaseForTicker,
  fetchDiscoveryCandidates,
  type DiscoveryCandidateView,
} from "../discovery/discoveryCandidatesApi";
import { useAlphaWatchlist, type WatchlistEntryView } from "../discovery/watchlistActions";
import { useAlphaPortfolio } from "../portfolio/alphaPortfolioData";
import { fetchDailyBriefAgenda, type AgendaItemView } from "../dailyBriefAgenda/dailyBriefAgendaApi";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { fetchPortfolioFitForHoldings, type PortfolioFitAssessmentView } from "../portfolioFit/portfolioFitApi";
import type { PriorityLevel } from "../status/statusTone";

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
type HoldingsFitStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; assessments: PortfolioFitAssessmentView[] };
type CandidateStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; candidates: DiscoveryCandidateView[] };
type SearchStatus =
  | { kind: "idle" }
  | { kind: "searching" }
  | { kind: "error" }
  | { kind: "loaded"; query: string; results: SecurityCandidateView[] };
type DailyBriefAgendaFetchStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; items: AgendaItemView[] };

/**
 * Discover Doctrine (2026-08-27) -- Discover's single, locked purpose:
 * help the investor decide which company deserves attention first.
 * Not a news feed, not a watchlist dump, not a research workspace.
 * Atlas's editorial layer.
 *
 * Three sections, in strict priority order (Phase 12), ranked by
 * `rankCandidates.ts` from three real, already-computed categorical
 * signals (Portfolio Fit, Stance, Agenda priority) -- no new ranking
 * engine, no numeric score invented anywhere:
 * 1. Atlas supports a new position -- a small number of primary cards.
 * 2. No conclusion yet -- the dense comparative table. Named for what
 *    the band means rather than borrowing Stance's own "worth
 *    reviewing" wording, which is a different, shared vocabulary and
 *    reads as a contradiction when it appears as a badge on a card in
 *    tier 1.
 * 3. Entry not supported -- behind one disclosure, never dropped.
 *
 * Convergence Sprint 4D re-based all three on Atlas's own canonical
 * conclusion about entering, rather than on how the company happens to
 * suit this portfolio; see `rankCandidates.ts` for why, and for the
 * measurement that forced it.
 *
 * Convergence Sprint 4C settles three things Sprint 4B's universe
 * exposed:
 *
 * a) **The universe is the page's own state, and nothing else's.**
 *    Every tier used to render behind `watchlistStatus.entries.length
 *    > 0`: a successfully loaded candidate universe stayed completely
 *    invisible whenever the Watchlist happened to be empty, and the
 *    page then explained itself with "Your Watchlist is empty" -- a
 *    sentence about a list Discovery no longer sources anything from.
 *    Loading, error and empty now each describe the candidate fetch
 *    alone. A degraded secondary service can no longer hide candidates
 *    that loaded.
 *
 * b) **Two fetches fed nothing.** `fetchPortfolioFitForCandidates` and
 *    `fetchStanceForCandidates` were still called on every visit, and
 *    both maps built from them were already dead code -- Fit and
 *    Stance arrive on the candidate itself since Sprint 4B. Their only
 *    surviving effect was that a failed *Portfolio Fit* request
 *    printed "Atlas could not load your ranked candidates," an error
 *    about a universe that had loaded perfectly. Both are gone.
 *
 * c) **Density.** Fourteen Worth-reviewing candidates rendered as
 *    fourteen one-signal rows is a list, not a comparison; the lower
 *    tiers are now `DiscoveryCandidateTable`.
 *
 * Compare and Search remain secondary/tertiary (Phase 7/8). Search is
 * now explicitly separated rather than merely quiet: passive candidates
 * are ranked and evaluated, search results are neither, and the page
 * says so instead of leaving the difference to visual weight alone.
 */
export function DiscoveryPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const portfolioResource = useAlphaPortfolio();
  const portfolioStatus: PortfolioStatus =
    portfolioResource.kind === "loaded" ? { kind: "loaded", view: portfolioResource.data as PortfolioView } : portfolioResource;
  /** Read for exactly one purpose: marking a *search* result the
   * investor already watches (Phase 8). It never gates, filters or
   * orders a candidate -- the backend already excluded actively
   * watched companies from the universe. */
  const watchlistStatus: WatchlistStatus = useAlphaWatchlist();
  /** Only used to pre-fill Compare's "against your weakest holding"
   * quick pick (Phase 7) -- never merged into the candidate list
   * itself. A held ticker is not a Discovery candidate (Phase 6). */
  const [holdingsFitStatus, setHoldingsFitStatus] = useState<HoldingsFitStatus>({ kind: "loading" });
  const [dailyBriefAgenda, setDailyBriefAgenda] = useState<DailyBriefAgendaFetchStatus>({ kind: "loading" });
  /** Sprint 4B: the passive candidate universe now comes from the
   * backend -- securities Atlas has analysed that the investor is not
   * already following. It used to be `nonHeldWatchlistEntries`, so
   * Discovery could only ever show back the prospects the investor had
   * added themselves. */
  const [candidateStatus, setCandidateStatus] = useState<CandidateStatus>({ kind: "loading" });
  const [searchQuery, setSearchQuery] = useState("");
  const [searchStatus, setSearchStatus] = useState<SearchStatus>({ kind: "idle" });
  const [openingTicker, setOpeningTicker] = useState<string | null>(null);
  const [openCaseFailed, setOpenCaseFailed] = useState(false);

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
   * -- a candidate's own sentence is always Atlas's own canonical
   * Decision Support statement, never a raw event announcement. */
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
    fetchDiscoveryCandidates(controller.signal)
      .then((candidates) => setCandidateStatus({ kind: "loaded", candidates }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setCandidateStatus({ kind: "error" });
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

  function clearSearch() {
    setSearchQuery("");
    setSearchStatus({ kind: "idle" });
  }

  /** Sprint 4B: straight to the Investment Case.
   *
   * This used to route through `/discovery/candidate/:ticker`, whose
   * Open-Case button silently did nothing for a company that was
   * neither held nor watchlisted -- there was no branch for it,
   * because a Case had no instrument of its own and adding to the
   * Watchlist was the only way to get one. Sprint 4A fixed that;
   * `ensureCaseForTicker` reuses an existing Case or creates a bound
   * one, and mutates no membership.
   *
   * Sprint 4C makes the wait and the failure visible: the open is
   * announced while it is in flight, a second open is ignored until
   * it settles, and a failed ensure now says so instead of quietly
   * resetting to a control that looks as if it was never pressed. */
  function openCaseForTicker(ticker: string) {
    if (openingTicker !== null) return;
    setOpeningTicker(ticker);
    setOpenCaseFailed(false);
    ensureCaseForTicker(ticker)
      .then((caseId) => navigate(`/investment-case/${caseId}`, { state: { origin: "discovery", ticker } }))
      .catch(() => {
        setOpeningTicker(null);
        setOpenCaseFailed(true);
      });
  }

  const heldTickers = new Set(portfolioStatus.kind === "loaded" ? portfolioStatus.view.holdings.map((h) => h.ticker) : []);
  const watchlistTickers = new Set(watchlistStatus.kind === "loaded" ? watchlistStatus.entries.map((e) => e.ticker) : []);
  const priorityByTicker = new Map<string, PriorityLevel>();
  if (dailyBriefAgenda.kind === "loaded") {
    for (const item of dailyBriefAgenda.items) {
      if (item.ticker) priorityByTicker.set(item.ticker, item.priority);
    }
  }

  /** Sprint 4B. Eligibility is the backend's decision and ranking is
   * this page's -- kept apart on purpose. The endpoint has already
   * excluded holdings ("already owned, Portfolio shows its state") and
   * active Watchlist prospects ("already explicitly monitored"), so
   * nothing is filtered here; `rankCandidates` receives an
   * already-eligible set and only decides the order.
   *
   * `fit` and `stance` arrive on the candidate itself. A `null` is a
   * real answer -- Portfolio Fit or Stance genuinely could not
   * evaluate the company -- and `rankCandidates` ranks it last rather
   * than treating it as neutral. Agenda priority stays a local lookup:
   * it is Daily Brief's signal and only exists for companies that feed
   * it, which is honestly `null` for an independent candidate. */
  const candidates = candidateStatus.kind === "loaded" ? candidateStatus.candidates : [];
  const candidateByCaseId = new Map(candidates.map((candidate) => [candidate.caseId, candidate]));
  const candidateTickers = new Set(candidates.map((candidate) => candidate.ticker));
  const rankedCandidateInputs: RankedCandidate[] = candidates.map((candidate) => ({
    ticker: candidate.ticker,
    caseId: candidate.caseId,
    fit: candidate.fitRating,
    stance: candidate.stanceLevel,
    priority: priorityByTicker.get(candidate.ticker) ?? null,
    decisionSupport: candidate.decisionSupportLevel,
  }));
  const ranked = rankCandidates(rankedCandidateInputs);

  /** Sprint 4C. `rankCandidates` deliberately carries only the three
   * signals it ranks on, so the rendered rows are rejoined here to the
   * candidate the universe actually sent, preserving the ranked order
   * exactly -- no re-sorting, no re-filtering.
   *
   * The join key is `caseId`, not the ticker: `case_instrument_
   * bindings` makes `case_id` its primary key but leaves
   * `instrument_key` merely indexed, so two Cases bound to one
   * instrument is a state the schema permits (nothing in the live
   * database is in it today). Joining on the ticker would then render
   * one candidate twice under one React key; joining on the Case
   * cannot. */
  function resolveTier(tier: RankedCandidate[]): DiscoveryCandidateView[] {
    return tier.flatMap((entry) => {
      const candidate = entry.caseId === null ? undefined : candidateByCaseId.get(entry.caseId);
      return candidate ? [candidate] : [];
    });
  }
  const highestCandidates = resolveTier(ranked.highest);
  const worthReviewingCandidates = resolveTier(ranked.worthReviewing);
  const everythingElseCandidates = resolveTier(ranked.everythingElse);

  const evaluatedHoldings =
    holdingsFitStatus.kind === "loaded" ? holdingsFitStatus.assessments.filter((a) => a.overall !== "unavailable") : [];
  const weakestHoldingTicker = evaluatedHoldings.length > 0 ? evaluatedHoldings[evaluatedHoldings.length - 1]!.ticker : null;

  function compareHref(ticker: string): string {
    const params = new URLSearchParams({ a: ticker });
    if (weakestHoldingTicker && weakestHoldingTicker !== ticker) params.set("b", weakestHoldingTicker);
    return `/discovery/compare?${params.toString()}`;
  }

  /** Phase 8 / Sprint 4C. What Atlas actually knows about a searched
   * ticker, and nothing more. Ownership and monitoring are only
   * claimed once those lists have really loaded -- a failed Portfolio
   * or Watchlist request must not turn a company the investor owns
   * into "New candidate". A ticker already in the loaded universe is
   * marked as analysed, because telling the investor a company Atlas
   * has evaluated is "not yet evaluated" would be false. */
  function searchStateKey(ticker: string): "discovery.card.reason.holding" | "discovery.card.reason.watchlist" | "discovery.search.inCandidates" | "discovery.search.newCandidate" | null {
    if (portfolioStatus.kind === "loaded" && heldTickers.has(ticker)) return "discovery.card.reason.holding";
    if (watchlistStatus.kind === "loaded" && watchlistTickers.has(ticker)) return "discovery.card.reason.watchlist";
    if (candidateTickers.has(ticker)) return "discovery.search.inCandidates";
    if (portfolioStatus.kind === "loaded" && watchlistStatus.kind === "loaded" && candidateStatus.kind === "loaded") {
      return "discovery.search.newCandidate";
    }
    return null;
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

        {/* Sprint 4C. Loading, error and empty describe the candidate
            universe and only the candidate universe. */}
        {candidateStatus.kind === "loading" && (
          <Text role="status" aria-live="polite">
            {t("discovery.candidates.loading")}
          </Text>
        )}
        {candidateStatus.kind === "error" && (
          <Text color="tertiary" role="alert">
            {t("discovery.candidates.loadError")}
          </Text>
        )}
        {candidateStatus.kind === "loaded" && candidates.length === 0 && (
          <Text color="tertiary">{t("discovery.candidates.empty")}</Text>
        )}
        {/* Opening a Case can be started from a card, from any table
            row or from a search result, so both its progress and its
            failure are announced in one predictable place rather than
            beside whichever control happened to be pressed. */}
        {openingTicker !== null && (
          <Text color="tertiary" role="status" aria-live="polite">
            {t("discovery.card.openingCase", { ticker: openingTicker })}
          </Text>
        )}
        {openCaseFailed && (
          <Text color="tertiary" role="alert">
            {t("discovery.card.openCaseFailed")}
          </Text>
        )}

        {candidateStatus.kind === "loaded" && candidates.length > 0 && (
          <>
            {/* The one factual line about what this page is looking at
                -- a count of the loaded universe, no claim beyond it. */}
            <Text color="tertiary" as="p">
              {t(candidates.length === 1 ? "discovery.candidates.universeOne" : "discovery.candidates.universeOther", {
                count: candidates.length,
              })}
            </Text>

            {/* 1. Highest opportunity -- the page's entire reason to
                exist (Phase 2/13). */}
            <Stack gap="metadata">
              <Label>{t("discovery.entrySupported.heading")}</Label>
              {highestCandidates.length === 0 ? (
                <Text color="tertiary">{t("discovery.entrySupported.empty")}</Text>
              ) : (
                <Stack gap="row">
                  {highestCandidates.map((candidate) => (
                    <DiscoveryCandidateCard
                      key={candidate.caseId}
                      ticker={candidate.ticker}
                      displayName={candidate.companyName}
                      fit={candidate.fitRating}
                      stance={candidate.stanceLevel}
                      decisionSupport={candidate.decisionSupportLevel}
                      variant="primary"
                      onOpenCase={() => openCaseForTicker(candidate.ticker)}
                      onCompare={() => navigate(compareHref(candidate.ticker))}
                    />
                  ))}
                </Stack>
              )}
            </Stack>

            {/* 2. Worth reviewing -- the dense comparative table
                (Sprint 4C). */}
            {worthReviewingCandidates.length > 0 && (
              <>
                <Divider tone="hairline" />
                <Stack gap="metadata">
                  <Label>{t("discovery.notConcluded.heading")}</Label>
                  <Text color="tertiary" as="p">
                    {t("discovery.notConcluded.explanation")}
                  </Text>
                  <DiscoveryCandidateTable
                    candidates={worthReviewingCandidates}
                    captionKey="discovery.notConcluded.heading"
                    onOpenCase={openCaseForTicker}
                  />
                </Stack>
              </>
            )}

            {/* 3. Everything else -- never dropped, always reachable,
                never shown with the same visual weight as a real
                candidate signal. */}
            {everythingElseCandidates.length > 0 && (
              <>
                <Divider tone="hairline" />
                <ExpandableDetail
                  summaryLabel={t(
                    everythingElseCandidates.length === 1
                      ? "discovery.notSupported.headingOne"
                      : "discovery.notSupported.headingOther",
                    { count: everythingElseCandidates.length },
                  )}
                >
                  <DiscoveryCandidateTable
                    candidates={everythingElseCandidates}
                    captionKey="discovery.notSupported.caption"
                    onOpenCase={openCaseForTicker}
                  />
                </ExpandableDetail>
              </>
            )}
          </>
        )}

        <Divider tone="hairline" />

        {/* Search -- a utility (Phase 8), still the lowest-weight
            region on the page, but now explicitly named rather than
            unlabelled. Sprint 4C: an unlabelled field sitting directly
            under a ranked list reads as part of it. These results are
            neither ranked nor evaluated -- they are whatever the SEC
            ticker file matched -- and the page states that instead of
            trusting visual weight to carry the distinction. */}
        <Stack gap="metadata">
          <Label>{t("discovery.search.heading")}</Label>
          <Text color="tertiary" as="p">
            {t("discovery.search.explanation")}
          </Text>
          <Inline gap="row" align="center" wrap>
            <TextField
              value={searchQuery}
              aria-label={t("discovery.search.heading")}
              placeholder={t("discovery.search.placeholder")}
              onChange={(event) => setSearchQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") submitSearch();
              }}
            />
            <Button variant="tertiary" onClick={submitSearch} disabled={searchStatus.kind === "searching" || searchQuery.trim() === ""}>
              {searchStatus.kind === "searching" ? t("common.submitting") : t("discovery.search.button")}
            </Button>
            {searchStatus.kind !== "idle" && (
              <Button variant="tertiary" onClick={clearSearch}>
                {t("discovery.search.clear")}
              </Button>
            )}
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
                const stateKey = searchStateKey(result.ticker);
                return (
                  <Link
                    key={result.ticker}
                    href="#"
                    style={{ color: "var(--color-text-secondary)", display: "block" }}
                    onClick={(event) => {
                      event.preventDefault();
                      openCaseForTicker(result.ticker);
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
                        {stateKey !== null && <Text color="tertiary">{t(stateKey)}</Text>}
                        <Text as="span" color="tertiary">→</Text>
                      </Inline>
                    </Inline>
                  </Link>
                );
              })}
            </Stack>
          )}
        </Stack>
      </Stack>
    </Container>
  );
}
