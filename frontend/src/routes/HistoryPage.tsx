import { useEffect, useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { Button, Container, Divider, Heading, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import {
  deriveActivity,
  sortActivity,
  type ActivityEvent,
  type DecisionRecord,
  type HoldingLite,
  type OutcomeRecord,
  type TradeLogEntry,
} from "../activity/deriveActivity";
import {
  BUSINESS_CATEGORY_KEY,
  BUSINESS_STATUS_KEY,
  CHANGE_DIRECTION_SYMBOL,
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
 */
export function HistoryPage() {
  const { t } = useTranslation();
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

  const [kindFilter, setKindFilter] = useState<KindFilter>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [sortDirection, setSortDirection] = useState<SortDirection>("newest");
  const [expandedSnapshotIds, setExpandedSnapshotIds] = useState<Set<string>>(new Set());

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

  const statuses = [decisionsStatus, outcomesStatus, tradesStatus, portfolioStatus, analyticalStatus];
  const isLoading = statuses.some((s) => s.kind === "loading");
  const firstError = statuses.find((s) => s.kind === "error") as
    | { kind: "error"; message: string }
    | undefined;

  const activityEvents =
    decisionsStatus.kind === "loaded" &&
    outcomesStatus.kind === "loaded" &&
    tradesStatus.kind === "loaded" &&
    portfolioStatus.kind === "loaded"
      ? deriveActivity(
          decisionsStatus.data,
          outcomesStatus.data,
          tradesStatus.data,
          portfolioStatus.data.holdings,
        )
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
    <Container>
      <Stack gap="inter-section">
        <Heading level={1}>{t("history.title")}</Heading>

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
            <Surface tier="primary">
              <Stack gap="inter-section">
                <div>
                  <Button
                    variant={kindFilter === "all" ? "primary" : "tertiary"}
                    onClick={() => setKindFilter("all")}
                  >
                    {t("history.scope.all")}
                  </Button>{" "}
                  <Button
                    variant={kindFilter === "decisions" ? "primary" : "tertiary"}
                    onClick={() => setKindFilter("decisions")}
                  >
                    {t("history.scope.decisions")}
                  </Button>{" "}
                  <Button
                    variant={kindFilter === "investmentCases" ? "primary" : "tertiary"}
                    onClick={() => setKindFilter("investmentCases")}
                  >
                    {t("history.scope.investmentCases")}
                  </Button>
                </div>
                {kindFilter !== "investmentCases" && (
                  <>
                    <div>
                      <Button
                        variant={statusFilter === "all" ? "primary" : "tertiary"}
                        onClick={() => setStatusFilter("all")}
                      >
                        {t("history.filter.all")}
                      </Button>{" "}
                      <Button
                        variant={statusFilter === "open" ? "primary" : "tertiary"}
                        onClick={() => setStatusFilter("open")}
                      >
                        {t("history.filter.open")}
                      </Button>{" "}
                      <Button
                        variant={statusFilter === "completed" ? "primary" : "tertiary"}
                        onClick={() => setStatusFilter("completed")}
                      >
                        {t("history.filter.completed")}
                      </Button>
                    </div>
                    <div>
                      <Button
                        variant={typeFilter === "all" ? "primary" : "tertiary"}
                        onClick={() => setTypeFilter("all")}
                      >
                        {t("history.filter.all")}
                      </Button>{" "}
                      <Button
                        variant={typeFilter === "BUY" ? "primary" : "tertiary"}
                        onClick={() => setTypeFilter("BUY")}
                      >
                        {t("investmentCase.decision.typeBuy")}
                      </Button>{" "}
                      <Button
                        variant={typeFilter === "SELL" ? "primary" : "tertiary"}
                        onClick={() => setTypeFilter("SELL")}
                      >
                        {t("investmentCase.decision.typeSell")}
                      </Button>{" "}
                      <Button
                        variant={typeFilter === "HOLD" ? "primary" : "tertiary"}
                        onClick={() => setTypeFilter("HOLD")}
                      >
                        {t("investmentCase.decision.typeHold")}
                      </Button>
                    </div>
                  </>
                )}
                <div>
                  <Button
                    variant={sortDirection === "newest" ? "primary" : "tertiary"}
                    onClick={() => setSortDirection("newest")}
                  >
                    {t("history.sort.newest")}
                  </Button>{" "}
                  <Button
                    variant={sortDirection === "oldest" ? "primary" : "tertiary"}
                    onClick={() => setSortDirection("oldest")}
                  >
                    {t("history.sort.oldest")}
                  </Button>
                </div>
              </Stack>
            </Surface>

            <Divider />

            <Surface tier="primary">
              <Stack gap="inter-section">
                {isEmpty && (
                  <Stack gap="inter-section">
                    <Text color="secondary">{t("history.empty")}</Text>
                    <RouterLink to="/portfolio">{t("history.empty.portfolioLink")}</RouterLink>
                  </Stack>
                )}
                {noneMatchFilter && <Text color="secondary">{t("history.noneMatchFilter")}</Text>}
                {sortedRows.map((row) =>
                  row.kind === "activity" ? (
                    <div key={`activity:${row.event.id}`}>
                      <Button variant="tertiary" onClick={() => openEvent(row.event)}>
                        {row.event.security}
                      </Button>
                      <Text>{t(KIND_LABEL_KEY[row.event.kind])}</Text>
                      <Text color="secondary" as="p">
                        {row.event.decisionType &&
                          (DECISION_TYPE_KEY[row.event.decisionType]
                            ? t(DECISION_TYPE_KEY[row.event.decisionType]!)
                            : row.event.decisionType)}
                        {" · "}
                        {row.event.status === "open" ? t("history.status.open") : t("history.status.completed")}
                        {" · "}
                        {row.event.date}
                      </Text>
                      {row.event.summary && (
                        <Text color="secondary" as="p">
                          {row.event.summary}
                        </Text>
                      )}
                      <Divider tone="hairline" />
                    </div>
                  ) : (
                    <AnalyticalHistoryRow
                      key={`analytical:${row.entry.snapshotId}`}
                      entry={row.entry}
                      expanded={expandedSnapshotIds.has(row.entry.snapshotId)}
                      onToggleDetails={() => toggleDetails(row.entry.snapshotId)}
                      onOpenCase={() => openCase(row.entry.caseId)}
                      t={t}
                    />
                  ),
                )}
                {!isEmpty && kindFilter === "investmentCases" && analyticalEntries.length === 0 && (
                  <Text color="secondary">{t("history.analytical.emptyOnly")}</Text>
                )}
              </Stack>
            </Surface>
          </>
        )}
      </Stack>
    </Container>
  );
}

