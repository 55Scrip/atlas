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

interface CaseIdentityLite {
  companyProfile: { name: string | null; sector: string | null } | null;
}

type ListStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; entries: WatchlistEntryView[] };

type RowStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; identity: CaseIdentityLite };

type StanceStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; stance: StanceView | null };

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
  const [rowStatuses, setRowStatuses] = useState<Record<string, RowStatus>>({});
  const [stanceStatuses, setStanceStatuses] = useState<Record<string, StanceStatus>>({});
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

  useEffect(() => {
    if (listStatus.kind !== "loaded") return;
    const controller = new AbortController();
    for (const entry of listStatus.entries) {
      if (rowStatuses[entry.ticker]) continue;
      setRowStatuses((current) => ({ ...current, [entry.ticker]: { kind: "loading" } }));
      fetch(`/api/cases/${entry.caseId}/analysis`, { signal: controller.signal })
        .then((r) => {
          if (!r.ok) throw new Error(`Backend responded with ${r.status}`);
          return r.json() as Promise<CaseIdentityLite>;
        })
        .then((identity) => setRowStatuses((current) => ({ ...current, [entry.ticker]: { kind: "loaded", identity } })))
        .catch((error: unknown) => {
          if (error instanceof DOMException && error.name === "AbortError") return;
          setRowStatuses((current) => ({ ...current, [entry.ticker]: { kind: "error" } }));
        });
    }
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  function fetchRowIdentity(ticker: string, caseId: string) {
    setRowStatuses((current) => ({ ...current, [ticker]: { kind: "loading" } }));
    fetch(`/api/cases/${caseId}/analysis`)
      .then((r) => {
        if (!r.ok) throw new Error(`Backend responded with ${r.status}`);
        return r.json() as Promise<CaseIdentityLite>;
      })
      .then((identity) => setRowStatuses((current) => ({ ...current, [ticker]: { kind: "loaded", identity } })))
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
        fetchRowIdentity(entry.ticker, entry.caseId);
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
            rowStatuses={rowStatuses}
            stanceStatuses={stanceStatuses}
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

function WatchlistTable({
  entries,
  rowStatuses,
  stanceStatuses,
  heldTickers,
  navigate,
  locale,
  onRemoved,
  t,
}: {
  entries: WatchlistEntryView[];
  rowStatuses: Record<string, RowStatus>;
  stanceStatuses: Record<string, StanceStatus>;
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
            <th style={headerCellStyle}>{t("watchlist.table.companyHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.monitoringSinceHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.waitingForHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.currentViewHeader")}</th>
            <th style={headerCellStyle} />
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <WatchlistTableRow
              key={entry.ticker}
              entry={entry}
              rowStatus={rowStatuses[entry.ticker]}
              stanceStatus={stanceStatuses[entry.ticker]}
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
  rowStatus,
  stanceStatus,
  isHeld,
  navigate,
  locale,
  onRemoved,
  t,
}: {
  entry: WatchlistEntryView;
  rowStatus: RowStatus | undefined;
  stanceStatus: StanceStatus | undefined;
  isHeld: boolean;
  navigate: ReturnType<typeof useNavigate>;
  locale: string;
  onRemoved: (ticker: string) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const loaded = rowStatus?.kind === "loaded" ? rowStatus.identity : null;
  const companyName = loaded?.companyProfile?.name ?? entry.ticker;
  const sector = loaded?.companyProfile?.sector;
  const monitoringSince = new Date(entry.addedAt).toLocaleDateString(locale, { year: "numeric", month: "short", day: "numeric" });
  const stance = stanceStatus?.kind === "loaded" ? stanceStatus.stance : null;

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
      className={styles.row}
      style={{ cursor: "pointer" }}
    >
      <td style={{ ...cellStyle, fontFamily: "var(--type-family-prose)" }}>
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
            {isHeld && (
              <Text as="span" color="tertiary" style={{ fontSize: "var(--type-body-min-size)" }}>
                {t("watchlist.table.alsoHeld")}
              </Text>
            )}
          </Inline>
        </Stack>
      </td>
      <td style={{ ...cellStyle, fontVariantNumeric: "tabular-nums" }}>
        <Text as="span" color="secondary">
          {t("watchlist.table.monitoringSince", { date: monitoringSince })}
        </Text>
      </td>
      <td style={cellStyle}>
        {stance ? (
          <Text as="span" color="secondary">
            {waitingForLine(stance, t)}
          </Text>
        ) : stanceStatus?.kind === "error" ? (
          <Text as="span" color="tertiary">
            {t("watchlist.table.notAvailable")}
          </Text>
        ) : (
          <Text as="span" color="tertiary">
            {t("watchlist.table.notAvailable")}
          </Text>
        )}
      </td>
      <td style={cellStyle}>{stance ? <StanceBadge level={stance.level} /> : <Text color="tertiary">{t("watchlist.table.notAvailable")}</Text>}</td>
      <td style={cellStyle} onClick={(event) => event.stopPropagation()}>
        {removeStatus.kind === "idle" && (
          <Inline gap="row" wrap>
            <Button
              variant="primary"
              onClick={() => navigate(`/investment-case/${entry.caseId}`, { state: { origin: "watchlist", ticker: entry.ticker } })}
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
