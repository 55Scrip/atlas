import { useEffect, useState, type CSSProperties, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Container, Divider, Heading, Inline, Label, Link, Stack, StatusBadge, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import {
  deriveActivity,
  type ActivityEvent,
  type DecisionRecord,
  type HoldingLite,
  type OutcomeRecord,
  type TradeLogEntry,
} from "../activity/deriveActivity";
import {
  BUSINESS_CATEGORY_KEY,
  BUSINESS_STATUS_KEY,
  describeChange,
  HIGHLIGHT_KIND_KEY,
  OPEN_QUESTION_ORIGIN_KEY,
  VALUATION_STATUS_KEY,
  type AnalysisBusinessStatus,
  type AnalysisHighlightKind,
  type AnalysisOpenQuestionOrigin,
  type AnalysisThesisImpact,
  type AnalysisValuationStatus,
  type ChangeFindingView,
} from "../changeIntelligence/describeChange";
import {
  buildObservedPropertiesByDecisionId,
  type ObservedDecisionPropertiesResponse,
  type ObservedDecisionPropertyView,
  type ObservedPropertyScope,
} from "../history/deriveObservedDecisionProperties";
import {
  confirmSecuritySelection,
  correctSecuritySelection,
  fetchSecurityConfirmation,
  fetchSecurityDiscoveryCandidates,
  revokeSecurityConfirmation,
  type ConfirmedSecuritySelectionView,
  type SecurityCandidateView,
} from "../history/securityConfirmationApi";

/** Visual Fidelity Pass -- matches Portfolio/Investment Case/Daily
 * Brief/Discovery's own accent link treatment. */
const ACCENT_LINK_STYLE = { color: "var(--global-color-accent)", textDecoration: "none", fontSize: "var(--type-body-min-size)" } as const;

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

interface PortfolioViewLite {
  holdings: HoldingLite[];
}

type FetchStatus<T> =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "loaded"; data: T };

type StatusFilter = "all" | "open" | "completed";
type TypeFilter = "all" | "BUY" | "SELL" | "HOLD";
type SortDirection = "newest" | "oldest";
type KindFilter = "all" | "decisions" | "investmentCases";

const KIND_LABEL_KEY: Record<ActivityEvent["kind"], TranslationKey> = {
  decision: "history.row.kindDecision",
  outcome: "history.row.kindOutcome",
  trade: "history.row.kindTrade",
};

const DECISION_TYPE_KEY: Record<string, TranslationKey> = {
  BUY: "investmentCase.decision.typeBuy",
  SELL: "investmentCase.decision.typeSell",
  HOLD: "investmentCase.decision.typeHold",
  WATCH: "investmentCase.decision.typeWatch",
  PASS: "investmentCase.decision.typePass",
};

const HEADLINE_KEY: Record<AnalysisThesisImpact, TranslationKey> = {
  strengthened: "history.analytical.headline.strengthened",
  weakened: "history.analytical.headline.weakened",
  mixed: "history.analytical.headline.mixed",
  unchanged: "history.analytical.headline.unchanged",
};

// History v1 (analysis_engine/investment_case_history.py, GET
// /history/analysis): a read-only presentation layer over persisted
// Investment Case snapshots -- one entry per snapshot, across every
// Case that exists because of Portfolio or Watchlist membership
// (already deduplicated server-side). Every field below is a direct
// read of the backend response; this page computes nothing analytical
// -- see that module's own "History does not reason" doctrine.
interface HistoricalAnalysisEntryView {
  caseId: string;
  ticker: string | null;
  snapshotId: string;
  capturedAt: string;
  isBaseline: boolean;
  thesisImpact: AnalysisThesisImpact;
  summary: string;
  changeCount: number;
  changes: ChangeFindingView[];
  atlasThesisNarrative: string | null;
  atlasThesisPosture: string | null;
  strengths: AnalysisHighlightKind[];
  risks: AnalysisHighlightKind[];
  openQuestions: AnalysisOpenQuestionOrigin[];
  businessCategoryStates: { category: string; status: string; findingId: string }[];
  riskCategoryStates: { category: string; status: string; findingId: string }[];
  valuationStatus: AnalysisValuationStatus;
  currentYield: number | null;
}

interface AnalyticalHistoryView {
  generatedAt: string;
  entries: HistoricalAnalysisEntryView[];
}

type TimelineRow =
  | { kind: "activity"; date: string; event: ActivityEvent }
  | { kind: "analytical"; date: string; entry: HistoricalAnalysisEntryView };

const TIMELINE_PREVIEW_COUNT = 8;
/** Matches the approved screen's own two-up "Decision Reviews" layout. */
const MAX_REVIEWS = 4;

type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

