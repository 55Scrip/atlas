import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Divider, Inline, Label, Link, Stack, Surface, Text } from "../foundation";
import { useTranslation, type TranslationKey } from "../i18n";
import { useCompanionContext } from "./useCompanionContext";
import {
  sendCompanionChat,
  type CompanionChatMessage,
  type CompanionOutcome,
  type CompanionRole,
} from "./companionApi";
import styles from "./CompanionPanel.module.css";

const ACCENT_LINK_STYLE = { color: "var(--global-color-accent)", textDecoration: "none", fontSize: "var(--type-body-min-size)" } as const;

type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

/** The transcript is a superset of what's actually sent to the API
 * (`kind: "message"` entries only, mapped to `CompanionChatMessage`).
 * Context-change and tool-result lines are transcript-display facts,
 * never conversational turns the model itself produced -- they are
 * never included in the `messages` array a future send resends. */
type TranscriptEntry =
  | { kind: "message"; role: CompanionRole; content: string }
  | { kind: "context-change"; from: string; to: string }
  | { kind: "tool-result"; outcome: CompanionOutcome; ticker: string; caseId: string | null }
  | { kind: "error" };

interface PersistedSession {
  transcript: TranscriptEntry[];
  /** The structural context identity (`caseId`, or `"portfolio"`) that
   * accompanied the most recently *tracked* navigation -- used only to
   * detect a real context change, never resolved text, so a ticker
   * arriving late from the holdings fetch can never itself trigger a
   * spurious announcement. */
  announcedKey: string | null;
  /** The resolved display text for `announcedKey`, reused as the "from"
   * side of the next announcement. */
  announcedSubject: string | null;
}

const EMPTY_SESSION: PersistedSession = { transcript: [], announcedKey: null, announcedSubject: null };
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

