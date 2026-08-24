import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ACCENT_LINK_STYLE, Button, Divider, Inline, Label, Link, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import { useAlphaWatchlist } from "../discovery/watchlistActions";
import { useAlphaPortfolio } from "../portfolio/alphaPortfolioData";
import { useCompanionContext } from "./useCompanionContext";
import {
  sendCompanionChat,
  type CompanionChatMessage,
  type CompanionOutcome,
  type CompanionRole,
} from "./companionApi";
import styles from "./CompanionPanel.module.css";

type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

/** The transcript is a superset of what's actually sent to the API
 * (`kind: "message"` entries only, mapped to `CompanionChatMessage`).
 * Context-change and tool-result lines are transcript-display facts,
 * never conversational turns the model itself produced -- they are
 * never included in the `messages` array a future send resends.
 *
 * `context-change.from`/`to` are structural context keys (`"portfolio"`
 * or a caseId) -- never pre-resolved display text. Resolving them to a
 * ticker or the "Portfolio-wide" label happens at render time via
 * `resolveContextLabel`, so a later language switch (or a ticker that
 * resolves after the entry was recorded) re-renders correctly instead
 * of freezing whatever text happened to be live at that moment. */
type TranscriptEntry =
  | { kind: "message"; role: CompanionRole; content: string }
  | { kind: "context-change"; from: string; to: string }
  | { kind: "tool-result"; outcome: CompanionOutcome; ticker: string; caseId: string | null }
  | { kind: "error" };

interface PersistedSession {
  transcript: TranscriptEntry[];
  /** The structural context identity (`caseId`, or `"portfolio"`) that
   * accompanied the most recently *tracked* navigation -- used only to
   * detect a real context change and as the "from" side of the next
   * announcement. Never resolved text, so a ticker arriving late from
   * the holdings fetch can never itself trigger a spurious announcement. */
  announcedKey: string | null;
}

const EMPTY_SESSION: PersistedSession = { transcript: [], announcedKey: null };
const STORAGE_KEY_SESSION = "atlas.companion.session";
const STORAGE_KEY_EXPANDED = "atlas.companion.expanded";
const PANEL_ID = "atlas-companion-panel";

const OUTCOME_KEY: Record<CompanionOutcome, TranslationKey> = {
  opened: "companion.outcome.opened",
  created: "companion.outcome.created",
  unresolved: "companion.outcome.unresolved",
  failed: "companion.outcome.failed",
};

function readPersistedSession(): PersistedSession {
  if (typeof window === "undefined") return EMPTY_SESSION;
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY_SESSION);
    if (!raw) return EMPTY_SESSION;
    return JSON.parse(raw) as PersistedSession;
  } catch {
    return EMPTY_SESSION;
  }
}

/** Resolves a structural context key (`"portfolio"` or a caseId) to its
 * current display label. Called at render time -- never stored -- so it
 * always reflects the current language and the current ticker map. */
function resolveContextLabel(key: string, caseIdToTicker: Record<string, string>, t: Translate): string {
  return key === "portfolio" ? t("companion.context.portfolioWide") : (caseIdToTicker[key] ?? key);
}

export function readPersistedExpanded(): boolean {
  if (typeof window === "undefined") return false;
  return window.sessionStorage.getItem(STORAGE_KEY_EXPANDED) === "true";
}

/**
 * Atlas Companion -- the persistent, cross-workspace conversational
 * layer approved to replace every workspace's former page-local "Ask
 * Atlas" box. Mounted once in `AppShell.tsx`, outside the `<Outlet/>`
 * that swaps per route, so it never remounts on navigation.
 *
 * The only backend dependency is the existing `POST /api/discovery/chat`
 * (`companionApi.ts`) -- no new endpoint, no new system-prompt or
 * context-assembly logic. `useCompanionContext()` resolves which workspace
 * is active and either its `caseId` (Investment Case, known directly from
 * the URL) or its `ticker` (the holding-detail and Company routes, added
 * in Product Sprint 3, which carry only a ticker) -- `resolvedCaseId`
 * below converts the latter using the same ticker/Case map this component
 * already fetches for display, before it ever reaches the backend. Either
 * way the backend only ever sees a real Case ID or nothing -- the same
 * portfolio-wide-vs-Case-scoped granularity `DiscoveryContextService.
 * build(case_id)` already supports server-side.
 *
 * Session continuity only (`sessionStorage`, not `localStorage`): the
 * transcript survives navigation and an in-tab refresh, and is
 * deliberately gone when the tab closes -- this is not durable,
 * cross-device Companion memory, which remains a future backend
 * capability, not something this storage choice should be mistaken for.
 *
 * `expanded` is a controlled prop, owned by `AppShell`, rather than
 * local state -- `AppShell` needs to know whether Companion is expanded
 * so it can reserve horizontal space for the panel and keep it from
 * rendering over workspace content (see `--global-companion-reserved-width`
 * in global.css).
 */