/** Locale threaded from the app's own language toggle (`useTranslation`)
 * rather than `undefined` -- so switching Atlas to Swedish also
 * switches these dates, instead of silently following whatever the
 * browser/OS happens to be set to (Cross-Workspace Consistency
 * Cleanup; matches Investment Case's own `formatRelativeTime(date, t)`
 * precedent). */
function formatDate(iso: string, locale: string): string {
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return parsed.toLocaleDateString(locale, { month: "short", day: "numeric" });
}

/**
 * History (Sprint 4 investor activity + History v1 analytical
 * timeline): one chronological record combining an investor's own
 * activity (Decisions/Outcomes/Trades, from `deriveActivity` over
 * `/api/decisions`, `/api/outcomes`, `/api/alpha-portfolio/trade-log`)
 * with Atlas's own analytical history for every Case it covers (from
 * `GET /api/history/analysis`). The two are deliberately kept
 * type-distinct throughout -- a company's analytical state changing
 * ("Growth weakened") is never rendered or filtered as if it were an
 * investor action ("Investor sold 25%"), even though both now appear
 * in the same list. No new backend endpoint was needed for the
 * investor-activity half; the analytical half reads the one new,
 * narrowly-scoped read-only endpoint History v1 introduced.
 *
 * Visual Fidelity Pass: flat, dense, typography-led composition
 * (matching Portfolio/Investment Case/Daily Brief/Discovery), built
 * only from what's real. The approved Figma concept's fabricated hero
 * statistics, "Evidence at Decision" counts, "Atlas Recommendation"
 * directions, editorial "Lesson" text, Learning Patterns, Strategy
 * Evolution, and ranked Outcomes have no backing data or computation
 * anywhere in this codebase and are omitted entirely rather than
 * faked or shown as placeholders. "Recent Activity" is not duplicated
 * as a separate section -- it is the same Timeline data Decision
 * Timeline already renders. No embedded Ask Atlas UI.
 */