type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

/** One analytical timeline entry -- either a Case's baseline (its
 * first-ever recorded snapshot, never itself reported as a change) or
 * a real transition between two consecutive snapshots. Every fact
 * rendered here is a direct read of the backend's own persisted
 * `AnalyticalSnapshot`/`ChangeIntelligence` state (see this route's own
 * docstring) -- nothing is recomputed, and expanding a row never
 * fetches or shows the *current* Investment Case in place of the
 * historical one. */
function AnalyticalHistoryRow({
  entry,
  expanded,
  onToggleDetails,
  onOpenCase,
  t,
}: {
  entry: HistoricalAnalysisEntryView;
  expanded: boolean;
  onToggleDetails: () => void;
  onOpenCase: () => void;
  t: Translate;
}) {
  const company = entry.ticker ?? t("dailyBrief.entry.unknownCompany");
  const growthState = entry.businessCategoryStates.find((s) => s.category === "growth");

  return (
    <div>
      <Heading level={3}>{company}</Heading>
      {entry.isBaseline ? (
        <>
          <Text as="p">{t("history.analytical.baseline")}</Text>
          <Text color="secondary" as="p">
            {t("history.analytical.baselineDescription", { company })}
          </Text>
        </>
      ) : (
        <>
          <Text as="p">{t(HEADLINE_KEY[entry.thesisImpact])}</Text>
          {entry.changes.map((change) => (
            <Text as="p" color="secondary" key={change.id}>
              {CHANGE_DIRECTION_SYMBOL[change.direction]} {describeChange(change, t)}
            </Text>
          ))}
        </>
      )}
      <Text color="tertiary" as="p">
        {entry.capturedAt}
      </Text>
      <Button variant="tertiary" onClick={onToggleDetails}>
        {expanded ? t("history.analytical.hideDetails") : t("history.analytical.viewDetails")}
      </Button>{" "}
      <Button variant="tertiary" onClick={onOpenCase}>
        {t("dailyBrief.entry.openInvestmentCase")}
      </Button>

      {expanded && (
        <Stack gap="intra-section">
          <Divider tone="hairline" />
          <Heading level={4}>{t("history.analytical.detail.thesisHeading")}</Heading>
          <Text as="p" color="secondary">
            {entry.atlasThesisNarrative ?? t("history.analytical.detail.noThesis")}
          </Text>

          <Heading level={4}>{t("history.analytical.detail.strengthsHeading")}</Heading>
          {entry.strengths.length === 0 ? (
            <Text color="secondary">{t("history.analytical.detail.empty")}</Text>
          ) : (
            entry.strengths.map((kind) => <Text as="p" key={kind}>{t(HIGHLIGHT_KIND_KEY[kind])}</Text>)
          )}

          <Heading level={4}>{t("history.analytical.detail.risksHeading")}</Heading>
          {entry.risks.length === 0 ? (
            <Text color="secondary">{t("history.analytical.detail.empty")}</Text>
          ) : (
            entry.risks.map((kind) => <Text as="p" key={kind}>{t(HIGHLIGHT_KIND_KEY[kind])}</Text>)
          )}

          <Heading level={4}>{t("history.analytical.detail.growthHeading")}</Heading>
          <Text as="p" color="secondary">
            {growthState
              ? `${t(BUSINESS_CATEGORY_KEY.growth)}: ${t(BUSINESS_STATUS_KEY[growthState.status as AnalysisBusinessStatus])}`
              : t("history.analytical.detail.empty")}
          </Text>

          <Heading level={4}>{t("history.analytical.detail.valuationHeading")}</Heading>
          <Text as="p" color="secondary">
            {t(VALUATION_STATUS_KEY[entry.valuationStatus])}
          </Text>

          <Heading level={4}>{t("history.analytical.detail.openQuestionsHeading")}</Heading>
          {entry.openQuestions.length === 0 ? (
            <Text color="secondary">{t("history.analytical.detail.empty")}</Text>
          ) : (
            entry.openQuestions.map((origin) => (
              <Text as="p" key={origin}>
                {t(OPEN_QUESTION_ORIGIN_KEY[origin])}
              </Text>
            ))
          )}
        </Stack>
      )}
      <Divider tone="hairline" />
    </div>
  );
}
