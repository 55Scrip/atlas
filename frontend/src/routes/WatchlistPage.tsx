import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { CSSProperties, FormEvent } from "react";
import { Button, Container, Heading, Inline, Stack, Surface, Text, TextField } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import { ScopeFreshnessSummaryNote } from "../monitoring/ScopeFreshnessSummaryNote";
import { fetchMonitoringStatus, type MonitoringOperationalStatusView } from "../monitoring/monitoringApi";
import { getAlphaWatchlistSnapshot, setAlphaWatchlistData, useAlphaWatchlist } from "../discovery/watchlistActions";
import { useAlphaPortfolio } from "../portfolio/alphaPortfolioData";
import { fetchStanceForCase, type StanceView } from "../stance/stanceApi";
import { StanceBadge } from "../stance/StanceBadge";
import { fetchWatchlistSummary, type WatchlistEntrySummaryView } from "../watchlist/watchlistSummaryApi";
import {
  ANALYSIS_COVERAGE_LEVEL_KEY,
  ANALYSIS_COVERAGE_TONE,
  DECISION_SUPPORT_BADGE_KEY,
  DECISION_SUPPORT_TONE,
} from "../status/statusTone";
import { fetchPortfolioFitForCase, type PortfolioFitAssessmentView } from "../portfolioFit/portfolioFitApi";
import { FitBadge } from "../portfolioFit/FitBadge";
import { StatusBadge } from "../foundation";
import { dimensionLabel } from "../changeIntelligence/describeChange";
import type { Translate } from "../changeIntelligence/describeChange";
import styles from "./WatchlistPage.module.css";

/**
 * Watchlist Doctrine (2026-08-27) -- Watchlist's own, locked question:
 * "What companies is Atlas monitoring for me, and what is Atlas still
 * waiting to know before its view can change?" Not Daily Brief ("what
 * changed"), not Discover ("what has Atlas found"), not Investment
 * Case ("why").
 *
 * Phase 1 removed every Daily-Brief-Agenda-driven concept from this
 * page: the priority-sorted "Decision First" hero and the "Attention"
 * column both rendered the same raw, unfiltered Agenda headline Daily
 * Brief itself stopped showing when it built its own eligibility-
 * filtered change log -- Watchlist never adopted that fix and doctrine
 * review found it duplicating Daily Brief's own job outright. Neither
 * `fetchDailyBriefAgenda` nor any Agenda field is read on this page
 * anymore.
 *
 * Phase 4/5 replace the removed Investment/Portfolio/Evidence rating
 * cluster (current-state analysis, Investment Case's own job) with
 * two real, already-computed signals from the existing Stance engine,
 * newly fetched per row here: `StanceView.level` (one quiet badge,
 * "what does Atlas currently think") and `StanceView.missingInformation`
 * (the "waiting for" line -- reusing the exact same dimension-label
 * translation Investment Case's own `StanceSummary` already uses, no
 * new vocabulary invented). An empty `missingInformation` array is
 * rendered as an honest, calm confirmation, never silently blank --
 * Phase 9 makes monitoring status a *primary*, always-present element,
 * not a conditional one.
 *
 * Phase 3 reframes `added_at` as "Monitoring since" -- the one fact
 * genuinely unique to this page (no other surface says how long Atlas
 * has been watching a company).
 *
 * Phase 8: a ticker that is both held and watchlisted stays visible
 * (removing it automatically would be inventing lifecycle behavior no
 * real signal justifies -- the user chose to watchlist it and never
 * asked to stop) but is now clearly labeled "Also in your Portfolio,"
 * reusing the already-fetched Portfolio holdings list.
 */

interface WatchlistEntryView {
  ticker: string;
  caseId: string;
  addedAt: string;
}

interface HoldingLite {
  ticker: string;
  caseId: string | null;
}
interface PortfolioView {
  exists: boolean;
  holdings: HoldingLite[];
}
type PortfolioStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; view: PortfolioView };

type ListStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; entries: WatchlistEntryView[] };

type StanceStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; stance: StanceView | null };