export function HistoryPage() {
  const { t, language } = useTranslation();
  const locale = language === "sv" ? "sv-SE" : "en-US";
  const navigate = useNavigate();

  const [decisionsStatus, setDecisionsStatus] = useState<FetchStatus<DecisionRecord[]>>({
    kind: "loading",
  });
  const [outcomesStatus, setOutcomesStatus] = useState<FetchStatus<OutcomeRecord[]>>({
    kind: "loading",
  });
  const [tradesStatus, setTradesStatus] = useState<FetchStatus<TradeLogEntry[]>>({
    kind: "loading",
  });
  const [portfolioStatus, setPortfolioStatus] = useState<FetchStatus<PortfolioViewLite>>({
    kind: "loading",
  });
  const [analyticalStatus, setAnalyticalStatus] = useState<FetchStatus<AnalyticalHistoryView>>({
    kind: "loading",
  });
  // Observed Decision Properties (Sprint 14): deliberately a separate,
  // 6th fetch kept OUT of `statuses` below. Decision Reviews must keep
  // rendering from the five statuses above whether this one is still
  // loading, has failed, or has loaded -- this is factual secondary
  // context on an already-real Decision/Outcome, not a page-blocking
  // dependency (see Sprint 14 Phase 16/17).
  const [observedPropertiesStatus, setObservedPropertiesStatus] = useState<
    FetchStatus<ObservedDecisionPropertiesResponse>
  >({ kind: "loading" });

  const [kindFilter, setKindFilter] = useState<KindFilter>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [sortDirection, setSortDirection] = useState<SortDirection>("newest");
  const [expandedSnapshotIds, setExpandedSnapshotIds] = useState<Set<string>>(new Set());
  const [timelineExpanded, setTimelineExpanded] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/decisions", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<DecisionRecord[]>;
      })
      .then((data) => setDecisionsStatus({ kind: "loaded", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setDecisionsStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/outcomes", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<OutcomeRecord[]>;
      })
      .then((data) => setOutcomesStatus({ kind: "loaded", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setOutcomesStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-portfolio/trade-log", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<TradeLogEntry[]>;
      })
      .then((data) => setTradesStatus({ kind: "loaded", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setTradesStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-portfolio", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<PortfolioViewLite>;
      })
      .then((data) => setPortfolioStatus({ kind: "loaded", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setPortfolioStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/history/analysis", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<AnalyticalHistoryView>;
      })
      .then((data) => setAnalyticalStatus({ kind: "loaded", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setAnalyticalStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/observed-decision-properties", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
        return response.json() as Promise<ObservedDecisionPropertiesResponse>;
      })
      .then((data) => setObservedPropertiesStatus({ kind: "loaded", data }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setObservedPropertiesStatus({
          kind: "error",
          message: error instanceof Error ? error.message : t("common.unknownError"),
        });
      });
    return () => controller.abort();
  }, []);

  const statuses = [decisionsStatus, outcomesStatus, tradesStatus, portfolioStatus, analyticalStatus];
  const isLoading = statuses.some((s) => s.kind === "loading");
  const firstError = statuses.find((s) => s.kind === "error") as
    | { kind: "error"; message: string }
    | undefined;

  const holdings = portfolioStatus.kind === "loaded" ? portfolioStatus.data.holdings : [];
  const holdingByCaseId = new Map(
    holdings.filter((h): h is HoldingLite & { caseId: string } => h.caseId !== null).map((h) => [h.caseId, h]),
  );

  const activityEvents =
    decisionsStatus.kind === "loaded" &&
    outcomesStatus.kind === "loaded" &&
    tradesStatus.kind === "loaded" &&
    portfolioStatus.kind === "loaded"
      ? deriveActivity(decisionsStatus.data, outcomesStatus.data, tradesStatus.data, holdings)
      : [];
  const analyticalEntries = analyticalStatus.kind === "loaded" ? analyticalStatus.data.entries : [];

  const isEmpty = activityEvents.length === 0 && analyticalEntries.length === 0;

  const filteredActivity =
    kindFilter === "investmentCases"
      ? []
      : activityEvents.filter((event) => {
          if (statusFilter !== "all" && event.status !== statusFilter) return false;
          if (typeFilter !== "all" && event.decisionType !== typeFilter) return false;
          return true;
        });
  const filteredAnalytical = kindFilter === "decisions" ? [] : analyticalEntries;

  const rows: TimelineRow[] = [
    ...filteredActivity.map((event): TimelineRow => ({ kind: "activity", date: event.date, event })),
    ...filteredAnalytical.map((entry): TimelineRow => ({ kind: "analytical", date: entry.capturedAt, entry })),
  ];
  const sortedRows = [...rows].sort((a, b) => {
    const delta = new Date(a.date).getTime() - new Date(b.date).getTime();
    return sortDirection === "newest" ? -delta : delta;
  });
  const noneMatchFilter = !isEmpty && sortedRows.length === 0;
  const visibleRows = timelineExpanded ? sortedRows : sortedRows.slice(0, TIMELINE_PREVIEW_COUNT);
  const hasMoreRows = sortedRows.length > TIMELINE_PREVIEW_COUNT;

  // Real aggregate counts only -- no ratios, no attribution, no
  // performance claims (see module doc).
  const decisionCount = decisionsStatus.kind === "loaded" ? decisionsStatus.data.length : 0;
  const companyTickers = new Set<string>();
  activityEvents.forEach((event) => companyTickers.add(event.security));
  analyticalEntries.forEach((entry) => companyTickers.add(entry.ticker ?? entry.caseId));
  const allDates = [...activityEvents.map((e) => e.date), ...analyticalEntries.map((e) => e.capturedAt)]
    .map((iso) => new Date(iso))
    .filter((d) => !Number.isNaN(d.getTime()));
  const earliestDate = allDates.length > 0 ? new Date(Math.min(...allDates.map((d) => d.getTime()))) : null;

  // Observed Decision Properties (Sprint 14): a plain lookup indexed
  // once per render from whatever has loaded so far -- empty until the
  // 6th fetch above resolves, never blocking or altering Decision
  // Review card selection/ordering itself.
  const observedPropertiesByDecisionId =
    observedPropertiesStatus.kind === "loaded"
      ? buildObservedPropertiesByDecisionId(observedPropertiesStatus.data.properties)
      : new Map<string, ObservedDecisionPropertyView[]>();

  // Decision Reviews -- the most recent decisions that have both a
  // real recorded thesis (Decision.reason) and a real recorded
  // outcome (Outcome.statement). A deterministic filter over existing
  // fields, never an editorial "worth reflecting on" judgment.
  const decisionReviews =
    decisionsStatus.kind === "loaded" && outcomesStatus.kind === "loaded"
      ? decisionsStatus.data
          .map((decision) => ({
            decision,
            outcome: outcomesStatus.data.find((o) => o.decisionId === decision.id) ?? null,
          }))
          .filter(
            (entry): entry is { decision: DecisionRecord; outcome: OutcomeRecord } =>
              entry.outcome !== null && entry.decision.reason.trim() !== "",
          )
          .sort((a, b) => new Date(b.decision.decidedAt).getTime() - new Date(a.decision.decidedAt).getTime())
          .slice(0, MAX_REVIEWS)
      : [];

  function openEvent(event: ActivityEvent) {
    if (!event.caseId) return;
    navigate(`/investment-case/${event.caseId}`, { state: { origin: "history" } });
  }

  function openCase(caseId: string) {
    navigate(`/investment-case/${caseId}`, { state: { origin: "history" } });
  }

  function toggleDetails(snapshotId: string) {
    setExpandedSnapshotIds((current) => {
      const next = new Set(current);
      if (next.has(snapshotId)) next.delete(snapshotId);
      else next.add(snapshotId);
      return next;
    });
  }

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        <Heading level={3} style={PAGE_TITLE_STYLE}>
          {t("history.title")}
        </Heading>

        {isLoading && (
          <Text role="status" aria-live="polite">
            {t("common.loading")}
          </Text>
        )}
        {firstError && (
          <Text color="tertiary" role="alert">
            {t("history.loadError", { message: firstError.message })}
          </Text>
        )}

        {!isLoading && !firstError && (
          <>
            {isEmpty ? (
              <Stack gap="metadata">
                <Text color="secondary">{t("history.empty")}</Text>
                <Link
                  href="#"
                  style={ACCENT_LINK_STYLE}
                  onClick={(event) => {
                    event.preventDefault();
                    navigate("/portfolio");
                  }}
                >
                  {t("history.empty.portfolioLink")}
                </Link>
              </Stack>
            ) : (
              <>
                {decisionCount > 0 && earliestDate && (
                  <>
                    <Text as="p">
                      {t("history.summary", {
                        count: decisionCount,
                        companies: companyTickers.size,
                        since: earliestDate.toLocaleDateString(locale, { month: "long", year: "numeric" }),
                      })}
                    </Text>
                    <Divider tone="hairline" />
                  </>
                )}

                <Stack gap="metadata">
                  <Inline gap="row" wrap align="baseline" style={{ justifyContent: "space-between" }}>
                    <Label>{t("history.timeline.heading")}</Label>
                    <Inline gap="row" wrap>
                      <FilterTab active={sortDirection === "newest"} onClick={() => setSortDirection("newest")}>
                        {t("history.sort.newest")}
                      </FilterTab>
                      <Text color="tertiary">/</Text>
                      <FilterTab active={sortDirection === "oldest"} onClick={() => setSortDirection("oldest")}>
                        {t("history.sort.oldest")}
                      </FilterTab>
                    </Inline>
                  </Inline>

                  <Inline gap="row" wrap>
                    <FilterTab active={kindFilter === "all"} onClick={() => setKindFilter("all")}>
                      {t("history.scope.all")}
                    </FilterTab>
                    <Text color="tertiary">·</Text>
                    <FilterTab active={kindFilter === "decisions"} onClick={() => setKindFilter("decisions")}>
                      {t("history.scope.decisions")}
                    </FilterTab>
                    <Text color="tertiary">·</Text>
                    <FilterTab active={kindFilter === "investmentCases"} onClick={() => setKindFilter("investmentCases")}>
                      {t("history.scope.investmentCases")}
                    </FilterTab>
                    {kindFilter !== "investmentCases" && (
                      <>
                        <Text color="tertiary">|</Text>
                        <FilterTab active={statusFilter === "all"} onClick={() => setStatusFilter("all")}>
                          {t("history.filter.all")}
                        </FilterTab>
                        <Text color="tertiary">·</Text>
                        <FilterTab active={statusFilter === "open"} onClick={() => setStatusFilter("open")}>
                          {t("history.filter.open")}
                        </FilterTab>
                        <Text color="tertiary">·</Text>
                        <FilterTab active={statusFilter === "completed"} onClick={() => setStatusFilter("completed")}>
                          {t("history.filter.completed")}
                        </FilterTab>
                        <Text color="tertiary">|</Text>
                        <FilterTab active={typeFilter === "all"} onClick={() => setTypeFilter("all")}>
                          {t("history.filter.all")}
                        </FilterTab>
                        <Text color="tertiary">·</Text>
                        <FilterTab active={typeFilter === "BUY"} onClick={() => setTypeFilter("BUY")}>
                          {t("investmentCase.decision.typeBuy")}
                        </FilterTab>
                        <Text color="tertiary">·</Text>
                        <FilterTab active={typeFilter === "SELL"} onClick={() => setTypeFilter("SELL")}>
                          {t("investmentCase.decision.typeSell")}
                        </FilterTab>
                        <Text color="tertiary">·</Text>
                        <FilterTab active={typeFilter === "HOLD"} onClick={() => setTypeFilter("HOLD")}>
                          {t("investmentCase.decision.typeHold")}
                        </FilterTab>
                      </>
                    )}
                  </Inline>

                  {noneMatchFilter && <Text color="secondary">{t("history.noneMatchFilter")}</Text>}
                  {kindFilter === "investmentCases" && analyticalEntries.length === 0 && (
                    <Text color="secondary">{t("history.analytical.emptyOnly")}</Text>
                  )}

                  {visibleRows.map((row) =>
                    row.kind === "activity" ? (
                      <ActivityTimelineRow
                        key={`activity:${row.event.id}`}
                        event={row.event}
                        onOpen={() => openEvent(row.event)}
                        t={t}
                        locale={locale}
                      />
                    ) : (
                      <AnalyticalTimelineRow
                        key={`analytical:${row.entry.snapshotId}`}
                        entry={row.entry}
                        expanded={expandedSnapshotIds.has(row.entry.snapshotId)}
                        onToggleDetails={() => toggleDetails(row.entry.snapshotId)}
                        onOpenCase={() => openCase(row.entry.caseId)}
                        t={t}
                        locale={locale}
                      />
                    ),
                  )}

                  {hasMoreRows && !timelineExpanded && (
                    <Link
                      href="#"
                      style={ACCENT_LINK_STYLE}
                      onClick={(event) => {
                        event.preventDefault();
                        setTimelineExpanded(true);
                      }}
                    >
                      {t("history.timeline.viewFull")} →
                    </Link>
                  )}
                </Stack>

                {decisionReviews.length > 0 && (
                  <>
                    <Divider tone="hairline" />
                    <Stack gap="metadata">
                      <Label>{t("history.reviews.heading")}</Label>
                      <Text color="tertiary">{t("history.reviews.subheading")}</Text>
                      <Inline gap="inter-section" wrap align="start">
                        {decisionReviews.map(({ decision, outcome }) => (
                          <DecisionReviewCard
                            key={decision.id}
                            decision={decision}
                            outcome={outcome}
                            ticker={holdingByCaseId.get(decision.caseId)?.ticker ?? decision.subject}
                            observedProperties={observedPropertiesByDecisionId.get(decision.id) ?? []}
                            onOpen={() => openCase(decision.caseId)}
                            t={t}
                            locale={locale}
                          />
                        ))}
                      </Inline>
                    </Stack>
                  </>
                )}
              </>
            )}
          </>
        )}
      </Stack>
    </Container>
  );
}

/** Small text tab, bare `<button>` reset -- same idiom as Investment
 * Case's `TabLabel`, kept page-local since neither page shares a
 * component for it yet. */
function FilterTab({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        background: "none",
        border: "none",
        padding: 0,
        margin: 0,
        cursor: "pointer",
        fontFamily: "var(--type-family-metadata)",
        fontSize: "var(--type-body-min-size)",
        color: active ? "var(--color-text-primary)" : "var(--color-text-tertiary)",
        textDecoration: active ? "underline" : "none",
      }}
    >
      {children}
    </button>
  );
}

