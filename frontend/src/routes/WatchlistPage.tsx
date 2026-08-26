import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { CSSProperties, FormEvent } from "react";
import { Button, Container, Heading, Inline, Stack, StatusBadge, StatusText, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import {
  CONFIDENCE_KEY,
  CONFIDENCE_TONE,
  DATA_FRESHNESS_STATUS_KEY,
  DATA_FRESHNESS_STATUS_TONE,
  DECISION_SUPPORT_BADGE_KEY,
  DECISION_SUPPORT_TONE,
  type DataFreshnessStatus,
  type DecisionSupportLevel,
  type EvidenceCoverageLevel,
} from "../status/statusTone";
import { ScopeFreshnessSummaryNote } from "../monitoring/ScopeFreshnessSummaryNote";
import { fetchMonitoringStatus, type MonitoringOperationalStatusView } from "../monitoring/monitoringApi";
import { fetchDailyBriefAgenda, type AgendaItemView } from "../dailyBriefAgenda/dailyBriefAgendaApi";
import { PriorityBadge } from "../dailyBriefAgenda/PriorityBadge";
import { agendaItemHeadline } from "../dailyBriefAgenda/describeAgendaHeadline";
import { getAlphaWatchlistSnapshot, setAlphaWatchlistData, useAlphaWatchlist } from "../discovery/watchlistActions";

/**
 * Watchlist Workspace v1 -- exposes Atlas Alpha's existing provisional
 * Watchlist capability (`atlas/alpha/watchlist`) as a first-class
 * product workspace. Reuses the exact real endpoints unchanged:
 * `GET /api/alpha-watchlist` (list, `{ ticker, caseId, addedAt }` only
 * -- no name/sector/status/coverage on the wire) and
 * `POST /api/alpha-watchlist` (add, idempotent). No new backend
 * endpoint. Company name, sector, Decision Support status, and
 * evidence coverage are resolved per-row by fetching each entry's own
 * `GET /api/cases/{caseId}/analysis` -- the same real payload Company
 * Workspace and Investment Case already consume -- since no batch
 * endpoint exists; a watchlist is expected to stay small enough that
 * N parallel per-row fetches are reasonable.
 *
 * Remove uses the real `DELETE /api/alpha-watchlist/{ticker}` endpoint
 * (Watchlist Remove Capability sprint): a membership mutation only --
 * it never deletes the ticker's Case, Decision history, or Company
 * data (see `atlas/alpha/watchlist/service.py::remove_ticker`). The
 * row is removed from the table only after the backend confirms the
 * mutation (no optimistic hide). Internal Alpha Stabilization: the
 * original two-step click-then-confirm flow is gone -- its own
 * confirmation copy stated the action was non-destructive, which was
 * itself the proof no confirmation step was warranted; Discovery's own
 * "Remove from Watchlist" button was already one click for this exact
 * same mutation. Remove is now one click here too, matching Discovery
 * rather than the other way around.
 *
 * The approved Figma reference frames (`watchlist-workspace`/-empty/
 * -loading/-add-flow/-remove-flow) were generated for this sprint but
 * contained fabricated content discarded here: invented example
 * companies, "Custom Alerts Enabled," "Updated real-time," a
 * search-driven add flow implying a company database that does not
 * exist, and a functioning remove confirmation for a capability that
 * does not exist. Only real table columns, layout, and status-badge
 * conventions were carried over.
 */

interface WatchlistEntryView {
  ticker: string;
  caseId: string;
  addedAt: string;
}

interface CaseAnalysisLite {
  companyProfile: { name: string | null; sector: string | null } | null;
  recommendation: { level: DecisionSupportLevel };
  confidence: EvidenceCoverageLevel;
  evidenceQuality: { coverage: EvidenceCoverageLevel } | null;
  /** Atlas Intelligence Sprint 8 (Automated Monitoring Operations,
   * Deliverable 10). `null` only when Monitoring has no read model
   * wired for this build. */
  operationalFreshness: {
    isPending: boolean;
    lastMonitoredAt: string | null;
    lastRunFailedForCase: boolean;
    dataFreshnessStatus: DataFreshnessStatus;
  } | null;
}

type ListStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; entries: WatchlistEntryView[] };

type RowStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; analysis: CaseAnalysisLite };

/** Product Intelligence Sprint 2 (Watchlist Intelligence Activation).
 * `unavailable` covers both a genuine fetch failure and the honest
 * "Monitoring has never run" absence `daily_brief_agenda` itself
 * already returns as an empty item list -- either way, Attention is
 * simply not yet known for this page load, never rendered as "nothing
 * to see" (Phase 7's own "never imply missing data is a positive
 * signal"). Mirrors `monitoringStatus`'s own existing fetch-and-forget
 * pattern on this same page exactly. */
type AgendaStatus =
  | { kind: "loading" }
  | { kind: "unavailable" }
  | { kind: "loaded"; itemsByTicker: Map<string, AgendaItemView> };

/** Mirrors `atlas.alpha.daily_brief_agenda.engine._PRIORITY_RANK`
 * exactly -- the same, already-computed ranking, never a new one. */
const PRIORITY_RANK: Record<AgendaItemView["priority"], number> = { low: 0, normal: 1, high: 2, critical: 3 };

type AddStatus =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "success"; ticker: string }
  | { kind: "error"; reason: "validation" | "network" };

type RemoveStatus =
  | { kind: "idle" }
  | { kind: "removing" }
  | { kind: "error" };

const cellStyle: CSSProperties = {
  padding: "var(--space-metadata) var(--space-row)",
  textAlign: "left",
  borderBottom: "var(--width-border-hairline) solid var(--color-border-hairline)",
  fontFamily: "var(--type-family-metadata)",
  fontSize: "var(--type-body-min-size)",
};

const headerCellStyle: CSSProperties = {
  ...cellStyle,
  color: "var(--color-text-tertiary)",
  fontWeight: 500,
  fontSize: "11px",
  letterSpacing: "0.04em",
  textTransform: "uppercase",
  borderBottom: "var(--width-border-standard) solid var(--color-border-standard)",
};

