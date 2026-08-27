import { useNavigate, Link as RouterLink } from "react-router-dom";
import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { ACCENT_LINK_STYLE, Container, Divider, Heading, Inline, Stack, Text } from "../foundation";
import { useTranslation } from "../i18n";
import { fetchDailyBriefAgenda, type DailyBriefAgendaView } from "../dailyBriefAgenda/dailyBriefAgendaApi";
import type { TickerAgendaGroup } from "../dailyBriefAgenda/groupAgendaByTicker";
import { realAgendaGroups } from "../dailyBriefAgenda/bookkeepingFilter";
import { TickerAgendaCard } from "../dailyBriefAgenda/TickerAgendaCard";
import { itemsSinceLastVisit } from "../dailyBriefAgenda/sinceYouWereHere";
import { fetchDailyBriefViewState, markDailyBriefViewed } from "../dailyBriefAgenda/dailyBriefViewStateApi";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { ALPHA_PLACEHOLDER_USER_ID } from "../decisionWorkspace/alphaUser";
import { fetchDailyBriefDraftSummary, type DecisionDraftSummaryView } from "../decisionWorkspace/decisionDraftApi";
import { fetchStanceForHoldings, fetchStanceForCandidates, type TickerStanceView } from "../stance/stanceApi";
import { MonitoringFreshnessNote } from "../monitoring/MonitoringFreshnessNote";
import { ScopeFreshnessSummaryNote } from "../monitoring/ScopeFreshnessSummaryNote";
import { MonitoringChangeFeed } from "../monitoring/MonitoringChangeFeed";
import { filterDuplicateMonitoringChanges } from "../monitoring/filterDuplicateMonitoringChanges";
import {
  fetchMonitoringResults,
  fetchMonitoringStatus,
  type MonitoringOperationalStatusView,
  type MonitoringResultView,
} from "../monitoring/monitoringApi";

/** Cross-Workspace Consistency Cleanup -- same uppercase small-caps
 * workspace-label treatment every top-level workspace shares. */
const PAGE_TITLE_STYLE: CSSProperties = {
  fontFamily: "var(--type-family-prose)",
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.02em",
};

type AgendaStatus = { kind: "loading" } | { kind: "error"; message: string } | { kind: "loaded"; agenda: DailyBriefAgendaView };

/**
 * Daily Brief Engine & Prioritization (Product Sprint 6) -- a complete
 * rebuild around Deliverable 2's own explicit instruction: "instead of
 * presenting independent lists, build one prioritized agenda." The
 * previous v2 page (three independent sections: a client-derived
 * "Today's Priorities" list, plus separately-fetched "Portfolio
 * Changes"/"Watchlist Updates" columns, each with its own silent
 * ordering) is fully replaced -- every one of those three signal
 * sources (`derivePortfolioActions`'s own review-queue/evidence/
 * concentration data, and Change Intelligence's own entries) is now a
 * *source* feeding the one shared `/api/daily-brief-agenda` endpoint
 * (`atlas.alpha.daily_brief_agenda`, Product Sprint 6), not a
 * page-local re-derivation. Every item already answers "why is this
 * here / why today / why should I care" via its own `headline`/
 * `reason`/`portfolioContext` -- this page adds no narrative of its
 * own beyond the summary line (Deliverable 9), itself built from real
 * `PortfolioSummaryView` fields only.
 */