/** One investor-activity row (Decision/Outcome/Trade) -- dense,
 * clickable, real fields only. `decisionType` is translated into the
 * same verb vocabulary the rest of the app already uses (Buy/Sell/
 * Hold/Watch/Pass) rather than inventing Figma's untethered
 * Added/Trimmed/Validated taxonomy. */
function ActivityTimelineRow({
  event,
  onOpen,
  t,
  locale,
}: {
  event: ActivityEvent;
  onOpen: () => void;
  t: Translate;
  locale: string;
}) {
  const verb =
    event.kind === "decision" && event.decisionType && DECISION_TYPE_KEY[event.decisionType]
      ? t(DECISION_TYPE_KEY[event.decisionType]!)
      : t(KIND_LABEL_KEY[event.kind]);
  return (
    <Stack gap="metadata">
      <Link
        href="#"
        style={{ ...ACCENT_LINK_STYLE, color: "var(--color-text-primary)", display: "block" }}
        onClick={(clickEvent) => {
          clickEvent.preventDefault();
          onOpen();
        }}
      >
        <Inline gap="row" align="baseline" wrap>
          <Text color="tertiary" style={{ minWidth: "60px" }}>
            {formatDate(event.date, locale)}
          </Text>
          <Text color="secondary" style={{ minWidth: "84px" }}>
            {verb}
          </Text>
          <Text as="span" style={{ fontWeight: 600 }}>
            {event.security}
          </Text>
          {event.summary && <Text color="secondary">— {event.summary}</Text>}
        </Inline>
      </Link>
      <Divider tone="hairline" />
    </Stack>
  );
}