export function WatchlistPage() {
  const { t, language } = useTranslation();
  const navigate = useNavigate();
  const locale = language === "sv" ? "sv-SE" : "en-US";

  const listStatus: ListStatus = useAlphaWatchlist();
  const [rowStatuses, setRowStatuses] = useState<Record<string, RowStatus>>({});
  const [showAddForm, setShowAddForm] = useState(false);
  const [tickerInput, setTickerInput] = useState("");
  const [addStatus, setAddStatus] = useState<AddStatus>({ kind: "idle" });
  const [monitoringStatus, setMonitoringStatus] = useState<MonitoringOperationalStatusView | null>(null);
  const [agendaStatus, setAgendaStatus] = useState<AgendaStatus>({ kind: "loading" });

  /** Sprint 9, Deliverable 9 -- same aggregate summary Portfolio shows,
   * same source (`/api/monitoring/status`), same shared component. */
  useEffect(() => {
    const controller = new AbortController();
    fetchMonitoringStatus(controller.signal)
      .then((status) => setMonitoringStatus(status))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  /** Product Intelligence Sprint 2 (Watchlist Intelligence Activation)
   * -- the exact same `/api/daily-brief-agenda` fetch Portfolio's own
   * "Attention Required" section already uses (`PortfolioPage.tsx`),
   * filtered to `group === "watchlist"` the identical way that section
   * filters to `"portfolio"`. One request for the whole page, never
   * per-row -- reused across every row below via `itemsByTicker`. */
  useEffect(() => {
    const controller = new AbortController();
    fetchDailyBriefAgenda(controller.signal)
      .then((agenda) => {
        const itemsByTicker = new Map<string, AgendaItemView>();
        for (const item of agenda.items) {
          if (item.group === "watchlist" && item.ticker) itemsByTicker.set(item.ticker, item);
        }
        setAgendaStatus({ kind: "loaded", itemsByTicker });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setAgendaStatus({ kind: "unavailable" });
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (listStatus.kind !== "loaded") return;
    const controller = new AbortController();
    for (const entry of listStatus.entries) {
      if (rowStatuses[entry.ticker]) continue;
      setRowStatuses((current) => ({ ...current, [entry.ticker]: { kind: "loading" } }));
      fetch(`/api/cases/${entry.caseId}/analysis`, { signal: controller.signal })
        .then((r) => {
          if (!r.ok) throw new Error(`Backend responded with ${r.status}`);
          return r.json() as Promise<CaseAnalysisLite>;
        })
        .then((analysis) => setRowStatuses((current) => ({ ...current, [entry.ticker]: { kind: "loaded", analysis } })))
        .catch((error: unknown) => {
          if (error instanceof DOMException && error.name === "AbortError") return;
          setRowStatuses((current) => ({ ...current, [entry.ticker]: { kind: "error" } }));
        });
    }
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listStatus]);

  function fetchRowAnalysis(ticker: string, caseId: string) {
    setRowStatuses((current) => ({ ...current, [ticker]: { kind: "loading" } }));
    fetch(`/api/cases/${caseId}/analysis`)
      .then((r) => {
        if (!r.ok) throw new Error(`Backend responded with ${r.status}`);
        return r.json() as Promise<CaseAnalysisLite>;
      })
      .then((analysis) => setRowStatuses((current) => ({ ...current, [ticker]: { kind: "loaded", analysis } })))
      .catch(() => setRowStatuses((current) => ({ ...current, [ticker]: { kind: "error" } })));
  }

  function handleAddSubmit(event: FormEvent) {
    event.preventDefault();
    const normalized = tickerInput.trim().toUpperCase();
    if (!normalized) {
      setAddStatus({ kind: "error", reason: "validation" });
      return;
    }
    setAddStatus({ kind: "submitting" });
    fetch("/api/alpha-watchlist", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker: normalized }),
    })
      .then(async (r) => {
        if (r.status === 400) {
          setAddStatus({ kind: "error", reason: "validation" });
          return;
        }
        if (!r.ok) {
          setAddStatus({ kind: "error", reason: "network" });
          return;
        }
        const entry = (await r.json()) as WatchlistEntryView;
        const current = getAlphaWatchlistSnapshot();
        if (current.kind !== "loaded") {
          setAlphaWatchlistData([entry]);
        } else if (!current.entries.some((e) => e.ticker === entry.ticker)) {
          setAlphaWatchlistData([...current.entries, entry]);
        }
        fetchRowAnalysis(entry.ticker, entry.caseId);
        setAddStatus({ kind: "success", ticker: entry.ticker });
        setTickerInput("");
      })
      .catch(() => setAddStatus({ kind: "error", reason: "network" }));
  }

  function handleTickerRemoved(ticker: string) {
    const snapshot = getAlphaWatchlistSnapshot();
    if (snapshot.kind === "loaded") {
      setAlphaWatchlistData(snapshot.entries.filter((e) => e.ticker !== ticker));
    }
    setRowStatuses((current) => {
      if (!(ticker in current)) return current;
      const next = { ...current };
      delete next[ticker];
      return next;
    });
  }

  function closeAddForm() {
    setShowAddForm(false);
    setAddStatus({ kind: "idle" });
    setTickerInput("");
  }

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        <WatchlistHeader
          listStatus={listStatus}
          showAddForm={showAddForm}
          onOpenAddForm={() => setShowAddForm(true)}
          t={t}
        />
        {monitoringStatus && <ScopeFreshnessSummaryNote summary={monitoringStatus.watchlistFreshness} t={t} />}

        {showAddForm && (
          <AddCompanyForm
            tickerInput={tickerInput}
            setTickerInput={setTickerInput}
            addStatus={addStatus}
            onSubmit={handleAddSubmit}
            onClose={closeAddForm}
            onAddAnother={() => setAddStatus({ kind: "idle" })}
            t={t}
          />
        )}

        {listStatus.kind === "loading" && (
          <Text role="status" aria-live="polite">
            {t("common.loading")}
          </Text>
        )}
        {listStatus.kind === "error" && (
          <Text color="tertiary" role="alert">
            {t("watchlist.loadError")}
          </Text>
        )}
        {listStatus.kind === "loaded" && listStatus.entries.length === 0 && !showAddForm && (
          <WatchlistEmptyState onAdd={() => setShowAddForm(true)} t={t} />
        )}
        {listStatus.kind === "loaded" && listStatus.entries.length > 0 && (
          <WatchlistTable
            entries={listStatus.entries}
            rowStatuses={rowStatuses}
            agendaStatus={agendaStatus}
            navigate={navigate}
            locale={locale}
            onRemoved={handleTickerRemoved}
            t={t}
          />
        )}
      </Stack>
    </Container>
  );
}

