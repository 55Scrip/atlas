import { useNavigate, Link as RouterLink } from "react-router-dom";
import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { ACCENT_LINK_STYLE, Container, Divider, Heading, Inline, Stack, Text } from "../foundation";
import { useTranslation } from "../i18n";
import { fetchDailyBriefAgenda, type DailyBriefAgendaView } from "../dailyBriefAgenda/dailyBriefAgendaApi";
import { fetchDailyBriefChangeLog, type TickerChangeGroupView } from "../dailyBriefAgenda/dailyBriefChangeLogApi";
import { describeChangeLogEntry } from "../dailyBriefAgenda/describeChangeLogEntry";
import { fetchDailyBriefViewState, markDailyBriefViewed } from "../dailyBriefAgenda/dailyBriefViewStateApi";
import { ExpandableDetail } from "../investmentCase/ExpandableDetail";
import { ALPHA_PLACEHOLDER_USER_ID } from "../decisionWorkspace/alphaUser";
import { fetchDailyBriefDraftSummary, type DecisionDraftSummaryView } from "../decisionWorkspace/decisionDraftApi";
import { MonitoringFreshnessNote } from "../monitoring/MonitoringFreshnessNote";
import { ScopeFreshnessSummaryNote } from "../monitoring/ScopeFreshnessSummaryNote";
import { fetchMonitoringStatus, type MonitoringOperationalStatusView } from "../monitoring/monitoringApi";

/** Cross-Workspace Consistency Cleanup -- same uppercase small-caps
 * workspace-label treatment every top-level workspace shares. */
const PAGE_TITLE_STYLE: CSSProperties = {
  fontFamily: "var(--type-family-prose)",
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.02em",
};

type AgendaStatus = { kind: "loading" } | { kind: "error"; message: string } | { kind: "loaded"; agenda: DailyBriefAgendaView };
type ViewState = { kind: "loading" } | { kind: "unavailable" } | { kind: "loaded"; lastViewedAt: string | null };
type ChangeLogStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "unavailable" }
  | { kind: "loaded"; groups: TickerChangeGroupView[] };

/**
 * Daily Brief 2.0 (Decision-First Briefing & Notification Lifecycle) --
 * Daily Brief reports CHANGES in Atlas's investment view, never Atlas's
 * current view (that is Portfolio/Watchlist/Investment Case's own job,
 * unchanged by this sprint) and never raw system/bookkeeping activity.
 * The page's own three-section shape mirrors this sprint's own Phase 7
 * exactly: "Since your last visit" (real, durably-recorded eligible
 * changes -- `dailyBriefChangeLogApi.ts`, backed by
 * `atlas.alpha.daily_brief_change_log`), "Atlas is watching today"
 * (forward-looking catalysts -- always the calm fallback today, since
 * no scheduled-catalyst data source exists anywhere in this codebase;
 * see this sprint's own final report for why that is a documented gap,
 * not an oversight), and Reviews (intentionally not built this sprint
 * -- Weekly/Monthly Review is a real future consumer of the same
 * durable change log, but building it now would be exactly the
 * "recreate History as another consumer feed" this sprint's own
 * Non-Goals forbid).
 *
 * The former "Since You Were Here" section and the always-shown raw
 * agenda cards ("Today's most important developments") are both
 * removed: both re-announced Atlas's *current* state on every visit
 * (a persistent Reduce recommendation would resurface indefinitely),
 * which is precisely this sprint's Golden Rule violation. Current-state
 * review (watchlist candidates, portfolio positions) already has a
 * home on Portfolio/Watchlist -- unchanged by this sprint.
 */