/** One analytical timeline entry -- either a Case's baseline (its
 * first-ever recorded snapshot, never itself reported as a change) or
 * a real transition between two consecutive snapshots. Every fact
 * rendered here is a direct read of the backend's own persisted
 * `AnalyticalSnapshot`/`ChangeIntelligence` state (see this route's own
 * docstring) -- nothing is recomputed, and expanding a row never
 * fetches or shows the *current* Investment Case in place of the
 * historical one. */
function AnalyticalTimelineRow({
  entry,
  expanded,
  onToggleDetails,
  onOpenCase,
  t,
  locale,
}: {
  entry: HistoricalAnalysisEntryView;
  expanded: boolean;
  onToggleDetails: () => void;
  onOpenCase: () => void;
  t: Translate;
  locale: string;
}) {
  const company = entry.ticker ?? t("dailyBrief.entry.unknownCompany");
  const verb = entry.isBaseline ? t("history.analytical.baseline") : t(HEADLINE_KEY[entry.thesisImpact]);
  const description = entry.isBaseline
    ? t("history.analytical.baselineDescription", { company })
    : entry.changes[0]
      ? describeChange(entry.changes[0], t)
      : entry.summary;
  const growthState = entry.businessCategoryStates.find((s) => s.category === "growth");

  return (
    <Stack gap="metadata">
      <Inline gap="row" align="baseline" wrap style={{ justifyContent: "space-between" }}>
        <Inline gap="row" align="baseline" wrap>
          <Text color="tertiary" style={{ minWidth: "60px" }}>
            {formatDate(entry.capturedAt, locale)}
          </Text>
          <Text color="secondary" style={{ minWidth: "84px" }}>
            {verb}
          </Text>
          <Text as="span" style={{ fontWeight: 600 }}>
            {company}
          </Text>
          <Text color="secondary">— {description}</Text>
        </Inline>
        <Inline gap="row">
          <Link
            href="#"
            style={ACCENT_LINK_STYLE}
            onClick={(event) => {
              event.preventDefault();
              onToggleDetails();
            }}
          >
            {expanded ? t("history.analytical.hideDetails") : t("history.analytical.viewDetails")}
          </Link>
          <Link
            href="#"
            style={ACCENT_LINK_STYLE}
            onClick={(event) => {
              event.preventDefault();
              onOpenCase();
            }}
          >
            {t("dailyBrief.entry.openInvestmentCase")} →
          </Link>
        </Inline>
      </Inline>

      {expanded && (
        <Stack gap="metadata" style={{ paddingLeft: "var(--space-intra-section)" }}>
          <Label>{t("history.analytical.detail.thesisHeading")}</Label>
          <Text color="secondary" as="p">
            {entry.atlasThesisNarrative ?? t("history.analytical.detail.noThesis")}
          </Text>

          <Label>{t("history.analytical.detail.strengthsHeading")}</Label>
          <Text color="secondary" as="p">
            {entry.strengths.length === 0
              ? t("history.analytical.detail.empty")
              : entry.strengths.map((kind) => t(HIGHLIGHT_KIND_KEY[kind])).join(" · ")}
          </Text>

          <Label>{t("history.analytical.detail.risksHeading")}</Label>
          <Text color="secondary" as="p">
            {entry.risks.length === 0
              ? t("history.analytical.detail.empty")
              : entry.risks.map((kind) => t(HIGHLIGHT_KIND_KEY[kind])).join(" · ")}
          </Text>

          <Label>{t("history.analytical.detail.growthHeading")}</Label>
          <Text color="secondary" as="p">
            {growthState
              ? `${t(BUSINESS_CATEGORY_KEY.growth)}: ${t(BUSINESS_STATUS_KEY[growthState.status as AnalysisBusinessStatus])}`
              : t("history.analytical.detail.empty")}
          </Text>

          <Label>{t("history.analytical.detail.valuationHeading")}</Label>
          <Text color="secondary" as="p">
            {t(VALUATION_STATUS_KEY[entry.valuationStatus])}
          </Text>

          <Label>{t("history.analytical.detail.openQuestionsHeading")}</Label>
          <Text color="secondary" as="p">
            {entry.openQuestions.length === 0
              ? t("history.analytical.detail.empty")
              : entry.openQuestions.map((origin) => t(OPEN_QUESTION_ORIGIN_KEY[origin])).join(" · ")}
          </Text>
        </Stack>
      )}
      <Divider tone="hairline" />
    </Stack>
  );
}