function WatchlistHeader({
  listStatus,
  showAddForm,
  onOpenAddForm,
  t,
}: {
  listStatus: ListStatus;
  showAddForm: boolean;
  onOpenAddForm: () => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const count = listStatus.kind === "loaded" ? listStatus.entries.length : null;
  return (
    <Stack gap="metadata">
      <Inline gap="inter-section" wrap align="center" style={{ justifyContent: "space-between" }}>
        <Stack gap="metadata">
          <Heading level={1}>{t("watchlist.title")}</Heading>
          <Text color="secondary" as="p">
            {t("watchlist.description")}
          </Text>
          {count !== null && (
            <Text color="tertiary" as="p">
              {count === 1 ? t("watchlist.countOne") : t("watchlist.countOther", { count })}
            </Text>
          )}
        </Stack>
        {!showAddForm && (
          <Button variant="primary" onClick={onOpenAddForm}>
            {t("watchlist.addButton")}
          </Button>
        )}
      </Inline>
    </Stack>
  );
}

function AddCompanyForm({
  tickerInput,
  setTickerInput,
  addStatus,
  onSubmit,
  onClose,
  onAddAnother,
  t,
}: {
  tickerInput: string;
  setTickerInput: (value: string) => void;
  addStatus: AddStatus;
  onSubmit: (event: FormEvent) => void;
  onClose: () => void;
  onAddAnother: () => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const isSubmitting = addStatus.kind === "submitting";

  return (
    <Surface tier="primary" bordered>
      <Stack gap="metadata">
        {addStatus.kind === "success" ? (
          <>
            <Text as="p" role="status" aria-live="polite">
              {t("watchlist.addForm.successMessage", { ticker: addStatus.ticker })}
            </Text>
            <Inline gap="row" wrap>
              <Button variant="tertiary" onClick={onAddAnother}>
                {t("watchlist.addForm.addAnother")}
              </Button>
              <Button variant="primary" onClick={onClose}>
                {t("watchlist.addForm.done")}
              </Button>
            </Inline>
          </>
        ) : (
          <form onSubmit={onSubmit}>
            <Stack gap="metadata">
              <Text as="label" style={{ display: "block" }}>
                {t("watchlist.addForm.label")}
                <br />
                <input
                  value={tickerInput}
                  onChange={(event) => setTickerInput(event.target.value)}
                  placeholder={t("watchlist.addForm.placeholder")}
                  disabled={isSubmitting}
                  autoFocus
                />
              </Text>
              {addStatus.kind === "error" && (
                <Text color="tertiary" role="alert">
                  {addStatus.reason === "validation" ? t("watchlist.addForm.errorValidation") : t("watchlist.addForm.errorNetwork")}
                </Text>
              )}
              <Inline gap="row" wrap>
                <Button variant="tertiary" type="button" onClick={onClose} disabled={isSubmitting}>
                  {t("watchlist.addForm.cancel")}
                </Button>
                <Button variant="primary" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? t("watchlist.addForm.submitting") : t("watchlist.addForm.submit")}
                </Button>
              </Inline>
            </Stack>
          </form>
        )}
      </Stack>
    </Surface>
  );
}

function WatchlistEmptyState({ onAdd, t }: { onAdd: () => void; t: (key: TranslationKey) => string }) {
  return (
    <Surface tier="primary" bordered>
      <Stack gap="inter-section">
        <Heading level={2}>{t("watchlist.empty.heading")}</Heading>
        <Text as="p" color="secondary">
          {t("watchlist.empty.body")}
        </Text>
        <div>
          <Button variant="primary" onClick={onAdd}>
            {t("watchlist.empty.cta")}
          </Button>
        </div>
      </Stack>
    </Surface>
  );
}

/** Product Intelligence Sprint 2, Phase 4 (Prioritization). Rows with a
 * real, already-computed Agenda item sort first, highest `PriorityLevel`
 * first (mirrors the backend's own `_PRIORITY_RANK` order, never a new
 * ranking); rows with no item keep their existing relative order,
 * `Array.prototype.sort` being stable. Before the Agenda itself has
 * loaded, order is left entirely unchanged -- never resorted twice. */
function sortByAttention(entries: WatchlistEntryView[], agendaStatus: AgendaStatus): WatchlistEntryView[] {
  if (agendaStatus.kind !== "loaded") return entries;
  const { itemsByTicker } = agendaStatus;
  const rankOf = (ticker: string): number => {
    const item = itemsByTicker.get(ticker);
    return item ? PRIORITY_RANK[item.priority] : -1;
  };
  return [...entries].sort((a, b) => rankOf(b.ticker) - rankOf(a.ticker));
}

function WatchlistTable({
  entries,
  rowStatuses,
  agendaStatus,
  navigate,
  locale,
  onRemoved,
  t,
}: {
  entries: WatchlistEntryView[];
  rowStatuses: Record<string, RowStatus>;
  agendaStatus: AgendaStatus;
  navigate: ReturnType<typeof useNavigate>;
  locale: string;
  onRemoved: (ticker: string) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const orderedEntries = sortByAttention(entries, agendaStatus);
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={headerCellStyle}>{t("watchlist.table.companyHeader")}</th>
            {/* Product Intelligence Sprint 2: the page's own Mission --
                "which companies deserve my attention today, and why" --
                made a first-class column, positioned right after Company
                as the row's own most decision-relevant fact. */}
            <th style={headerCellStyle}>{t("watchlist.table.attentionHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.sectorHeader")}</th>
            {/* Internal Alpha Stabilization: was "Status" -- the exact
                same `DecisionSupportLevel` badge is labeled "Decision
                Support" on Portfolio's Holdings table and Company
                Workspace; standardized here so identical information
                carries the identical label everywhere it appears. */}
            <th style={headerCellStyle}>{t("watchlist.table.decisionSupportHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.coverageHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.monitoringHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.addedHeader")}</th>
            <th style={headerCellStyle} />
          </tr>
        </thead>
        <tbody>
          {orderedEntries.map((entry) => (
            <WatchlistTableRow
              key={entry.ticker}
              entry={entry}
              rowStatus={rowStatuses[entry.ticker]}
              agendaStatus={agendaStatus}
              navigate={navigate}
              locale={locale}
              onRemoved={onRemoved}
              t={t}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Product Intelligence Sprint 2, Phase 7 (Empty States). Three real,
 * distinct states, never conflated: the Agenda hasn't loaded yet
 * (`notYetAvailable`, a neutral "—", matching every other column's own
 * loading convention on this page); it loaded and genuinely found
 * nothing for this ticker (`noSignificantChanges`, `tone="neutral"`,
 * never `"positive"` -- Phase 7's own explicit "never imply missing
 * data is a positive signal"); or a real item exists. */
function AttentionCell({
  ticker,
  agendaStatus,
  t,
}: {
  ticker: string;
  agendaStatus: AgendaStatus;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  if (agendaStatus.kind !== "loaded") {
    return (
      <Text as="span" color="tertiary">
        {t("watchlist.table.notAvailable")}
      </Text>
    );
  }
  const item = agendaStatus.itemsByTicker.get(ticker);
  if (!item) {
    return <StatusText label={t("watchlist.attention.noSignificantChanges")} tone="neutral" />;
  }
  return (
    <Stack gap="metadata">
      <PriorityBadge priority={item.priority} />
      <Text as="span" color="secondary">
        {agendaItemHeadline(item, t)}
      </Text>
    </Stack>
  );
}

function WatchlistTableRow({
  entry,
  rowStatus,
  agendaStatus,
  navigate,
  locale,
  onRemoved,
  t,
}: {
  entry: WatchlistEntryView;
  rowStatus: RowStatus | undefined;
  agendaStatus: AgendaStatus;
  navigate: ReturnType<typeof useNavigate>;
  locale: string;
  onRemoved: (ticker: string) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const loaded = rowStatus?.kind === "loaded" ? rowStatus.analysis : null;
  const companyName = loaded?.companyProfile?.name ?? entry.ticker;
  const sector = loaded?.companyProfile?.sector;
  const coverage = loaded ? loaded.evidenceQuality?.coverage ?? loaded.confidence : null;
  const addedDate = new Date(entry.addedAt).toLocaleDateString(locale, { year: "numeric", month: "short", day: "numeric" });

  const [removeStatus, setRemoveStatus] = useState<RemoveStatus>({ kind: "idle" });
  const actionCellRef = useRef<HTMLTableCellElement>(null);
  const previousRemoveStatusKind = useRef<RemoveStatus["kind"]>(removeStatus.kind);

  useEffect(() => {
    // Foundation's <Button> isn't ref-forwarding (out of scope to change
    // here), so focus is moved via the action cell's own DOM node --
    // skipped on initial mount (previous === current) so idle rows never
    // steal focus on page load, only on an explicit state change (open
    // confirm / cancel back / land on an error).
    if (previousRemoveStatusKind.current !== removeStatus.kind) {
      actionCellRef.current?.querySelector<HTMLButtonElement>("button:not(:disabled)")?.focus();
    }
    previousRemoveStatusKind.current = removeStatus.kind;
  }, [removeStatus.kind]);

  /** Watchlist Navigation Scope (live-verification follow-up): the row
   * used to activate into Company Workspace -- a documented, deliberate
   * mid-flow triage page ("Portfolio -> Company -> Investment Case ->
   * Record Decision," per that page's own module docstring) whose own
   * "Record a decision" action already does nothing but navigate to
   * Investment Case itself. Watchlist's own mission is "which companies
   * deserve my attention today, and why" -- a page about deciding what
   * to do next, not a triage waypoint. The row now activates straight
   * into the one page that actually holds the full decision support and
   * the real decision-recording form, matching the explicit "Öppna
   * investeringscase" action in the same row exactly (same destination,
   * same origin-tracking state) rather than sending the row and the
   * button to two different pages. Company Workspace itself is
   * unchanged and remains reachable via its own existing entry points
   * (e.g. Portfolio); this only changes where Watchlist's own row leads. */
  function handleRowActivate() {
    navigate(`/investment-case/${entry.caseId}`, { state: { origin: "watchlist", ticker: entry.ticker } });
  }

  /** Internal Alpha Stabilization: this used to be a two-step
   * click-Remove-then-confirm flow. Removed here specifically because
   * the confirmation dialog's own copy ("This only removes {ticker}
   * from your Watchlist. The Investment Case and decision history are
   * preserved.") proved the action was never destructive in the first
   * place -- Discovery's own "Remove from Watchlist" button was already
   * one click, no confirmation, for the exact same real backend
   * mutation. Two different click-counts for one identical action was
   * both unnecessary friction (Deliverable 3) and a real inconsistency
   * (Deliverable 4); Watchlist now matches Discovery rather than the
   * other way around, per this sprint's "prefer removing friction." */
  function handleRemoveClick() {
    setRemoveStatus({ kind: "removing" });
    fetch(`/api/alpha-watchlist/${encodeURIComponent(entry.ticker)}`, { method: "DELETE" })
      .then((r) => {
        if (!r.ok) throw new Error(`Backend responded with ${r.status}`);
        onRemoved(entry.ticker);
      })
      .catch(() => setRemoveStatus({ kind: "error" }));
  }

  function handleCancelRemove() {
    setRemoveStatus({ kind: "idle" });
  }

  function handleRetryRemove() {
    handleRemoveClick();
  }

  return (
    <tr
      role="button"
      tabIndex={0}
      aria-label={t("watchlist.table.rowAriaLabel", { ticker: entry.ticker })}
      onClick={handleRowActivate}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          handleRowActivate();
        }
      }}
      style={{ cursor: "pointer" }}
    >
      <td style={{ ...cellStyle, fontFamily: "var(--type-family-prose)" }}>
        <Inline gap="metadata" align="baseline" wrap>
          <Text as="span" style={{ fontWeight: 600 }}>
            {companyName}
          </Text>
          <Text as="span" color="tertiary">
            {entry.ticker}
          </Text>
        </Inline>
      </td>
      <td style={cellStyle}>
        <AttentionCell ticker={entry.ticker} agendaStatus={agendaStatus} t={t} />
      </td>
      <td style={cellStyle}>
        <Text as="span" color="secondary">
          {sector ?? t("watchlist.table.notAvailable")}
        </Text>
      </td>
      <td style={cellStyle}>
        {loaded ? (
          <StatusBadge label={t(DECISION_SUPPORT_BADGE_KEY[loaded.recommendation.level])} tone={DECISION_SUPPORT_TONE[loaded.recommendation.level]} />
        ) : rowStatus?.kind === "error" ? (
          <Text as="span" color="tertiary">
            {t("watchlist.table.rowLoadError")}
          </Text>
        ) : (
          <Text as="span" color="tertiary">
            {t("watchlist.table.notAvailable")}
          </Text>
        )}
      </td>
      <td style={cellStyle}>
        {coverage ? (
          <StatusBadge label={t(CONFIDENCE_KEY[coverage])} tone={CONFIDENCE_TONE[coverage]} />
        ) : (
          <Text as="span" color="tertiary">
            {t("watchlist.table.notAvailable")}
          </Text>
        )}
      </td>
      <td style={cellStyle}>
        {loaded?.operationalFreshness ? (
          <StatusBadge
            label={t(DATA_FRESHNESS_STATUS_KEY[loaded.operationalFreshness.dataFreshnessStatus])}
            tone={DATA_FRESHNESS_STATUS_TONE[loaded.operationalFreshness.dataFreshnessStatus]}
          />
        ) : (
          <Text as="span" color="tertiary">
            {t("watchlist.table.notAvailable")}
          </Text>
        )}
      </td>
      <td style={{ ...cellStyle, fontVariantNumeric: "tabular-nums" }}>
        <Text as="span" color="secondary">
          {addedDate}
        </Text>
      </td>
      <td ref={actionCellRef} style={cellStyle} onClick={(event) => event.stopPropagation()}>
        {removeStatus.kind === "idle" && (
          <Inline gap="row" wrap>
            {/* Product Sprint 9 (Discovery Excellence, Deliverable 8 --
                Watchlist Flow): the only navigation this page previously
                offered was the row click into Company Workspace --
                Investment Case and Compare were both a dead end from
                here. Both reuse `entry.caseId`, already on hand, no new
                fetch. */}
            <Button
              variant="tertiary"
              onClick={() =>
                navigate(`/investment-case/${entry.caseId}`, { state: { origin: "watchlist", ticker: entry.ticker } })
              }
            >
              {t("watchlist.table.openInvestmentCase")}
            </Button>
            <Button variant="tertiary" onClick={() => navigate(`/discovery/compare?a=${encodeURIComponent(entry.ticker)}`)}>
              {t("watchlist.table.compareButton")}
            </Button>
            <Button variant="tertiary" onClick={handleRemoveClick}>
              {t("watchlist.table.removeButton")}
            </Button>
          </Inline>
        )}
        {removeStatus.kind === "removing" && (
          <Text as="p" role="status" color="tertiary">
            {t("watchlist.remove.removingLabel")}
          </Text>
        )}
        {removeStatus.kind === "error" && (
          <Stack gap="metadata">
            <Text as="p" role="alert" color="tertiary">
              {t("watchlist.remove.failureMessage", { ticker: entry.ticker })}
            </Text>
            <Inline gap="row" wrap>
              <Button variant="tertiary" onClick={handleCancelRemove}>
                {t("watchlist.remove.cancelButton")}
              </Button>
              <Button variant="primary" onClick={handleRetryRemove}>
                {t("watchlist.remove.retryButton")}
              </Button>
            </Inline>
          </Stack>
        )}
      </td>
    </tr>
  );
}