export function CompanionPanel({
  expanded,
  onExpandedChange,
}: {
  expanded: boolean;
  onExpandedChange: (expanded: boolean) => void;
}) {
  const { t, language } = useTranslation();
  const navigate = useNavigate();
  const context = useCompanionContext();

  const [session, setSession] = useState<PersistedSession>(readPersistedSession);
  const [inputValue, setInputValue] = useState("");
  const [sending, setSending] = useState(false);
  const [providerNotConfigured, setProviderNotConfigured] = useState(false);
  const [caseIdToTicker, setCaseIdToTicker] = useState<Record<string, string>>({});
  const [tickerToCaseId, setTickerToCaseId] = useState<Record<string, string>>({});
  const [holdingsLoaded, setHoldingsLoaded] = useState(false);
  const portfolioResource = useAlphaPortfolio();
  const watchlistResource = useAlphaWatchlist();

  const announcedKeyRef = useRef<string | null>(session.announcedKey);
  const inputRef = useRef<HTMLInputElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const transcriptEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    window.sessionStorage.setItem(STORAGE_KEY_EXPANDED, expanded ? "true" : "false");
  }, [expanded]);

  useEffect(() => {
    window.sessionStorage.setItem(STORAGE_KEY_SESSION, JSON.stringify(session));
  }, [session]);

  // Ticker/Case ID resolution -- the same real `/api/alpha-portfolio` +
  // `/api/alpha-watchlist` pair every other page reads (Portfolio,
  // Company, Daily Brief, Discovery, History, `CompanyWorkspacePage`),
  // now via the shared, cached hooks (Internal Alpha Stabilization 1,
  // navigation/cache fix) instead of Companion's own independent fetch
  // -- Companion is mounted once for the whole session (outside the
  // per-route `<Outlet/>`, see `AppShell.tsx`), so this still only
  // recomputes when the shared cache itself changes, not on every
  // navigation. A genuine improvement over the prior "fetched once,
  // frozen forever": a mutation elsewhere (add/remove holding, add/
  // remove watchlist entry) now keeps these maps correct instead of
  // going stale for the rest of the session. Portfolio takes precedence
  // over Watchlist when a ticker exists in both, matching
  // `case_membership.py`'s server-side precedence and every existing
  // frontend caller of the same pair.
  useEffect(() => {
    if (portfolioResource.kind === "loading" || watchlistResource.kind === "loading") return;
    const portfolio =
      portfolioResource.kind === "loaded"
        ? (portfolioResource.data as { holdings: { ticker: string; caseId: string | null }[] })
        : null;
    const watchlist = watchlistResource.kind === "loaded" ? watchlistResource.entries : null;

    const caseToTicker: Record<string, string> = {};
    const tickerToCase: Record<string, string> = {};
    // Watchlist first, Portfolio second -- later writes win, so a
    // ticker present in both ends up keyed to its Portfolio Case.
    for (const entry of watchlist ?? []) {
      caseToTicker[entry.caseId] = entry.ticker;
      tickerToCase[entry.ticker] = entry.caseId;
    }
    for (const holding of portfolio?.holdings ?? []) {
      if (!holding.caseId) continue;
      caseToTicker[holding.caseId] = holding.ticker;
      tickerToCase[holding.ticker] = holding.caseId;
    }
    setCaseIdToTicker(caseToTicker);
    setTickerToCaseId(tickerToCase);
    setHoldingsLoaded(true);
  }, [portfolioResource, watchlistResource]);

  useEffect(() => {
    if (!expanded) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onExpandedChange(false);
        toggleRef.current?.focus();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [expanded, onExpandedChange]);

  useEffect(() => {
    if (expanded) inputRef.current?.focus();
  }, [expanded]);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ block: "end" });
  }, [session.transcript.length, sending]);

  // `resolvedCaseId` is the one identifier ever sent to the backend.
  // `investmentCase` already carries a real Case ID from the URL
  // (`context.caseId`); `portfolio` (the holding-detail route) and
  // `company` carry only a ticker, resolved here against the map built
  // above -- the exact same resolution `CompanyWorkspacePage` already
  // does for itself, reused rather than duplicated as a new concept.
  const resolvedCaseId = context.caseId ?? (context.ticker ? (tickerToCaseId[context.ticker] ?? null) : null);
  // The ticker is already known synchronously from the URL wherever one
  // is present, so the context strip never waits on the holdings fetch to
  // name the company -- only the structural key below (and therefore the
  // announcement and the backend call) does.
  const currentSubject = context.ticker
    ? context.ticker
    : context.caseId
      ? (caseIdToTicker[context.caseId] ?? context.caseId)
      : t("companion.context.portfolioWide");
  const hasSubject = context.ticker !== null || context.caseId !== null;
  // "portfolio" is the shared key for every context with no case scoping
  // (bare Portfolio, Daily Brief, Discovery, History, Dashboard, and a
  // Watchlist with nothing selected) -- deliberately the same key as
  // before this sprint, so none of those pages announce a change against
  // each other (design doc: announcements track grounding context, never
  // which page component happens to be mounted).
  const currentKey = context.workspace === null ? null : (resolvedCaseId ?? "portfolio");
  // Only a route that still needs the holdings fetch to resolve its
  // identifier (a direct caseId, or a ticker awaiting conversion) should
  // gate the announcement effect below on it; bare workspace routes have
  // nothing to resolve and must not wait on it.
  const awaitingResolution = (context.caseId !== null || context.ticker !== null) && !holdingsLoaded;

  // Context-change announcement (design doc: never swap `case_id` under
  // an ongoing conversation silently). Keyed on the structural identity
  // (`currentKey`), never on the resolved display text. When the new
  // context is a specific Case, this deliberately waits for the holdings
  // fetch to finish (`holdingsLoaded`) before tracking or announcing
  // anything -- otherwise a page load that lands directly on an
  // Investment Case (a hard reload, a bookmark, a shared link) could
  // announce the raw caseId instead of its ticker, before the one real
  // fetch that resolves it has had a chance to complete. Once resolved,
  // it is never re-resolved for the same navigation (the ticker cannot
  // itself trigger a second, spurious announcement).
  useEffect(() => {
    if (currentKey === null || currentKey === announcedKeyRef.current) return;
    if (awaitingResolution) return;
    // Captured *before* the ref below is mutated -- reading the ref live
    // inside the `setSession` updater is unsafe, since React can defer
    // invoking that updater until after this synchronous block
    // (including the ref mutation two lines down) has already run,
    // which would make `from` and `to` read the same, just-updated
    // value instead of the real previous one.
    const previousKey = announcedKeyRef.current;
    setSession((previous) => {
      const hasSentMessage = previous.transcript.some((entry) => entry.kind === "message");
      const shouldAnnounce = hasSentMessage && previousKey !== null;
      return {
        transcript: shouldAnnounce
          ? [...previous.transcript, { kind: "context-change", from: previousKey!, to: currentKey }]
          : previous.transcript,
        announcedKey: currentKey,
      };
    });
    announcedKeyRef.current = currentKey;
    // context.caseId/context.ticker intentionally excluded -- currentKey
    // already embeds their resolved value, so this effect only needs to
    // re-run on a real navigation (currentKey changing) or the holdings
    // fetch resolving what it was waiting on (awaitingResolution changing).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentKey, awaitingResolution]);

  if (context.workspace === null) return null;

  function openCase(caseId: string) {
    navigate(`/investment-case/${caseId}`, { state: { origin: "companion", ticker: caseIdToTicker[caseId] ?? null } });
  }

  async function handleSend() {
    const trimmed = inputValue.trim();
    if (trimmed === "" || sending) return;

    const nextTranscript: TranscriptEntry[] = [...session.transcript, { kind: "message", role: "user", content: trimmed }];
    const apiMessages: CompanionChatMessage[] = nextTranscript
      .filter((entry): entry is Extract<TranscriptEntry, { kind: "message" }> => entry.kind === "message")
      .map((entry) => ({ role: entry.role, content: entry.content }));

    setSession((previous) => ({ ...previous, transcript: nextTranscript }));
    setInputValue("");
    setSending(true);

    try {
      const result = await sendCompanionChat(apiMessages, language, resolvedCaseId);
      if (result.mode === "not_configured") {
        setProviderNotConfigured(true);
      } else if (result.mode === "provider_error") {
        setSession((previous) => ({ ...previous, transcript: [...previous.transcript, { kind: "error" }] }));
      } else if (result.mode === "tool_call" && result.toolResult) {
        const { outcome, ticker, caseId } = result.toolResult;
        setSession((previous) => ({
          ...previous,
          transcript: [...previous.transcript, { kind: "tool-result", outcome, ticker, caseId }],
        }));
      } else {
        setSession((previous) => ({
          ...previous,
          transcript: [...previous.transcript, { kind: "message", role: "atlas", content: result.message ?? "" }],
        }));
      }
    } catch {
      setSession((previous) => ({ ...previous, transcript: [...previous.transcript, { kind: "error" }] }));
    } finally {
      setSending(false);
    }
  }

  return (
    <div
      style={{
        position: "fixed",
        bottom: "24px",
        right: "24px",
        zIndex: "var(--global-z-companion)",
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-end",
        gap: "8px",
      }}
    >
      {expanded && (
        <Surface
          tier="elevated"
          role="dialog"
          aria-label={t("companion.panel.title")}
          id={PANEL_ID}
          className={styles.panel}
          style={{
            width: "400px",
            maxWidth: "calc(100vw - 48px)",
            maxHeight: "70vh",
            padding: 0,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          <div style={{ padding: "var(--space-card-padding)" }}>
            <Text as="span" style={{ fontWeight: 600 }}>
              {t("companion.panel.title")}
            </Text>
            <Text color="tertiary" as="p">
              {hasSubject
                ? t("companion.context.discussing", { subject: currentSubject })
                : t("companion.context.portfolioWide")}
            </Text>
          </div>
          <Divider tone="hairline" />

          <div style={{ flex: 1, overflowY: "auto", padding: "var(--space-card-padding)" }}>
            <Stack gap="intra-section">
              {session.transcript.map((entry, index) => (
                <TranscriptEntryView key={index} entry={entry} onOpenCase={openCase} t={t} caseIdToTicker={caseIdToTicker} />
              ))}
              {sending && <Text color="tertiary">{t("companion.sending")}</Text>}
            </Stack>
            <div ref={transcriptEndRef} />
          </div>

          {providerNotConfigured && (
            <>
              <Divider tone="hairline" />
              <Text color="tertiary" as="p" style={{ padding: "0 var(--space-card-padding)", paddingTop: "var(--space-metadata)" }}>
                {t("companion.notConfigured")}
              </Text>
            </>
          )}

          <Divider tone="hairline" />
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void handleSend();
            }}
            style={{ padding: "var(--space-card-padding)" }}
          >
            <Inline gap="row" align="center">
              <input
                ref={inputRef}
                value={inputValue}
                placeholder={t("companion.input.placeholder")}
                disabled={sending}
                onChange={(event) => setInputValue(event.target.value)}
                style={{ flex: 1 }}
              />
              <Button variant="tertiary" type="submit" disabled={sending || inputValue.trim() === ""}>
                {t("companion.input.send")}
              </Button>
            </Inline>
          </form>
        </Surface>
      )}

      <button
        ref={toggleRef}
        type="button"
        aria-expanded={expanded}
        aria-controls={PANEL_ID}
        aria-label={expanded ? t("companion.toggle.closeLabel") : t("companion.toggle.openLabel")}
        onClick={() => onExpandedChange(!expanded)}
        style={{
          width: "48px",
          height: "48px",
          borderRadius: "50%",
          border: "var(--width-border-hairline) solid var(--color-border-hairline)",
          background: "var(--surface-elevated)",
          color: "var(--color-text-primary)",
          boxShadow: "var(--elevation-card-shadow)",
          cursor: "pointer",
          fontFamily: "var(--type-family-prose)",
          fontSize: expanded ? "20px" : "13px",
          fontWeight: 600,
        }}
      >
        {expanded ? "×" : "Atlas"}
      </button>
    </div>
  );
}

function TranscriptEntryView({
  entry,
  onOpenCase,
  t,
  caseIdToTicker,
}: {
  entry: TranscriptEntry;
  onOpenCase: (caseId: string) => void;
  t: Translate;
  caseIdToTicker: Record<string, string>;
}) {
  if (entry.kind === "message") {
    return (
      <Stack gap="metadata">
        <Label>{entry.role === "user" ? t("companion.role.user") : t("companion.role.atlas")}</Label>
        <Text as="p">{entry.content}</Text>
      </Stack>
    );
  }

  if (entry.kind === "context-change") {
    return (
      <Text color="tertiary" as="p" style={{ textAlign: "center" }}>
        {t("companion.context.changed", {
          from: resolveContextLabel(entry.from, caseIdToTicker, t),
          to: resolveContextLabel(entry.to, caseIdToTicker, t),
        })}
      </Text>
    );
  }

  if (entry.kind === "tool-result") {
    const canOpen = (entry.outcome === "opened" || entry.outcome === "created") && entry.caseId !== null;
    return (
      <Stack gap="metadata">
        <Text color="secondary" as="p">
          {t(OUTCOME_KEY[entry.outcome], { ticker: entry.ticker })}
        </Text>
        {canOpen && (
          <Link
            href="#"
            style={ACCENT_LINK_STYLE}
            onClick={(event) => {
              event.preventDefault();
              onOpenCase(entry.caseId!);
            }}
          >
            {t("dailyBrief.entry.openInvestmentCase")} →
          </Link>
        )}
      </Stack>
    );
  }

  return (
    <Text color="tertiary" as="p">
      {t("companion.providerError")}
    </Text>
  );
}