/** One Decision Review -- real Original Thesis (`Decision.reason`) and
 * real recorded Outcome (`Outcome.statement`) only. No "Evidence at
 * Decision" count, no "Atlas Recommendation" direction, no editorial
 * "Lesson" -- none of those have a real field to read from (see module
 * doc). */
const SCOPE_LABEL_KEY: Record<ObservedPropertyScope, TranslationKey> = {
  single_company: "history.reviews.observedProperties.scope.singleCompany",
  portfolio_wide: "history.reviews.observedProperties.scope.portfolioWide",
};

function DecisionReviewCard({
  decision,
  outcome,
  ticker,
  observedProperties,
  onOpen,
  t,
  locale,
}: {
  decision: DecisionRecord;
  outcome: OutcomeRecord;
  ticker: string;
  observedProperties: ObservedDecisionPropertyView[];
  onOpen: () => void;
  t: Translate;
  locale: string;
}) {
  const verb = DECISION_TYPE_KEY[decision.decisionType] ? t(DECISION_TYPE_KEY[decision.decisionType]!) : decision.decisionType;
  return (
    <div style={{ flex: "1 1 340px", minWidth: 0 }}>
      <Stack gap="metadata">
        <Inline gap="row" align="baseline" wrap style={{ justifyContent: "space-between" }}>
          <Text as="span" style={{ fontWeight: 600 }}>
            {ticker}
          </Text>
          <Text color="tertiary">
            {verb} · {formatDate(decision.decidedAt, locale)}
          </Text>
        </Inline>

        <SecurityConfirmationSection decisionId={decision.id} subject={decision.subject} t={t} />
        <Divider tone="hairline" />

        <Label>{t("history.reviews.originalThesis")}</Label>
        <Text color="secondary" as="p">
          {decision.reason}
        </Text>

        <Label>{t("history.reviews.outcome")}</Label>
        <Text color="secondary" as="p">
          {outcome.statement}
        </Text>

        <Link
          href="#"
          style={ACCENT_LINK_STYLE}
          onClick={(event) => {
            event.preventDefault();
            onOpen();
          }}
        >
          {t("dailyBrief.entry.openInvestmentCase")} →
        </Link>

        {observedProperties.length > 0 && (
          <>
            <Divider tone="hairline" />
            <Label>{t("history.reviews.observedProperties.heading")}</Label>
            {observedProperties.map((property) => (
              <Stack key={property.propertyType} gap="metadata">
                <Text color="secondary" as="p">
                  {property.factualDescription}
                </Text>
                <Inline gap="row" wrap align="baseline">
                  <StatusBadge label={t(SCOPE_LABEL_KEY[property.scope])} tone="neutral" />
                  <Text color="tertiary">
                    {t("history.reviews.observedProperties.dateRange", {
                      from: formatDate(property.firstObservedAt, locale),
                      to: formatDate(property.lastObservedAt, locale),
                    })}
                  </Text>
                  {property.sampleSizeWarning && (
                    <Text color="tertiary">{t("history.reviews.observedProperties.smallSample")}</Text>
                  )}
                </Inline>
              </Stack>
            ))}
            <Text color="tertiary">{t("history.reviews.observedProperties.limitation")}</Text>
          </>
        )}
      </Stack>
    </div>
  );
}