/** Convergence Sprint 3B. One request composes every prospect's
 * identity, canonical recommendation state and analysis depth from
 * persisted state -- replacing the per-row `/cases/{id}/analysis`
 * fetch, which depended on the Alpha Vantage price provider, the quota
 * tracker and the price refresh coordinator, wrote an evidence
 * snapshot on every call, and could schedule a background price
 * refresh, all to read a company name. */
type SummaryStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; byTicker: Map<string, WatchlistEntrySummaryView> };

type FitStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; fit: PortfolioFitAssessmentView | null };

type AddStatus =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "success"; ticker: string }
  | { kind: "error"; reason: "validation" | "network" };

type RemoveStatus = { kind: "idle" } | { kind: "removing" } | { kind: "error" };

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
  const [stanceStatuses, setStanceStatuses] = useState<Record<string, StanceStatus>>({});
  const [summaryStatus, setSummaryStatus] = useState<SummaryStatus>({ kind: "loading" });
  const [fitStatuses, setFitStatuses] = useState<Record<string, FitStatus>>({});
  const [showAddForm, setShowAddForm] = useState(false);
  const [tickerInput, setTickerInput] = useState("");
  const [addStatus, setAddStatus] = useState<AddStatus>({ kind: "idle" });
  const [monitoringStatus, setMonitoringStatus] = useState<MonitoringOperationalStatusView | null>(null);

  const portfolioResource = useAlphaPortfolio();
  const portfolioStatus: PortfolioStatus =
    portfolioResource.kind === "loaded" ? { kind: "loaded", view: portfolioResource.data as PortfolioView } : portfolioResource;
  const heldTickers = new Set(portfolioStatus.kind === "loaded" ? portfolioStatus.view.holdings.map((h) => h.ticker) : []);

  useEffect(() => {
    const controller = new AbortController();
    fetchMonitoringStatus(controller.signal)
      .then((status) => setMonitoringStatus(status))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
      });
    return () => controller.abort();
  }, []);

  /** One request for the whole list. It replaces a per-entry
   * `/cases/{id}/analysis` fetch whose response this page used for two
   * strings -- the company name and its sector -- while that endpoint
   * reached the price provider, the quota tracker and the refresh
   * coordinator, and wrote an evidence snapshot each time. Its own
   * code says the lazy refresh it schedules is for "a single-ticker
   * view like this one (never Portfolio/Watchlist's own list
   * endpoints)"; calling it once per row defeated exactly that. */
  useEffect(() => {
    if (listStatus.kind !== "loaded") return;
    const controller = new AbortController();
    fetchWatchlistSummary(controller.signal)
      .then((rows) => setSummaryStatus({ kind: "loaded", byTicker: new Map(rows.map((row) => [row.ticker, row])) }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setSummaryStatus({ kind: "error" });
      });
    return () => controller.abort();
  }, [listStatus]);

  /** Phase 4 -- one Stance fetch per row, the real source for both the
   * one quiet "current view" badge and the "waiting for" line
   * (`missingInformation`). Mirrors the identity fetch above exactly;
   * a watchlist is expected to stay small enough that N parallel
   * per-row fetches are reasonable (the same precedent this page's own
   * identity/Fit fetches already established). */
  useEffect(() => {
    if (listStatus.kind !== "loaded") return;
    const controller = new AbortController();
    for (const entry of listStatus.entries) {
      if (stanceStatuses[entry.ticker]) continue;
      setStanceStatuses((current) => ({ ...current, [entry.ticker]: { kind: "loading" } }));
      fetchStanceForCase(entry.caseId, controller.signal)
        .then((stance) => setStanceStatuses((current) => ({ ...current, [entry.ticker]: { kind: "loaded", stance } })))
        .catch((error: unknown) => {
          if (error instanceof DOMException && error.name === "AbortError") return;
          setStanceStatuses((current) => ({ ...current, [entry.ticker]: { kind: "error" } }));
        });
    }
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listStatus]);

  /** Portfolio Fit for a prospect the investor does not hold. The
   * engine supports exactly this case (`is_existing_holding` false,
   * `current_weight_percent` null) and answers "how would this sit in
   * my portfolio" -- which is the question a watchlist exists to ask.
   * `unavailable` is one of its own real ratings, never a middle
   * score. */
  useEffect(() => {
    if (listStatus.kind !== "loaded") return;
    const controller = new AbortController();
    for (const entry of listStatus.entries) {
      if (fitStatuses[entry.ticker]) continue;
      setFitStatuses((current) => ({ ...current, [entry.ticker]: { kind: "loading" } }));
      fetchPortfolioFitForCase(entry.caseId, controller.signal)
        .then((fit) => setFitStatuses((current) => ({ ...current, [entry.ticker]: { kind: "loaded", fit } })))
        .catch((error: unknown) => {
          if (error instanceof DOMException && error.name === "AbortError") return;
          setFitStatuses((current) => ({ ...current, [entry.ticker]: { kind: "error" } }));
        });
    }
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listStatus]);

  /** After an add, recompose the list from persisted state. Adding a
   * ticker legitimately enriches it server-side; reading the list back
   * afterwards must not enrich anything again. */
  function refreshSummary() {
    fetchWatchlistSummary()
      .then((rows) => setSummaryStatus({ kind: "loaded", byTicker: new Map(rows.map((row) => [row.ticker, row])) }))
      .catch(() => setSummaryStatus({ kind: "error" }));
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
        refreshSummary();
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
  }

  function closeAddForm() {
    setShowAddForm(false);
    setAddStatus({ kind: "idle" });
    setTickerInput("");
  }

  /** Atlas UX Freeze v1 -- the approved atlas-watchlist frame resolves
   * the pre-freeze implementation's duplicate add-company presentation
   * (this header button and the empty-state's own CTA both visible at
   * once) down to one control, without changing either's underlying
   * action. The empty-state card already offers the identical action
   * when it is the thing on screen, so the header button is suppressed
   * for exactly that one state -- every other state (populated list,
   * or the add form itself open) is unaffected. */
  const showEmptyState = listStatus.kind === "loaded" && listStatus.entries.length === 0 && !showAddForm;

  return (
    <Container width="wide">
      <Stack gap="intra-section">
        <WatchlistHeader
          listStatus={listStatus}
          showAddForm={showAddForm}
          hideAddButton={showEmptyState}
          onOpenAddForm={() => setShowAddForm(true)}
          t={t}
        />
        {monitoringStatus && (
          <ScopeFreshnessSummaryNote summary={monitoringStatus.watchlistFreshness} scopeKey="monitoring.freshnessSummary.scope.watchlist" t={t} />
        )}

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
        {showEmptyState && <WatchlistEmptyState onAdd={() => setShowAddForm(true)} t={t} />}
        {listStatus.kind === "loaded" && listStatus.entries.length > 0 && (
          <WatchlistTable
            entries={[...listStatus.entries].sort((a, b) => a.ticker.localeCompare(b.ticker))}
            summaryStatus={summaryStatus}
            stanceStatuses={stanceStatuses}
            fitStatuses={fitStatuses}
            heldTickers={heldTickers}
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
  hideAddButton,
  onOpenAddForm,
  t,
}: {
  listStatus: ListStatus;
  showAddForm: boolean;
  hideAddButton: boolean;
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
        {!showAddForm && !hideAddButton && (
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
                <TextField
                  value={tickerInput}
                  onChange={(event) => setTickerInput(event.target.value)}
                  placeholder={t("watchlist.addForm.placeholder")}
                  disabled={isSubmitting}
                  autoFocus
                  style={{ marginTop: "var(--space-metadata)" }}
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

/** Phase 4 -- the real, already-computed "waiting for" line. Reuses
 * `missingInformation` and the exact same `dimensionLabel` translation
 * `StanceSummary` (Investment Case) already uses -- no new vocabulary,
 * no fabricated gap. An empty array is a real, positive fact (Atlas
 * genuinely has what it needs) and is stated as such, never left
 * blank -- monitoring status is always-present, primary content
 * (Phase 9), not a conditional one. */
function waitingForLine(stance: StanceView, t: Translate): string {
  if (stance.missingInformation.length === 0) return t("watchlist.table.waitingForNothing");
  const labels = stance.missingInformation.map((dimension) => dimensionLabel(dimension, t));
  return t("watchlist.table.waitingForLabel", { items: labels.join(", ") });
}

/** Convergence Sprint 3, Phase J. One honest em dash for every unknown
 * in the table, with the word behind it for screen readers. A prospect
 * Atlas has not been able to judge must never read as a mediocre one. */
function UnknownCell({ t }: { t: (key: TranslationKey, params?: Record<string, string | number>) => string }) {
  return (
    <Text as="span" color="tertiary">
      <span aria-hidden="true">{"\u2014"}</span>
      <span style={{ position: "absolute", width: 1, height: 1, overflow: "hidden", clip: "rect(0 0 0 0)" }}>
        {t("watchlist.table.notAssessed")}
      </span>
    </Text>
  );
}

function WatchlistTable({
  entries,
  summaryStatus,
  stanceStatuses,
  fitStatuses,
  heldTickers,
  navigate,
  locale,
  onRemoved,
  t,
}: {
  entries: WatchlistEntryView[];
  summaryStatus: SummaryStatus;
  stanceStatuses: Record<string, StanceStatus>;
  fitStatuses: Record<string, FitStatus>;
  heldTickers: Set<string>;
  navigate: ReturnType<typeof useNavigate>;
  locale: string;
  onRemoved: (ticker: string) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {/* Convergence Sprint 3. Five comparative columns, every
                one a closed categorical vocabulary Atlas already
                computes, so prospects can be scanned down a column
                instead of read one row at a time. "Monitoring since"
                lost its own column and moved into the prospect cell --
                it is context, not something anyone compares on.

                Deliberately absent, because no provider-free per-case
                source exists for them: valuation state, analysis depth
                and the risk projection (cockpit-only or behind the
                heavy analysis endpoint). Also absent because the
                engine has no such concept at all: Conviction, Expected
                Return, Upside, Downside. None of those is approximated
                from something adjacent. */}
            <th style={headerCellStyle}>{t("watchlist.table.companyHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.decisionHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.currentViewHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.coverageHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.fitHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.waitingForHeader")}</th>
            <th style={headerCellStyle} />
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <WatchlistTableRow
              key={entry.ticker}
              entry={entry}
              summary={summaryStatus.kind === "loaded" ? summaryStatus.byTicker.get(entry.ticker) : undefined}
              stanceStatus={stanceStatuses[entry.ticker]}
              fitStatus={fitStatuses[entry.ticker]}
              isHeld={heldTickers.has(entry.ticker)}
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

function WatchlistTableRow({
  entry,
  summary,
  stanceStatus,
  fitStatus,
  isHeld,
  navigate,
  locale,
  onRemoved,
  t,
}: {
  entry: WatchlistEntryView;
  summary: WatchlistEntrySummaryView | undefined;
  stanceStatus: StanceStatus | undefined;
  fitStatus: FitStatus | undefined;
  isHeld: boolean;
  navigate: ReturnType<typeof useNavigate>;
  locale: string;
  onRemoved: (ticker: string) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const companyName = summary?.companyName ?? entry.ticker;
  const sector = summary?.sector;
  const monitoringSince = new Date(entry.addedAt).toLocaleDateString(locale, { year: "numeric", month: "short", day: "numeric" });
  const stance = stanceStatus?.kind === "loaded" ? stanceStatus.stance : null;
  const fit = fitStatus?.kind === "loaded" ? fitStatus.fit : null;

  const [removeStatus, setRemoveStatus] = useState<RemoveStatus>({ kind: "idle" });

  function handleRowActivate() {
    navigate(`/investment-case/${entry.caseId}`, { state: { origin: "watchlist", ticker: entry.ticker } });
  }

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

  /* Final Pre-Alpha Convergence. The row used to carry `role="button"`
     and its own key handling, which overrode the native table row role
     and put focusable buttons (Compare, Remove) inside a control that
     claimed to be a button itself. Discovery's identical table already
     moved to a real button in the company cell; this is the same
     change, so the one pattern behaves the same way on both surfaces.
     Pointer users still activate anywhere on the row. */
  return (
    <tr className={styles.row} onClick={handleRowActivate}>
      <td style={{ ...cellStyle, fontFamily: "var(--type-family-prose)" }}>
        <button
          type="button"
          className={styles.caseButton}
          aria-label={t("watchlist.table.rowAriaLabel", { ticker: entry.ticker })}
          onClick={(event) => {
            event.stopPropagation();
            handleRowActivate();
          }}
        >
        <Stack gap="metadata">
          <Inline gap="metadata" align="baseline" wrap>
            <Text as="span" style={{ fontWeight: 600 }}>
              {companyName}
            </Text>
            <Text as="span" color="tertiary">
              {entry.ticker}
            </Text>
          </Inline>
          <Inline gap="row" align="center" wrap>
            {sector && (
              <Text as="span" color="tertiary" style={{ fontSize: "var(--type-body-min-size)" }}>
                {sector}
              </Text>
            )}
            {/* Monitoring-since is context, not something anyone
                compares prospects on -- it moved out of its own column
                and in here, where it costs a line instead of a sixth
                of the table's width. */}
            <Text as="span" color="tertiary" style={{ fontSize: "var(--type-body-min-size)" }}>
              {t("watchlist.table.monitoringSince", { date: monitoringSince })}
            </Text>
            {isHeld && (
              <Text as="span" color="tertiary" style={{ fontSize: "var(--type-body-min-size)" }}>
                {t("watchlist.table.alsoHeld")}
              </Text>
            )}
          </Inline>
        </Stack>
        </button>
      </td>
      {/* Convergence Sprint 3B, Phases G/H. This used to render the
          Investment Decision layer's `DecisionAction` through its own
          translation bank -- "Inget beslut ännu", "Behåll", "Minska".
          `ACTION_BY_DECISION_SUPPORT_LEVEL` is a pure 1:1 lookup over
          `DecisionSupportLevel` with no additional inputs, so those
          were a second investor-facing vocabulary for a value Portfolio
          and the Investment Case already name "Vet inte än", "Tesen
          kvarstår", "Minskning stöds". The canonical level now arrives
          on the wire and is rendered through the one shared bank, so
          the same state reads the same way wherever it appears. The
          column heading still differs by surface; the state label does
          not. */}
      <td style={cellStyle}>
        {summary ? (
          <StatusBadge
            label={t(DECISION_SUPPORT_BADGE_KEY[summary.decisionSupportLevel])}
            tone={DECISION_SUPPORT_TONE[summary.decisionSupportLevel]}
            weight="strong"
          />
        ) : (
          <UnknownCell t={t} />
        )}
      </td>
      <td style={cellStyle}>{stance ? <StanceBadge level={stance.level} /> : <UnknownCell t={t} />}</td>
      {/* Analysis depth, the one extra field this sprint's lightweight
          composition made available for free. It carries the same
          weight here as on Portfolio: it separates "Atlas looked and
          is unconvinced" from "Atlas has no data yet", two states that
          call for completely different action but read identically
          without it. */}
      <td style={cellStyle}>
        {summary ? (
          <StatusBadge
            label={t(ANALYSIS_COVERAGE_LEVEL_KEY[summary.analysisCoverageLevel])}
            tone={ANALYSIS_COVERAGE_TONE[summary.analysisCoverageLevel]}
          />
        ) : (
          <UnknownCell t={t} />
        )}
      </td>
      <td style={cellStyle}>{fit ? <FitBadge rating={fit.overall} /> : <UnknownCell t={t} />}</td>
      <td style={{ ...cellStyle, fontFamily: "var(--type-family-prose)", maxWidth: "260px" }}>
        {stance ? (
          <Text as="span" color="secondary">
            {waitingForLine(stance, t)}
          </Text>
        ) : (
          <UnknownCell t={t} />
        )}
      </td>
      <td style={cellStyle} onClick={(event) => event.stopPropagation()}>
        {removeStatus.kind === "idle" && (
          <Inline gap="row" wrap>
            {/* The primary "Open Investment Case" button is gone: the
                whole row is already a keyboard-operable button that
                does exactly that, so this was a second copy of one
                action taking a third of the row's action column. */}
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
              <Button variant="primary" onClick={handleRemoveClick}>
                {t("watchlist.remove.retryButton")}
              </Button>
            </Inline>
          </Stack>
        )}
      </td>
    </tr>
  );
}