export function DailyBriefPage() {
  const { t, language } = useTranslation();
  const locale = language === "sv" ? "sv-SE" : "en-US";
  const navigate = useNavigate();
  const [status, setStatus] = useState<AgendaStatus>({ kind: "loading" });
  const [openDrafts, setOpenDrafts] = useState<DecisionDraftSummaryView[]>([]);
  const [monitoringStatus, setMonitoringStatus] = useState<MonitoringOperationalStatusView | null>(null);
  /** Read BEFORE this visit's agenda call -- `lastViewedAt === null`
   * means this is the user's first-ever Daily Brief visit (Phase 6):
   * nothing is "since your last visit" yet, and this visit's own
   * agenda build deliberately records nothing into the change log
   * either (see the agenda-fetch effect below), so a brand-new
   * portfolio's initial analysis never resurfaces as "changes" on the
   * second visit. */
  const [viewState, setViewState] = useState<ViewState>({ kind: "loading" });
  const [hasMarkedViewed, setHasMarkedViewed] = useState(false);
  const [changeLogStatus, setChangeLogStatus] = useState<ChangeLogStatus>({ kind: "idle" });

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

  /** Waits for `viewState` to resolve before building the agenda, since
   * whether this call passes `userId` (and therefore whether it may
   * durably record an eligible change) depends on knowing first whether
   * this is a genuine first visit. A `viewState` fetch failure
   * ("unavailable") also withholds `userId` -- recording without a
   * trustworthy `lastViewedAt` risks logging onboarding noise as a
   * "change," which this sprint exists to prevent, not risk. */
  useEffect(() => {
    if (viewState.kind === "loading") return;
    const controller = new AbortController();
    const isGenuineFirstVisit = viewState.kind === "loaded" && viewState.lastViewedAt === null;
    const recordingUserId = viewState.kind === "loaded" && !isGenuineFirstVisit ? ALPHA_PLACEHOLDER_USER_ID : undefined;
    fetchDailyBriefAgenda(controller.signal, recordingUserId)
      .then((agenda) => setStatus({ kind: "loaded", agenda }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus({ kind: "error", message: error instanceof Error ? error.message : t("common.unknownError") });
      });
    return () => controller.abort();
  }, [viewState.kind]);

  /** The change log itself -- fetched only once this visit's own agenda
   * build has already run (so a change first detected on this very
   * visit is already durably recorded and included), and only when
   * there is a real prior visit to report changes "since." */
  useEffect(() => {
    if (status.kind !== "loaded") return;
    if (viewState.kind !== "loaded" || viewState.lastViewedAt === null) return;
    const controller = new AbortController();
    setChangeLogStatus({ kind: "loading" });
    fetchDailyBriefChangeLog(ALPHA_PLACEHOLDER_USER_ID, controller.signal)
      .then((groups) => setChangeLogStatus({ kind: "loaded", groups }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setChangeLogStatus({ kind: "unavailable" });
      });
    return () => controller.abort();
  }, [status.kind, viewState.kind]);

  /** Marks `lastViewedAt` as now -- only once the agenda has
   * successfully rendered, and only once per page visit. */
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

  /** RC-3, Phase 4 -- marking a change SEEN is no longer done here.
   * Every real path into an Investment Case (this card included)
   * converges on `InvestmentCasePage` itself, which is now the one
   * place that marks the case's own live change seen on load -- so
   * this card only navigates, exactly like every other entry point,
   * rather than duplicating a second mark-seen call and a second
   * optimistic-update path. */
  function openChangeFromCard(group: TickerChangeGroupView) {
    if (group.primary.caseId) openInvestmentCase(group.primary.caseId, group.ticker);
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

        {status.kind === "loaded" && (
          <>
            <SinceYourLastVisitSection viewState={viewState} changeLogStatus={changeLogStatus} onOpen={openChangeFromCard} />
            <AtlasIsWatchingTodaySection />
          </>
        )}

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

            <PortfolioSummarySection agenda={status.agenda} />

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
          </>
        )}
      </Stack>
    </Container>
  );
}

/** Phase 7, Section 1: "Since your last visit" -- the only section
 * reporting real, durably-recorded eligible changes
 * (`eligibility.py`'s own materiality rule, applied once on the
 * backend, never re-derived here). Capped at 3 primary cards, one per
 * company (Phase 10), with the remainder behind one disclosure -- never
 * dropped, never hidden permanently. */
const MAX_VISIBLE_CHANGE_GROUPS = 3;

function SinceYourLastVisitSection({
  viewState,
  changeLogStatus,
  onOpen,
}: {
  viewState: ViewState;
  changeLogStatus: ChangeLogStatus;
  onOpen: (group: TickerChangeGroupView) => void;
}) {
  const { t } = useTranslation();
  // A read-state we can't honestly confirm is rendered as nothing --
  // never a fabricated "no changes" line when Atlas genuinely doesn't
  // know whether this is a first visit (Non-Goal: "never fake
  // read-state").
  if (viewState.kind !== "loaded") return null;

  return (
    <Stack gap="metadata">
      <Heading level={2}>{t("dailyBrief.sinceLastVisit.heading")}</Heading>
      {viewState.lastViewedAt === null ? (
        <Text color="secondary">{t("dailyBrief.sinceLastVisit.onboardingCalm")}</Text>
      ) : changeLogStatus.kind === "loading" || changeLogStatus.kind === "idle" ? (
        <Text role="status" aria-live="polite">
          {t("common.loading")}
        </Text>
      ) : changeLogStatus.kind === "unavailable" ? (
        <Text color="tertiary" role="alert">
          {t("dailyBrief.sinceLastVisit.unavailable")}
        </Text>
      ) : changeLogStatus.groups.length === 0 ? (
        <Text color="secondary">{t("dailyBrief.sinceLastVisit.empty")}</Text>
      ) : (
        <>
          <Stack gap="inter-section">
            {changeLogStatus.groups.slice(0, MAX_VISIBLE_CHANGE_GROUPS).map((group) => (
              <ChangeGroupCard key={group.ticker} group={group} onOpen={onOpen} />
            ))}
          </Stack>
          {changeLogStatus.groups.length > MAX_VISIBLE_CHANGE_GROUPS && (
            <ExpandableDetail
              summaryLabel={t(
                changeLogStatus.groups.length - MAX_VISIBLE_CHANGE_GROUPS === 1
                  ? "dailyBriefAgenda.collapsed.headingOne"
                  : "dailyBriefAgenda.collapsed.headingOther",
                { count: changeLogStatus.groups.length - MAX_VISIBLE_CHANGE_GROUPS },
              )}
            >
              <Stack gap="inter-section">
                {changeLogStatus.groups.slice(MAX_VISIBLE_CHANGE_GROUPS).map((group) => (
                  <ChangeGroupCard key={group.ticker} group={group} onOpen={onOpen} />
                ))}
              </Stack>
            </ExpandableDetail>
          )}
        </>
      )}
    </Stack>
  );
}