/** Sprint 21 (Explicit Security Confirmation -- First Product Flow): the
 * one frontend surface for Sprint 19's discovery + Sprint 20's
 * confirmation. `subject` is rendered verbatim as `Decision.subject`
 * (never the resolved holding ticker `DecisionReviewCard`'s own header
 * shows) -- "Recorded as" must reflect exactly what was historically
 * recorded, per Sprint 21's own non-negotiable ground rule that
 * `Decision.subject` is never rewritten.
 *
 * State is entirely local and Decision-scoped: nothing here is shared
 * across cards, nothing here propagates a confirmation to any sibling
 * Decision, and "Not this security" is never a backend call -- before a
 * confirmation exists there is nothing to revoke, only a candidate to
 * stop looking at.
 *
 * Sprint 22 (Correction, Revocation & Historical Integrity) adds two
 * explicit actions from the confirmed state: "Change selection" (runs
 * discovery again, then calls `correctSecuritySelection` instead of
 * `confirmSecuritySelection` -- the backend's own `correct()` requires
 * an active confirmation and appends a revoked+confirmed event pair,
 * never rewriting the earlier one) and "Remove confirmation" (calls
 * `revokeSecurityConfirmation`, returning the card to the idle "Find
 * security" state). Every discovery/confirm state below now carries a
 * `mode: "confirm" | "correct"` so the same render branches serve both
 * the first-confirmation flow and the change-selection flow without
 * duplicating markup -- only which API function gets called differs. */
type SecurityConfirmationState =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "confirmed"; selection: ConfirmedSecuritySelectionView }
  | { kind: "revoking"; selection: ConfirmedSecuritySelectionView }
  | { kind: "revokeError"; selection: ConfirmedSecuritySelectionView }
  | { kind: "idle" }
  | { kind: "discovering"; mode: "confirm" | "correct" }
  | { kind: "discoveryError"; mode: "confirm" | "correct" }
  | { kind: "discovered"; candidates: SecurityCandidateView[]; mode: "confirm" | "correct" }
  | { kind: "confirming"; candidates: SecurityCandidateView[]; pendingTicker: string; mode: "confirm" | "correct" }
  | { kind: "confirmError"; candidates: SecurityCandidateView[]; mode: "confirm" | "correct" };