export function DailyBriefPage() {
  const { t, language } = useTranslation();
  const locale = language === "sv" ? "sv-SE" : "en-US";
  const navigate = useNavigate();
  const [status, setStatus] = useState<AgendaStatus>({ kind: "loading" });
  const [openDrafts, setOpenDrafts] = useState<DecisionDraftSummaryView[]>([]);
  /** Atlas Intelligence Sprint 2 (Recommendation Quality &
   * Actionability, Deliverable 8) -- one ticker->Stance map, covering
   * both Portfolio holdings and Watchlist candidates (Daily Brief items
   * span both groups). `AgendaItemRow` itself only ever shows the
   * current Stance next to an item whose `source` is already
   * `change_intelligence` -- Change Intelligence's own real, already-
   * established "did something genuinely change today" eligibility
   * gate, never a new persisted "previous stance" this Sprint does not
   * build (see this page's own Sprint 2 addendum below). */
  const [stanceByTicker, setStanceByTicker] = useState<Map<string, TickerStanceView["stance"]>>(new Map());
  /** Atlas Intelligence Sprint 8 (Automated Monitoring Operations,
   * Deliverable 16) -- a separate fetch, deliberately: operational
   * status is a distinct read model from the agenda itself (Deliverable
   * 7), never folded into `DailyBriefAgendaView`. */
  const [monitoringStatus, setMonitoringStatus] = useState<MonitoringOperationalStatusView | null>(null);
  /** Product Intelligence Sprint 3 (Monitoring Intelligence Activation)
   * -- `GET /api/monitoring/results` (Deliverable 21's own cached read
   * model) had zero frontend callers before this sprint; only the
   * operational half above (`fetchMonitoringStatus`) was ever fetched.
   * A separate fetch, deliberately: this is investment-state
   * (`MonitoringResultView`), never conflated with `monitoringStatus`
   * above (operational state), mirroring that exact same distinction
   * this codebase already enforces at every other layer. Fetch-and-
   * forget with a silent `AbortError` no-op, matching every other
   * effect on this page. */
  const [monitoringResultsStatus, setMonitoringResultsStatus] = useState<
    { kind: "loading" } | { kind: "unavailable" } | { kind: "loaded"; results: MonitoringResultView[] }
  >({ kind: "loading" });
  /** Since You Were Here -- the value read BEFORE this visit, used to
   * compute this render's own "since you were here" window. Marking a
   * new `lastViewedAt` happens separately, once, after this value and
   * the agenda have both successfully loaded (see the effect below) --
   * never before, so a failed or still-loading page never silently
   * consumes this visit's own window without the user ever having
   * seen it. */
  const [viewState, setViewState] = useState<{ kind: "loading" } | { kind: "unavailable" } | { kind: "loaded"; lastViewedAt: string | null }>({
    kind: "loading",
  });
  const [hasMarkedViewed, setHasMarkedViewed] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetchDailyBriefAgenda(controller.signal)
      .then((agenda) => setStatus({ kind: "loaded", agenda }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus({ kind: "error", message: error instanceof Error ? error.message : t("common.unknownError") });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchDailyBriefViewState(ALPHA_PLACEHOLDER_USER_ID, controller.signal)
      .then((state) => setViewState({ kind: "loaded", lastViewedAt: state.lastViewedAt }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setViewState({ kind: "unavailable" });
      });
    return () => controller.abort();
  }, []);

  /** Marks `lastViewedAt` as now -- deliberately only once the agenda
   * has *successfully rendered* (both fetches loaded), and only once
   * per page visit (`hasMarkedViewed`). Marking on page load alone
   * (before the agenda is confirmed loaded) would risk consuming this
   * visit's own change window even if the agenda fetch then failed --
   * the smallest choice that never claims the user saw something they
   * were never actually shown. */
  useEffect(() => {
    if (hasMarkedViewed || status.kind !== "loaded" || viewState.kind !== "loaded") return;
    setHasMarkedViewed(true);
    markDailyBriefViewed(ALPHA_PLACEHOLDER_USER_ID).catch(() => {
      // Best-effort: a failed mark-viewed call simply means the next
      // visit's own window starts from the same lastViewedAt as this
      // one did -- never a lie, only a slightly wider honest window.
    });
  }, [hasMarkedViewed, status.kind, viewState.kind]);

  useEffect(() => {
    const controller = new AbortController();
    fetchMonitoringStatus(controller.signal)
      .then((s) => setMonitoringStatus(s))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchMonitoringResults(controller.signal)
      .then((run) => setMonitoringResultsStatus({ kind: "loaded", results: run.results }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setMonitoringResultsStatus({ kind: "unavailable" });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([fetchStanceForHoldings(controller.signal), fetchStanceForCandidates(controller.signal)])
      .then(([holdings, candidates]) => {
        const map = new Map<string, TickerStanceView["stance"]>();
        for (const entry of [...holdings, ...candidates]) map.set(entry.ticker, entry.stance);
        setStanceByTicker(map);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  /** Product Sprint 12 (Decision Workflow Consolidation, Deliverable 4/7
   * -- Draft Workflow discoverability / Daily Brief Integration):
   * `fetchDailyBriefDraftSummary` already existed (Sprint 9's own
   * ADR-DD-001 design anticipated exactly this) with zero callers
   * anywhere in the frontend. A committed Decision on a case with no
   * Portfolio holding and no Watchlist entry -- e.g. a brand-new
   * candidate's first decision, `StartDecisionSection`'s own primary
   * scenario -- has no visibility anywhere in Daily Brief's own agenda
   * (scoped to Portfolio/Watchlist groups only, unchanged here), so an
   * in-progress *draft* had no visibility anywhere at all. This closes
   * that gap with the endpoint already built for it. */
  useEffect(() => {
    const controller = new AbortController();
    fetchDailyBriefDraftSummary(ALPHA_PLACEHOLDER_USER_ID, controller.signal)
      .then((drafts) => setOpenDrafts(drafts))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  function openInvestmentCase(caseId: string, ticker: string | null) {
    navigate(`/investment-case/${caseId}`, { state: { origin: "daily-brief", ticker } });
  }
  function openCandidate(ticker: string) {
    navigate(`/discovery/candidate/${encodeURIComponent(ticker)}`);
  }
  function compare(ticker: string) {
    navigate(`/discovery/compare?a=${encodeURIComponent(ticker)}`);
  }
  function openHolding(ticker: string) {
    navigate(`/portfolio/holding/${encodeURIComponent(ticker)}`);
  }
  function goToPortfolio() {
    navigate("/portfolio");
  }

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        <Heading level={3} style={PAGE_TITLE_STYLE}>
          {t("dailyBrief.title")}
        </Heading>

        <Inline gap="row" wrap style={{ justifyContent: "space-between" }}>
          <Text color="secondary">{t("dailyBrief.subtitle")}</Text>
          {status.kind === "loaded" && (
            <Text color="tertiary">
              {t("dailyBriefAgenda.lastUpdated", { time: new Date(status.agenda.generatedAt).toLocaleString(locale) })}
            </Text>
          )}
        </Inline>

        <Divider tone="hairline" />

        {status.kind === "loading" && (
          <Text role="status" aria-live="polite">
            {t("common.loading")}
          </Text>
        )}
        {status.kind === "error" && <Text color="secondary">{status.message}</Text>}

        {status.kind === "loaded" && <SinceYouWereHereSection agenda={status.agenda} viewState={viewState} locale={locale} />}

        {/* Implementation Sprint B2 (Hero Reordering): moved down from
            directly under the page title -- these are Atlas's own
            operational status ("N companies awaiting analysis"), not
            its conclusion, the same "raw stats after the opinion, not
            before it" fix Portfolio's own hero already got this sprint.
            Still independent of `status.kind` (unchanged behavior --
            `monitoringStatus` is its own, separately-fetched state, so
            these notes still show even while the agenda itself is still
            loading or failed to load); only their position moved. */}
        {monitoringStatus && <MonitoringFreshnessNote status={monitoringStatus} t={t} />}
        {monitoringStatus && (
          <ScopeFreshnessSummaryNote
            summary={{
              waitingForAnalysis:
                monitoringStatus.portfolioFreshness.waitingForAnalysis + monitoringStatus.watchlistFreshness.waitingForAnalysis,
              noNewData: monitoringStatus.portfolioFreshness.noNewData + monitoringStatus.watchlistFreshness.noNewData,
              needsAttention:
                monitoringStatus.portfolioFreshness.needsAttention + monitoringStatus.watchlistFreshness.needsAttention,
            }}
            scopeKey="monitoring.freshnessSummary.scope.combined"
            t={t}
          />
        )}

        {status.kind === "loaded" && (
          <>
            <Divider tone="hairline" />

            <PortfolioSummarySection agenda={status.agenda} groups={realAgendaGroups(status.agenda.items)} />

            {openDrafts.length > 0 && (
              <>
                <Divider tone="hairline" />
                <Stack gap="metadata">
                  <Heading level={2}>{t("dailyBrief.openDrafts.heading")}</Heading>
                  <Stack gap="row">
                    {openDrafts.map((draft) => (
                      <RouterLink key={draft.draftId} to={`/decision-drafts/${draft.draftId}/commit`} style={ACCENT_LINK_STYLE}>
                        {t("dailyBrief.openDrafts.resumeLink", {
                          subject: draft.subject ?? t("decisionWorkspace.startDecision.resumeFallbackSubject"),
                        })}
                      </RouterLink>
                    ))}
                  </Stack>
                </Stack>
              </>
            )}

            <Divider tone="hairline" />

            <DailyBriefAgendaSection
              agenda={status.agenda}
              stanceByTicker={stanceByTicker}
              onOpenInvestmentCase={openInvestmentCase}
              onOpenCandidate={openCandidate}
              onCompare={compare}
              onOpenHolding={openHolding}
              onGoToPortfolio={goToPortfolio}
            />

            <Divider tone="hairline" />

            <MonitoringHistorySection
              agenda={status.agenda}
              monitoringResultsStatus={monitoringResultsStatus}
              onOpenInvestmentCase={openInvestmentCase}
            />
          </>
        )}
      </Stack>
    </Container>
  );
}

/** Since You Were Here -- the only new judgment this section makes is
 * "is `lastViewedAt` known, and if so, which already-real agenda items
 * carry a `since` timestamp after it" (`itemsSinceLastVisit`, pure,
 * tested separately). A genuine first visit (`lastViewedAt === null`)
 * renders nothing here -- "since you were here" presupposes a real
 * prior visit to compare against; inventing first-visit copy would be
 * exactly the fabricated precision this sprint exists to avoid. From
 * the second visit onward, the empty state uses Phase 7's own required
 * exact wording -- never "no events," never "everything OK." */
function SinceYouWereHereSection({
  agenda,
  viewState,
  locale,
}: {
  agenda: DailyBriefAgendaView;
  viewState: { kind: "loading" } | { kind: "unavailable" } | { kind: "loaded"; lastViewedAt: string | null };
  locale: string;
}) {
  const { t } = useTranslation();
  if (viewState.kind !== "loaded" || viewState.lastViewedAt === null) return null;

  const changed = itemsSinceLastVisit(agenda.items, viewState.lastViewedAt);
  const lastCheckedText = t("dailyBrief.sinceYouWereHere.lastChecked", {
    time: new Date(viewState.lastViewedAt).toLocaleString(locale),
  });

  return (
    <Stack gap="metadata">
      <Inline gap="row" align="center" wrap style={{ justifyContent: "space-between" }}>
        <Heading level={2}>{t("dailyBrief.sinceYouWereHere.heading")}</Heading>
        <Text color="tertiary">{lastCheckedText}</Text>
      </Inline>
      {changed.length === 0 ? (
        <Text color="secondary">{t("dailyBrief.sinceYouWereHere.empty")}</Text>
      ) : (
        <Text as="p" style={{ fontWeight: 600 }}>
          {t(changed.length === 1 ? "dailyBrief.sinceYouWereHere.countOne" : "dailyBrief.sinceYouWereHere.countOther", {
            count: changed.length,
          })}
        </Text>
      )}
    </Stack>
  );
}

/** Daily Brief Compression -- Deliverable 4's own strict ranking: show
 * the five highest-priority ticker groups (`groupAgendaByTicker`'s own
 * priority + change-event ordering), collapse the remainder behind one
 * disclosure rather than rendering every group at once. Never a second
 * fetch, never a second sort criterion beyond what `groupAgendaByTicker`
 * already computes from real, existing fields. */
const MAX_VISIBLE_GROUPS = 5;

function DailyBriefAgendaSection({
  agenda,
  stanceByTicker,
  onOpenInvestmentCase,
  onOpenCandidate,
  onCompare,
  onOpenHolding,
  onGoToPortfolio,
}: {
  agenda: DailyBriefAgendaView;
  stanceByTicker: Map<string, TickerStanceView["stance"]>;
  onOpenInvestmentCase: (caseId: string, ticker: string | null) => void;
  onOpenCandidate: (ticker: string) => void;
  onCompare: (ticker: string) => void;
  onOpenHolding: (ticker: string) => void;
  onGoToPortfolio: () => void;
}) {
  const { t } = useTranslation();
  /* Atlas UX Phase 7B, Phase 1 -- Atlas's own internal bookkeeping (a
     decision without an outcome, a missing note, an allocation awaiting
     reconciliation) is process housekeeping, never an investment fact:
     a ticker whose entire agenda is that kind of housekeeping gets no
     card here, exactly matching Portfolio's own Attention Required
     precedent (`PortfolioPage.tsx`'s `AttentionRequiredSection`), so
     the same real signal never reads as Critical on one page and as
     nothing at all on the other. */
  const groups = realAgendaGroups(agenda.items);
  const visible = groups.slice(0, MAX_VISIBLE_GROUPS);
  const collapsed = groups.slice(MAX_VISIBLE_GROUPS);

  return (
    <Stack gap="metadata">
      <Heading level={2}>{t("dailyBriefAgenda.heading")}</Heading>
      {groups.length === 0 && <Text color="tertiary">{t("dailyBriefAgenda.empty.noItems")}</Text>}
      <Stack gap="inter-section">
        {visible.map((group) => (
          <TickerAgendaCard
            key={group.ticker ?? group.items[0]!.id}
            group={group}
            stanceByTicker={stanceByTicker}
            onOpenInvestmentCase={onOpenInvestmentCase}
            onOpenCandidate={onOpenCandidate}
            onCompare={onCompare}
            onOpenHolding={onOpenHolding}
            onGoToPortfolio={onGoToPortfolio}
          />
        ))}
      </Stack>
      {collapsed.length > 0 && (
        <ExpandableDetail
          summaryLabel={t(
            collapsed.length === 1 ? "dailyBriefAgenda.collapsed.headingOne" : "dailyBriefAgenda.collapsed.headingOther",
            { count: collapsed.length },
          )}
        >
          <Stack gap="inter-section">
            {collapsed.map((group) => (
              <TickerAgendaCard
                key={group.ticker ?? group.items[0]!.id}
                group={group}
                stanceByTicker={stanceByTicker}
                onOpenInvestmentCase={onOpenInvestmentCase}
                onOpenCandidate={onOpenCandidate}
                onCompare={onCompare}
                onOpenHolding={onOpenHolding}
                onGoToPortfolio={onGoToPortfolio}
              />
            ))}
          </Stack>
        </ExpandableDetail>
      )}
    </Stack>
  );
}

/** Daily Brief Consolidation -- Monitoring history becomes a
 * collapsed, secondary drill-down (Phase 3's source-of-truth
 * principle: Daily Brief agenda owns "what matters now," Monitoring
 * owns "what happened historically"; no surface should compete with
 * another). `filterDuplicateMonitoringChanges` removes only the exact
 * change lines already surfaced in the agenda above (same ticker, same
 * `reason` string -- structurally the same underlying fact, not a
 * fuzzy guess); every minor change and every change for a ticker with
 * no agenda entry survives untouched, so no real history is lost, only
 * de-duplicated against what is already visible one section up. */
function MonitoringHistorySection({
  agenda,
  monitoringResultsStatus,
  onOpenInvestmentCase,
}: {
  agenda: DailyBriefAgendaView;
  monitoringResultsStatus: { kind: "loading" } | { kind: "unavailable" } | { kind: "loaded"; results: MonitoringResultView[] };
  onOpenInvestmentCase: (caseId: string, ticker: string | null) => void;
}) {
  const { t } = useTranslation();

  if (monitoringResultsStatus.kind === "loading") {
    return (
      <Stack gap="metadata">
        <Heading level={2}>{t("monitoring.changeFeed.heading")}</Heading>
        <Text role="status" aria-live="polite">
          {t("common.loading")}
        </Text>
      </Stack>
    );
  }
  if (monitoringResultsStatus.kind === "unavailable") {
    return (
      <Stack gap="metadata">
        <Heading level={2}>{t("monitoring.changeFeed.heading")}</Heading>
        <Text color="tertiary" role="alert">
          {t("monitoring.changeFeed.unavailable")}
        </Text>
      </Stack>
    );
  }

  /* Atlas UX Phase 7B, Phase 1 -- the dedup set includes each reason's
     own structured fact `label` (the bare, canonical fact statement,
     e.g. "Data center capex growth decelerates below 10% YoY"), not
     only the raw `reason[]` text. Confirmed live: a case-condition
     agenda reason arrives from the backend wrapped in its own ticker
     prefix and "(satisfied)" suffix, while Monitoring's own
     `change.reason` wraps the identical fact in a different sentence
     ("A condition you set for NVDA was met: ..."). Neither wrapped
     string contains the other, so only the shared, unwrapped `label`
     reliably identifies them as the same real event. */
  const agendaReasonsByTicker = new Map<string, Set<string>>();
  for (const group of realAgendaGroups(agenda.items)) {
    if (group.ticker === null) continue;
    const labels = group.reasonFacts.map((fact) => fact?.label).filter((label): label is string => !!label);
    agendaReasonsByTicker.set(group.ticker, new Set([...group.reasons, ...labels]));
  }
  const deduplicated = filterDuplicateMonitoringChanges(monitoringResultsStatus.results, agendaReasonsByTicker);
  const eventCount = deduplicated.reduce((total, result) => total + result.changes.length, 0);

  return (
    <Stack gap="metadata">
      <Heading level={2}>{t("monitoring.changeFeed.heading")}</Heading>
      {eventCount === 0 ? (
        <Text color="secondary">{t("monitoring.changeFeed.empty")}</Text>
      ) : (
        <ExpandableDetail
          summaryLabel={t(eventCount === 1 ? "monitoring.changeFeed.viewEventsOne" : "monitoring.changeFeed.viewEventsOther", {
            count: eventCount,
          })}
        >
          <MonitoringChangeFeed results={deduplicated} t={t} onOpenInvestmentCase={onOpenInvestmentCase} />
        </ExpandableDetail>
      )}
    </Stack>
  );
}

/** Atlas UX Phase 7B, Phase 1 -- Deliverable 9's original opening
 * summary showed three equal-weight bold numbers ("N items need
 * attention today" / "N high-priority items to review" / "N holdings
 * tracked") that could disagree with each other and with the agenda
 * list below (see this file's own prior "Internal Alpha Stabilization
 * fix" note, kept below for history): a real investor had no way to
 * know which number was the one that mattered. This rebuild chooses
 * exactly one primary number -- real, bookkeeping-filtered Critical and
 * High-priority tickers combined into a single "N things need your
 * attention today," counted from the same `groups` `DailyBriefAgendaSection`
 * itself renders below, so the headline number and the visible list can
 * never contradict each other. Everything else (watchlist opportunities,
 * holdings tracked, cash) is real but secondary, and renders as quiet
 * supporting metadata, never a second bold claim.
 *
 * (Internal Alpha Stabilization fix, superseded by the above: critical
 * and high-priority counts used to be mutually exclusive (an `if
 * critical, else if high` chain) -- with both present, the summary said
 * only "2 items need attention today," silently dropping the
 * high-priority item from the count even though the full agenda list
 * right below still showed it. The combined count above inherits that
 * fix by construction: both priorities are summed into the one number.) */
function PortfolioSummarySection({ agenda, groups }: { agenda: DailyBriefAgendaView; groups: TickerAgendaGroup[] }) {
  const { t } = useTranslation();
  const { summary } = agenda;
  const attentionCount = groups.filter((group) => group.topPriority === "critical" || group.topPriority === "high").length;

  return (
    <Stack gap="metadata">
      {attentionCount === 0 ? (
        <Text as="p" style={{ fontWeight: 600 }}>
          {t("dailyBriefAgenda.summary.allStable")}
        </Text>
      ) : (
        <Text as="p" style={{ fontWeight: 600 }}>
          {t(attentionCount === 1 ? "dailyBriefAgenda.summary.attentionCountOne" : "dailyBriefAgenda.summary.attentionCountOther", {
            count: attentionCount,
          })}
        </Text>
      )}
      {summary.watchlistOpportunityCount > 0 && (
        <Text color="secondary" as="p">
          {t(
            summary.watchlistOpportunityCount === 1
              ? "dailyBriefAgenda.summary.watchlistOpportunityCountOne"
              : "dailyBriefAgenda.summary.watchlistOpportunityCountOther",
            { count: summary.watchlistOpportunityCount },
          )}
        </Text>
      )}
      <Inline gap="row" wrap>
        <Text color="tertiary">{t("dailyBriefAgenda.summary.holdingsCount", { count: summary.holdingsCount })}</Text>
        {summary.cashWeightPercent !== null && (
          <Text color="tertiary">{t("dailyBriefAgenda.summary.cash", { percent: summary.cashWeightPercent.toFixed(1) })}</Text>
        )}
      </Inline>
    </Stack>
  );
}