const NEW_DOT_STYLE: CSSProperties = {
  display: "inline-block",
  width: "8px",
  height: "8px",
  borderRadius: "50%",
  background: "var(--color-accent)",
  flexShrink: 0,
};

/** One company, one message (Phase 10) -- `group.primary` is the single
 * real fact this card is built from; `additionalCount` is surfaced as a
 * plain link into the Investment Case, never a second card, never a
 * fabricated combined sentence stitching unrelated facts together. */
function ChangeGroupCard({ group, onOpen }: { group: TickerChangeGroupView; onOpen: (group: TickerChangeGroupView) => void }) {
  const { t } = useTranslation();
  const sentence = describeChangeLogEntry(group.primary, t);

  return (
    <Stack gap="row">
      <Inline gap="row" align="center">
        {group.isNew && <span aria-hidden="true" style={NEW_DOT_STYLE} />}
        <Text as="span" style={{ fontWeight: 600 }}>
          {group.ticker}
        </Text>
        {group.isNew && (
          <Text as="span" color="tertiary" style={{ fontSize: "var(--type-body-min-size)" }}>
            {t("dailyBrief.sinceLastVisit.newLabel")}
          </Text>
        )}
      </Inline>
      <Text color="secondary" as="p">
        {sentence}
      </Text>
      {group.additionalCount > 0 && group.primary.caseId && (
        <a
          href="#"
          style={ACCENT_LINK_STYLE}
          onClick={(event) => {
            event.preventDefault();
            onOpen(group);
          }}
        >
          {t(
            group.additionalCount === 1 ? "dailyBrief.sinceLastVisit.moreForCompanyOne" : "dailyBrief.sinceLastVisit.moreForCompanyOther",
            { count: group.additionalCount, ticker: group.ticker },
          )}
        </a>
      )}
      {group.primary.caseId && (
        <a
          href="#"
          style={ACCENT_LINK_STYLE}
          onClick={(event) => {
            event.preventDefault();
            onOpen(group);
          }}
        >
          {t("dailyBrief.entry.openInvestmentCase")} →
        </a>
      )}
    </Stack>
  );
}

/** Phase 7, Section 2: "Atlas is watching today" -- forward-looking
 * catalysts that may materially affect a holding. No scheduled-catalyst
 * data source exists anywhere in this codebase today (`CanonicalAnalysis
 * .catalysts` is an explicit `UnavailableCapability`, and every
 * leadership-change event's own `effective_date`/`announcement_date` is
 * hardcoded `None`) -- a documented structural gap, not an oversight
 * this sprint invents data to paper over. This section therefore always
 * shows the honest calm state; wiring it to real data is future work
 * once a catalyst-aware provider exists. */
function AtlasIsWatchingTodaySection() {
  const { t } = useTranslation();
  return (
    <Stack gap="metadata">
      <Heading level={2}>{t("dailyBrief.watchingToday.heading")}</Heading>
      <Text color="secondary">{t("dailyBrief.watchingToday.calm")}</Text>
    </Stack>
  );
}

/** RC-3, Phase 2 -- the former "N things need your attention today"
 * line directly contradicted "Since your last visit" showing 1 real
 * change: two competing definitions of "attention" on the same page.
 * Every field this used to derive that count (`attentionCount` from
 * raw agenda priorities, `watchlistOpportunityCount`, `cashWeightPercent`)
 * still exists on `PortfolioSummaryView` and is still shown -- on
 * Portfolio/Watchlist, the pages that actually own current portfolio
 * state (RC-3, Phase 1). This section now states one calm, factual
 * count Daily Brief is entitled to: how many holdings Atlas keeps
 * under ongoing review. No data was removed, only what this specific
 * page renders from it. */
function PortfolioSummarySection({ agenda }: { agenda: DailyBriefAgendaView }) {
  const { t } = useTranslation();
  return (
    <Text color="tertiary">{t("dailyBriefAgenda.summary.holdingsMonitored", { count: agenda.summary.holdingsCount })}</Text>
  );
}