function SecurityConfirmationSection({
  decisionId,
  subject,
  t,
}: {
  decisionId: string;
  subject: string;
  t: Translate;
}) {
  const [state, setState] = useState<SecurityConfirmationState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchSecurityConfirmation(decisionId, controller.signal)
      .then((selection) => setState(selection ? { kind: "confirmed", selection } : { kind: "idle" }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ kind: "error" });
      });
    return () => controller.abort();
  }, [decisionId]);

  function findSecurity(mode: "confirm" | "correct") {
    setState({ kind: "discovering", mode });
    fetchSecurityDiscoveryCandidates(subject)
      .then((candidates) => setState({ kind: "discovered", candidates, mode }))
      .catch(() => setState({ kind: "discoveryError", mode }));
  }

  function notThisSecurity(candidates: SecurityCandidateView[], ticker: string, mode: "confirm" | "correct") {
    const remaining = candidates.filter((candidate) => candidate.ticker !== ticker);
    setState({ kind: "discovered", candidates: remaining, mode });
  }

  function confirm(candidates: SecurityCandidateView[], candidate: SecurityCandidateView, mode: "confirm" | "correct") {
    setState({ kind: "confirming", candidates, pendingTicker: candidate.ticker, mode });
    const request = mode === "confirm" ? confirmSecuritySelection : correctSecuritySelection;
    request(decisionId, candidate)
      .then((selection) => setState({ kind: "confirmed", selection }))
      .catch(() => setState({ kind: "confirmError", candidates, mode }));
  }

  function removeConfirmation(selection: ConfirmedSecuritySelectionView) {
    setState({ kind: "revoking", selection });
    revokeSecurityConfirmation(decisionId)
      .then(() => setState({ kind: "idle" }))
      .catch(() => setState({ kind: "revokeError", selection }));
  }

  return (
    <Stack gap="metadata">
      <Label>{t("history.reviews.securityConfirmation.recordedAs")}</Label>
      <Text as="span" style={{ fontWeight: 600 }}>
        {subject}
      </Text>

      {state.kind === "loading" && <Text color="tertiary">{t("common.loading")}</Text>}
      {state.kind === "error" && (
        <Text color="tertiary" role="alert">
          {t("history.reviews.securityConfirmation.loadError")}
        </Text>
      )}

      {(state.kind === "confirmed" || state.kind === "revoking" || state.kind === "revokeError") && (
        <>
          <Label>{t("history.reviews.securityConfirmation.confirmedSelection")}</Label>
          <Text as="span">
            {state.selection.confirmedTicker} — {state.selection.confirmedDisplayName}
          </Text>
          <Text color="tertiary">{t("history.reviews.securityConfirmation.confirmedByYou")}</Text>
          <Inline gap="row" wrap>
            <Button
              variant="tertiary"
              disabled={state.kind === "revoking"}
              onClick={() => findSecurity("correct")}
            >
              {t("history.reviews.securityConfirmation.changeSelection")}
            </Button>
            <Button
              variant="tertiary"
              disabled={state.kind === "revoking"}
              onClick={() => removeConfirmation(state.selection)}
            >
              {t("history.reviews.securityConfirmation.removeConfirmation")}
            </Button>
          </Inline>
          {state.kind === "revokeError" && (
            <Text color="tertiary" role="alert">
              {t("history.reviews.securityConfirmation.revokeError")}
            </Text>
          )}
        </>
      )}

      {state.kind === "idle" && (
        <Button variant="tertiary" onClick={() => findSecurity("confirm")}>
          {t("history.reviews.securityConfirmation.findSecurity")}
        </Button>
      )}

      {state.kind === "discovering" && <Text color="tertiary">{t("common.loading")}</Text>}
      {state.kind === "discoveryError" && (
        <Text color="tertiary" role="alert">
          {t("history.reviews.securityConfirmation.discoveryError")}
        </Text>
      )}

      {(state.kind === "discovered" || state.kind === "confirming" || state.kind === "confirmError") && (
        <Stack gap="metadata">
          {state.mode === "correct" && (
            <Text color="tertiary">{t("history.reviews.securityConfirmation.changeSelectionNote")}</Text>
          )}
          {state.candidates.length === 0 ? (
            <Text color="tertiary">{t("history.reviews.securityConfirmation.noCandidateFound")}</Text>
          ) : (
            <Stack gap="metadata">
              {state.candidates.map((candidate) => (
                <Stack key={candidate.ticker} gap="metadata">
                  <Label>{t("history.reviews.securityConfirmation.possibleMatch")}</Label>
                  <Text as="span">
                    {candidate.ticker} — {candidate.displayName}
                  </Text>
                  <Inline gap="row" wrap>
                    <Button
                      variant="primary"
                      disabled={state.kind === "confirming"}
                      onClick={() => confirm(state.candidates, candidate, state.mode)}
                    >
                      {t("history.reviews.securityConfirmation.confirmThisSecurity")}
                    </Button>
                    <Button
                      variant="tertiary"
                      disabled={state.kind === "confirming"}
                      onClick={() => notThisSecurity(state.candidates, candidate.ticker, state.mode)}
                    >
                      {t("history.reviews.securityConfirmation.notThisSecurity")}
                    </Button>
                  </Inline>
                </Stack>
              ))}
            </Stack>
          )}
          {state.kind === "confirmError" && (
            <Text color="tertiary" role="alert">
              {t("history.reviews.securityConfirmation.confirmError")}
            </Text>
          )}
        </Stack>
      )}
    </Stack>
  );
}
