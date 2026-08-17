import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { CSSProperties, FormEvent } from "react";
import { Button, Container, Heading, Inline, Stack, StatusBadge, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import {
  CONFIDENCE_KEY,
  CONFIDENCE_TONE,
  DECISION_SUPPORT_BADGE_KEY,
  DECISION_SUPPORT_TONE,
  type DecisionSupportLevel,
  type EvidenceCoverageLevel,
} from "../status/statusTone";

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
 * There is no remove/delete capability anywhere in the real backend
 * (`AlphaWatchlistStore`/`AlphaWatchlistService` -- grepped, only
 * `add`/`list_all`/`get_by_ticker`/`get_by_case_id` exist). Rather than
 * fabricate a fake removal, the Remove control renders disabled with an
 * honest tooltip -- the same precedent already established for
 * "Dismiss from Attention" (`HoldingAttentionPage.tsx`) and "Dismiss"
 * (`CompanyWorkspacePage.tsx`).
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
}

type ListStatus =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "loaded"; entries: WatchlistEntryView[] };

type RowStatus = { kind: "loading" } | { kind: "error" } | { kind: "loaded"; analysis: CaseAnalysisLite };

type AddStatus =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "success"; ticker: string }
  | { kind: "error"; reason: "validation" | "network" };

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

  const [listStatus, setListStatus] = useState<ListStatus>({ kind: "loading" });
  const [rowStatuses, setRowStatuses] = useState<Record<string, RowStatus>>({});
  const [showAddForm, setShowAddForm] = useState(false);
  const [tickerInput, setTickerInput] = useState("");
  const [addStatus, setAddStatus] = useState<AddStatus>({ kind: "idle" });

  useEffect(() => {
    const controller = new AbortController();
    setListStatus({ kind: "loading" });
    fetch("/api/alpha-watchlist", { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error(`Backend responded with ${r.status}`);
        return r.json() as Promise<WatchlistEntryView[]>;
      })
      .then((entries) => setListStatus({ kind: "loaded", entries }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setListStatus({ kind: "error" });
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
        setListStatus((current) => {
          if (current.kind !== "loaded") return { kind: "loaded", entries: [entry] };
          if (current.entries.some((e) => e.ticker === entry.ticker)) return current;
          return { kind: "loaded", entries: [...current.entries, entry] };
        });
        fetchRowAnalysis(entry.ticker, entry.caseId);
        setAddStatus({ kind: "success", ticker: entry.ticker });
        setTickerInput("");
      })
      .catch(() => setAddStatus({ kind: "error", reason: "network" }));
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
            navigate={navigate}
            locale={locale}
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

function WatchlistTable({
  entries,
  rowStatuses,
  navigate,
  locale,
  t,
}: {
  entries: WatchlistEntryView[];
  rowStatuses: Record<string, RowStatus>;
  navigate: ReturnType<typeof useNavigate>;
  locale: string;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={headerCellStyle}>{t("watchlist.table.companyHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.sectorHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.statusHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.coverageHeader")}</th>
            <th style={headerCellStyle}>{t("watchlist.table.addedHeader")}</th>
            <th style={headerCellStyle} />
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <WatchlistTableRow key={entry.ticker} entry={entry} rowStatus={rowStatuses[entry.ticker]} navigate={navigate} locale={locale} t={t} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function WatchlistTableRow({
  entry,
  rowStatus,
  navigate,
  locale,
  t,
}: {
  entry: WatchlistEntryView;
  rowStatus: RowStatus | undefined;
  navigate: ReturnType<typeof useNavigate>;
  locale: string;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}) {
  const loaded = rowStatus?.kind === "loaded" ? rowStatus.analysis : null;
  const companyName = loaded?.companyProfile?.name ?? entry.ticker;
  const sector = loaded?.companyProfile?.sector;
  const coverage = loaded ? loaded.evidenceQuality?.coverage ?? loaded.confidence : null;
  const addedDate = new Date(entry.addedAt).toLocaleDateString(locale, { year: "numeric", month: "short", day: "numeric" });

  function handleRowActivate() {
    navigate(`/company/${encodeURIComponent(entry.ticker)}`);
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
      <td style={{ ...cellStyle, fontVariantNumeric: "tabular-nums" }}>
        <Text as="span" color="secondary">
          {addedDate}
        </Text>
      </td>
      <td style={cellStyle}>
        <Button
          variant="tertiary"
          disabled
          title={t("watchlist.table.removeUnavailable")}
          onClick={(event) => event.stopPropagation()}
        >
          {t("watchlist.table.removeButton")}
        </Button>
      </td>
    </tr>
  );
}