function readPersistedExpanded(): boolean {
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
 * context-assembly logic. `useCompanionContext()` resolves which
 * workspace is active and, when on a specific Investment Case, its
 * `caseId` -- the same portfolio-wide-vs-Case-scoped granularity
 * `DiscoveryContextService.build(case_id)` already supports server-side.
 *
 * Session continuity only (`sessionStorage`, not `localStorage`): the
 * transcript survives navigation and an in-tab refresh, and is
 * deliberately gone when the tab closes -- this is not durable,
 * cross-device Companion memory, which remains a future backend
 * capability, not something this storage choice should be mistaken for.
 */
export function CompanionPanel() {
  const { t, language } = useTranslation();
  const navigate = useNavigate();
  const context = useCompanionContext();

  const [expanded, setExpanded] = useState<boolean>(readPersistedExpanded);
  const [session, setSession] = useState<PersistedSession>(readPersistedSession);
  const [inputValue, setInputValue] = useState("");
  const [sending, setSending] = useState(false);
  const [providerNotConfigured, setProviderNotConfigured] = useState(false);
  const [caseIdToTicker, setCaseIdToTicker] = useState<Record<string, string>>({});
  const [holdingsLoaded, setHoldingsLoaded] = useState(false);

  const announcedKeyRef = useRef<string | null>(session.announcedKey);
  const announcedSubjectRef = useRef<string | null>(session.announcedSubject);
  const inputRef = useRef<HTMLInputElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const transcriptEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    window.sessionStorage.setItem(STORAGE_KEY_EXPANDED, expanded ? "true" : "false");
  }, [expanded]);

  useEffect(() => {
    window.sessionStorage.setItem(STORAGE_KEY_SESSION, JSON.stringify(session));
  }, [session]);

  // Ticker resolution only -- the same real `/api/alpha-portfolio` fetch
  // every other page already makes independently for itself (Portfolio,
  // Daily Brief, Discovery, History). Fetched once; Companion is mounted
  // for the whole session, so there is no per-navigation refetch.
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/alpha-portfolio", { signal: controller.signal })
      .then((response) => (response.ok ? (response.json() as Promise<{ holdings: { ticker: string; caseId: string | null }[] }>) : null))
      .then((data) => {
        // `setCaseIdToTicker` and `setHoldingsLoaded` are both called
        // from this one callback invocation deliberately -- React 18
        // batches state updates scheduled within the same synchronous
        // callback, but NOT necessarily across separate promise-chain
        // ticks (e.g. a later `.finally`). Keeping both calls here
        // guarantees the resolved ticker map is visible in the very
        // same render where `holdingsLoaded` first becomes true, so the
        // context-change announcement effect (gated on `holdingsLoaded`)
        // never reads a stale, still-empty map.
        if (data) {
          const map: Record<string, string> = {};
          for (const holding of data.holdings) {
            if (holding.caseId) map[holding.caseId] = holding.ticker;
          }
          setCaseIdToTicker(map);
        }
        setHoldingsLoaded(true);
      })
      .catch((error: unknown) => {
        // In React 18 dev/StrictMode this effect mounts, cleans up
        // (aborting the in-flight fetch), then mounts again -- the
        // aborted first request's rejection lands here too. Treating
        // that as "loaded" would mark holdings ready with an empty map
        // before the real second fetch has had a chance to resolve,
        // which is exactly what caused the context-change announcement
        // to show the raw caseId instead of its ticker. Only a genuine
        // failure (not our own cleanup) should mark holdings as loaded.
        if (error instanceof DOMException && error.name === "AbortError") return;
        setHoldingsLoaded(true);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!expanded) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setExpanded(false);
        toggleRef.current?.focus();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [expanded]);

  useEffect(() => {
    if (expanded) inputRef.current?.focus();
  }, [expanded]);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ block: "end" });
  }, [session.transcript.length, sending]);

  const currentSubject = context.caseId
    ? (caseIdToTicker[context.caseId] ?? context.caseId)
    : t("companion.context.portfolioWide");
  const currentKey = context.workspace === null ? null : (context.caseId ?? "portfolio");

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
    if (context.caseId !== null && !holdingsLoaded) return;
    // Captured *before* the refs below are mutated -- reading the ref
    // live inside the `setSession` updater is unsafe, since React can
    // defer invoking that updater until after this synchronous block
    // (including the ref mutations two lines down) has already run,
    // which would make `from` and `to` read the same, just-updated
    // value instead of the real previous one.
    const previousSubject = announcedSubjectRef.current;
    setSession((previous) => {
      const hasSentMessage = previous.transcript.some((entry) => entry.kind === "message");
      const shouldAnnounce = hasSentMessage && previousSubject !== null;
      return {
        transcript: shouldAnnounce
          ? [...previous.transcript, { kind: "context-change", from: previousSubject!, to: currentSubject }]
          : previous.transcript,
        announcedKey: currentKey,
        announcedSubject: currentSubject,
      };
    });
    announcedKeyRef.current = currentKey;
    announcedSubjectRef.current = currentSubject;
    // currentSubject intentionally excluded -- only a real navigation
    // (currentKey changing) or the holdings fetch finishing should ever
    // trigger this effect.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentKey, holdingsLoaded]);

  if (context.workspace === null) return null;

  function openCase(caseId: string) {
    navigate(`/investment-case/${caseId}`, { state: { origin: "companion" } });
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
      const result = await sendCompanionChat(apiMessages, language, context.caseId);
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
              {context.caseId
                ? t("companion.context.discussing", { subject: currentSubject })
                : t("companion.context.portfolioWide")}
            </Text>
          </div>
          <Divider tone="hairline" />

          <div style={{ flex: 1, overflowY: "auto", padding: "var(--space-card-padding)" }}>
            <Stack gap="intra-section">
              {session.transcript.map((entry, index) => (
                <TranscriptEntryView key={index} entry={entry} onOpenCase={openCase} t={t} />
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
        onClick={() => setExpanded((current) => !current)}
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
}: {
  entry: TranscriptEntry;
  onOpenCase: (caseId: string) => void;
  t: Translate;
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
        {t("companion.context.changed", { from: entry.from, to: entry.to })}
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
